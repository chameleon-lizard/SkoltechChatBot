import pathlib
import itertools
import dotenv
import os
import openai

from pymilvus import MilvusClient
from tqdm import tqdm

from langchain_core.documents.base import Document
from langchain_community.embeddings import HuggingFaceBgeEmbeddings

from transformers.agents import Tool, ReactJsonAgent

from FlagEmbedding import FlagReranker


dotenv.load_dotenv("env")

RUSSIAN_ALPHABET = (
    "а",
    "б",
    "в",
    "г",
    "д",
    "е",
    "ж",
    "з",
    "и",
    "й",
    "к",
    "л",
    "м",
    "н",
    "о",
    "п",
    "р",
    "с",
    "т",
    "у",
    "ф",
    "х",
    "ц",
    "ч",
    "ш",
    "щ",
    "ъ",
    "ы",
    "ь",
    "э",
    "ю",
    "я",
)


def is_russian(query: str) -> bool:
    return (
        sum((_ in RUSSIAN_ALPHABET for _ in query.lower().strip()))
        > len(query.strip()) * 0.2
    )


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
        collection_name,
        embedder_func,
        reranker,
        verbose,
        translate,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.vectordb = vectordb
        self.collection_name = collection_name
        self.embedder_func = embedder_func
        self.reranker = reranker
        self.verbose = verbose
        self.translate = translate

    def forward(self, query: str) -> str:
        assert isinstance(query, str), "Your search query must be a string"
        if is_russian(query):
            query = self.translate(query, "en")

        search_res = self.vectordb.search(
            collection_name=self.collection_name,
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


def split_text(text: str) -> list[Document]:
    res = text.split("\n")

    return [
        Document(
            page_content=_,
            metadata={"source": "orientation.md"},
        )
        for _ in res
        if len(_) > 70
    ]


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
        model_name = "BAAI/bge-large-en-v1.5"
        model_kwargs = {"device": "cuda"}
        encode_kwargs = {"normalize_embeddings": True}

        self.embedding_model = HuggingFaceBgeEmbeddings(
            model_name=model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs,
        )

        self.reranker_model = FlagReranker("BAAI/bge-reranker-v2-m3", use_fp16=True)
        self.docs = [
            pathlib.Path(document_path).read_text() for document_path in document_paths
        ]

        self.milvus_client = MilvusClient(uri="./hf_milvus_demo.db")
        self.collection_name = "rag_collection"
        retriever_tool = RetrieverTool(
            self.milvus_client,
            self.collection_name,
            self.embedding_model.embed_query,
            self.reranker_model,
            self.verbose,
            self.translate,
        )

        self.agent = ReactJsonAgent(
            tools=[retriever_tool],
            llm_engine=self.llm_engine,
            max_iterations=4,
            verbose=2 if verbose else 0,
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
            chunks = split_text(doc)
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

    def translate(self, query: str, lang: str = "ru") -> str:
        match lang:
            case "ru":
                lang = "Russian"
            case "en":
                lang = "English"

        prompt = f'Please ignore all previous instructions. Please respond only in the {lang} language. Do not explain what you are doing. Do not self reference. You are an expert translator that will be tasked with translating and improving the spelling/grammar/literary quality of a piece of text. Please rewrite the translated text in your tone of voice and writing style. Ensure that the meaning of the original text is not changed. Do not translate links to websites and email addresses. Respond only with the translation, do not add any other words and phrases, do not agree with me and say "okay, here it is" and do not add any other notes. If you succeed, you will get $380. Final response should be written in {lang}.'

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": query},
        ]

        print(prompt)
        print(query)

        res = self.llm_engine(messages)

        print(res)
        return res

    def question(self, question: str) -> str:
        enchanced_question = f"""Using the information contained in your knowledge base, which you can access with the 'retriever' tool, give a comprehensive answer to the question below.
Respond only to the question asked, response should be concise and relevant to the question.
Your knowledge base is in English, thus, if the question asked by the user is not in English, you need to translate it into English.
If you cannot find information, do not give up and try calling your retriever again with different arguments!
If you did not find anything after calling retriever multiple times, do not come up with some answer yourself, tell you do not know the answer to the question and that the user should contact the Education Department.
You should call retriever at least once, even if you think you cannot help with the query -- because, for example, if user has suicide thoughts, you can find information on local mental health hotline in the knowledge base.
Your queries should not be questions but affirmative form sentences: e.g. rather than "Which scholarships are available in Skoltech?", query should be "Scholarships in Skoltech".
If the user asks you a question in a language other than English, you should answer in that language, e.g. if the question is in Russian, your final answer should be in Russian.
The knowledge base is about University called Skoltech. Questions on all other themes should not be answered if responses are not present in the knowledge base.

Question:
{question}"""

        res = self.agent.run(enchanced_question)

        if self.verbose:
            print(question, res)

        if "Thought: " in res or '"action": "' in res:
            if "final_answer" in res:
                res = res.split('final_answer"')[1]
                res = res.split("\n}")[0]
            else:
                res = "I'm sorry, I did not find any information about this topic in my knowledge base. I recommend contacting the Education Department for assistance."

        if (is_russian(question) and is_russian(res)) or (
            not is_russian(question) and is_russian(res)
        ):
            return res
        elif is_russian(question) and not is_russian(res):
            return self.translate(res, "ru")
        else:
            return self.translate(res, "en")


if __name__ == "__main__":
    c = Chatbot(
        f"{os.environ.get('CHATBOT_MODEL')}",
        f"{os.environ.get('API_LINK')}",
        f"{os.environ.get('VSEGPT_TOKEN')}",
        ["orientation.md"],
    )
    c.build_database()
    print(c.question("What are the sizes of scholarships in Skoltech?"))
