import pathlib
import dotenv
import os
import openai

from pymilvus import MilvusClient
from tqdm import tqdm

from langchain_experimental.text_splitter import SemanticChunker
from langchain_core.documents.base import Document
from langchain_community.embeddings import HuggingFaceBgeEmbeddings

from transformers.agents import Tool, ReactJsonAgent


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

    def __init__(self, vectordb, collection_name, embedder_func, **kwargs):
        super().__init__(**kwargs)
        self.vectordb = vectordb
        self.collection_name = collection_name
        self.embedder_func = embedder_func

    def forward(self, query: str) -> str:
        assert isinstance(query, str), "Your search query must be a string"

        search_res = self.vectordb.search(
            collection_name=self.collection_name,
            data=[
                self.embedder_func(query)
            ],  # Use the `emb_text` function to convert the question to an embedding vector
            limit=3,  # Return top 3 results
            search_params={"metric_type": "IP", "params": {}},  # Inner product distance
            output_fields=["text"],  # Return the text field
        )

        retrieved_lines_with_distances = [
            (res["entity"]["text"], res["distance"]) for res in search_res[0]
        ]

        return "\nRetrieved documents:\n" + "".join(
            [
                f"===== Document {str(i)}, similarity to query: {line_with_distance[1]} =====\n"
                + line_with_distance[0]
                for i, line_with_distance in enumerate(retrieved_lines_with_distances)
            ]
        )


def split_text(text: str, semantic_chunker: SemanticChunker) -> list[Document]:
    res = []
    buff = ""
    for line in text.splitlines():
        if line.strip().startswith("###"):
            res.append(buff)
            buff = ""
        buff += "\n" + line

    return semantic_chunker.create_documents(res)


class Chatbot:
    def __init__(
        self,
        model_name: str,
        api_link: str,
        api_key: str,
        document_paths: list[str],
    ) -> None:
        self.model_name = model_name
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=api_link,
        )
        model_name = "BAAI/bge-base-en-v1.5"
        model_kwargs = {"device": "cuda"}
        encode_kwargs = {"normalize_embeddings": True}

        self.embedding_model = HuggingFaceBgeEmbeddings(
            model_name=model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs,
        )

        self.text_splitter = SemanticChunker(self.embedding_model)

        self.docs = [
            pathlib.Path(document_path).read_text() for document_path in document_paths
        ]

        self.milvus_client = MilvusClient(uri="./hf_milvus_demo.db")
        self.collection_name = "rag_collection"
        retriever_tool = RetrieverTool(
            self.milvus_client, self.collection_name, self.embedding_model.embed_query
        )

        self.agent = ReactJsonAgent(
            tools=[retriever_tool],
            llm_engine=self.llm_engine,
            max_iterations=4,
            verbose=2,
        )

    def llm_engine(self, messages, stop_sequences=["Task"]) -> str:
        response_big = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.3,
            n=1,
            stop=stop_sequences + ["<end_action>"],
            max_tokens=1024,
        )

        return response_big.choices[0].message.content

    def build_database(self) -> None:
        def emb_text(text):
            return self.embedding_model.embed_query(text)

        test_embedding = emb_text("This is a test")
        embedding_dim = len(test_embedding)

        if self.milvus_client.has_collection(self.collection_name):
            self.milvus_client.drop_collection(self.collection_name)

        for doc in self.docs:
            chunks = split_text(doc, self.text_splitter)
            text_lines = [chunk.page_content for chunk in chunks]

            self.milvus_client.create_collection(
                collection_name=self.collection_name,
                dimension=embedding_dim,
                metric_type="IP",  # Inner product distance
                consistency_level="Strong",  # Strong consistency level
            )

            data = []

            for i, line in enumerate(tqdm(text_lines, desc="Creating embeddings")):
                data.append({"id": i, "vector": emb_text(line), "text": line})

            insert_res = self.milvus_client.insert(
                collection_name=self.collection_name, data=data
            )
            insert_res["insert_count"]

    def question(self, question: str) -> str:
        enchanced_question = f"""Using the information contained in your knowledge base, which you can access with the 'retriever' tool, give a comprehensive answer to the question below.
Respond only to the question asked, response should be concise and relevant to the question.
Your knowledge base is in English, thus, if the question asked by the user is not in English, you need to translate it into English.
If you cannot find information, do not give up and try calling your retriever again with different arguments!
If you did not find anything after calling retriever multiple times, do not come up with some answer yourself, tell you do not know the answer to the question and that the user should contact the Education Department.
You should call retriever at least once, even if you think you cannot help with the query -- because, for example, if user has suicide thoughts, you can find information on local mental health hotline in the knowledge base.
Your queries should not be questions but affirmative form sentences: e.g. rather than "Which scholarships are available in Skoltech?", query should be "Scholarships in Skoltech".
If the user asks you a question in a language other than English, you should answer in that language, e.g. if the question is in Russian, your final answer should be in Russian.
The knowledge base is about Russian University called Skoltech. Questions on all other themes should not be answered if responses are not present in the knowledge base.

Question:
{question}"""
        return self.agent.run(enchanced_question)


if __name__ == "__main__":
    c = Chatbot(
        f"{os.environ.get('CHATBOT_MODEL')}",
        f"{os.environ.get('API_LINK')}",
        f"{os.environ.get('VSEGPT_TOKEN')}",
        ["orientation.md"],
    )
    c.build_database()
    print(c.question("Which scholarships are available in Skoltech?"))
