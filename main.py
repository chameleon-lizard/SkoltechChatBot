import pathlib
import dotenv
import os

import openai

from pymilvus import MilvusClient

from tqdm import tqdm

from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.retrievers import BM25Retriever

from transformers.agents import Tool, ReactJsonAgent

from FlagEmbedding import FlagReranker

import src.utils as utils
import src.prompts as prompts


dotenv.load_dotenv("env")


class RetrieverTool(Tool):
    name = "retriever"
    description = "Using semantic similarity, retrieves some documents from the knowledge base that have the closest embeddings to the input query."
    inputs = {
        "query": {
            "type": "text",
            "description": "The query to perform. This should be semantically close to your target documents. Use the affirmative form rather than a question.",
        }
    }
    output_type = "text"

    def __init__(
        self,
        vectordb,
        vector_collection,
        bm25,
        embedder_func,
        reranker,
        verbose,
        translate,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.vectordb = vectordb
        self.vector_collection = vector_collection
        self.bm25 = bm25
        self.embedder_func = embedder_func
        self.reranker = reranker
        self.verbose = verbose
        self.translate = translate

    def forward(self, query: str) -> str:
        assert isinstance(query, str), "Your search query must be a string"

        search_res = self.vectordb.search(
            collection_name=self.vector_collection,
            data=[
                self.embedder_func(query)
            ],  # Use the `emb_text` function to convert the question to an embedding vector
            limit=24,  # Return top N results
            search_params={"metric_type": "IP", "params": {}},  # Inner product distance
            output_fields=["text"],  # Return the text field
        )

        retrieved_lines_with_distances = [
            (res["entity"]["text"], res["distance"]) for res in search_res[0]
        ]

        if utils.is_russian(query):
            translated_query = self.translate(query, "en")
            bm25_res = self.bm25.invoke(translated_query, k=10)
        else:
            bm25_res = self.bm25.invoke(query, k=10)

        retrieved_lines_with_distances += [(_.page_content, 0) for _ in bm25_res]

        if self.verbose:
            print(retrieved_lines_with_distances)

        reranked_lines = [
            (self.reranker.compute_score([query, line[0]], normalize=True), line[0])
            for line in retrieved_lines_with_distances
        ]
        reranked_lines = sorted(reranked_lines, key=lambda x: x[0], reverse=True)[:6]

        return "\nRetrieved documents:\n" + "".join(
            [
                f"===== Document {str(i)}, similarity to query: {line_with_distance[0]} =====\n"
                + line_with_distance[1]
                for i, line_with_distance in enumerate(reranked_lines)
            ]
        )


class Chatbot:
    def __init__(
        self,
        model_name: str,
        api_link: str,
        api_key: str,
        document_paths: list[str],
        verbose=True,
    ) -> None:
        self.verbose = verbose

        self.model_name = model_name
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=api_link,
        )

        self.embedding_model = SentenceTransformer(
            f"{os.environ.get('EMBEDDER_MODEL')}"
        )
        self.reranker_model = FlagReranker(
            f"{os.environ.get('RERANKER_MODEL')}", use_fp16=True
        )

        self.docs = [
            (pathlib.Path(document_path).read_text(), document_path)
            for document_path in document_paths
        ]

        self.milvus_client = MilvusClient(uri="./hf_milvus_demo.db")

        self.vector_collection = "vector_collection"

        # BM25 collection
        recursive_chunker = RecursiveCharacterTextSplitter(
            chunk_size=100,
            chunk_overlap=10,
        )

        bm25_docs = recursive_chunker.split_text(
            "\n".join([doc[0] for doc in self.docs]),
        )

        self.bm25 = BM25Retriever.from_texts(bm25_docs)

        self.retriever_tool = RetrieverTool(
            self.milvus_client,
            self.vector_collection,
            self.bm25,
            self.emb_text,
            self.reranker_model,
            self.verbose,
            self.translate,
        )

        self.agent = ReactJsonAgent(
            tools=[self.retriever_tool],
            llm_engine=self.llm_engine,
            max_iterations=3,
            verbose=2 if verbose else 0,
        )

    def llm_engine(self, messages, stop_sequences=["Task"]) -> str:
        response_big = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.3,
            n=1,
            stop=stop_sequences,
            max_tokens=1024,
        )

        return response_big.choices[0].message.content

    def load_database(self) -> None:
        self.milvus_client.load_collection(self.vector_collection)

    def emb_text(self, text):
        return self.embedding_model.encode(
            prompts.EMBEDDER_PROMPT + text, normalize_embeddings=True
        )

    def build_database(self) -> None:
        test_embedding = self.emb_text("This is a test")
        embedding_dim = len(test_embedding)

        if self.milvus_client.has_collection(self.vector_collection):
            self.milvus_client.drop_collection(self.vector_collection)

        for doc, document_path in self.docs:
            # Vector collection
            chunks = utils.split_text(doc, document_path)
            text_lines = [chunk.page_content for chunk in chunks]

            self.milvus_client.create_collection(
                collection_name=self.vector_collection,
                dimension=embedding_dim,
                metric_type="IP",  # Inner product distance
                consistency_level="Strong",  # Strong consistency level
            )

            data = []

            for i, line in enumerate(tqdm(text_lines, desc="Creating embeddings")):
                data.append({"id": i, "vector": self.emb_text(line), "text": line})

            insert_res = self.milvus_client.insert(
                collection_name=self.vector_collection, data=data
            )
            insert_res["insert_count"]

    def translate(self, query: str, lang: str = "ru") -> str:
        match lang:
            case "ru":
                lang = "Russian"
            case "en":
                lang = "English"

        messages = [
            {"role": "system", "content": prompts.TRANSLATE_PROMPT.format(lang=lang)},
            {"role": "user", "content": query},
        ]

        print(query)

        res = self.llm_engine(messages)

        print(res)
        return res

    def question(
        self,
        question: str,
    ) -> str:
        res = self.agent.run(prompts.ENCHANCED_QUESTION + question)

        if self.verbose:
            print(question, res)

        if not res or "Thought: " in res or '"action": "' in res:
            if "final_answer" in res:
                res = res.split('final_answer"')[1]
                res = res.split("\n}")[0]
            else:
                res = prompts.DID_NOT_FIND

        if (utils.is_russian(question) and utils.is_russian(res)) or (
            not utils.is_russian(question) and not utils.is_russian(res)
        ):
            return res
        elif utils.is_russian(question) and not utils.is_russian(res):
            if utils.is_link_or_email(res):
                return res
            return self.translate(res, "ru")
        else:
            return self.translate(res, "en")


if __name__ == "__main__":
    c = Chatbot(
        f"{os.environ.get('CHATBOT_MODEL')}",
        f"{os.environ.get('API_LINK')}",
        f"{os.environ.get('TOKEN')}",
        ["data/orientation.md"],
    )
    c.build_database()
    print(c.question("What are the sizes of scholarships in Skoltech?"))
