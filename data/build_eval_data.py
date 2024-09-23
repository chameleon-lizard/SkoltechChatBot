import json
import time
import threading
import pathlib
from openai import OpenAI
from tqdm import tqdm
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from queue import Queue

import dotenv

dotenv.load_dotenv("env")

model_name = "BAAI/bge-base-en-v1.5"
model_kwargs = {"device": "cuda"}
encode_kwargs = {"normalize_embeddings": True}

embedding_model = HuggingFaceBgeEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs,
)

text_splitter = SemanticChunker(embedding_model)

doc = pathlib.Path("orientation.md").read_text()


def split_text(text: str, semantic_chunker: SemanticChunker) -> list:
    res = []
    buff = ""
    for line in text.splitlines():
        if line.strip().startswith("###"):
            res.append(buff)
            buff = ""
        buff += "\n" + line

    return semantic_chunker.create_documents(res)


def send_question(
    prompt: str,
):
    token = f"{os.environ.get('TOKEN')}"

    client = OpenAI(
        api_key=token,
        base_url="https://api.vsegpt.ru:7090/v1",
    )

    messages = []
    messages.append({"role": "user", "content": prompt})

    response_big = client.chat.completions.create(
        model="google/gemini-flash-1.5",
        messages=messages,
        temperature=0.7,
        n=1,
        max_tokens=512,
    )

    response = response_big.choices[0].message.content

    return response


def generate_synth(sampled_context, q, sem):
    if len(sampled_context) < 100:
        return

    # Generate QA couple
    time.sleep(1)
    with sem:
        output_QA_couple = send_question(
            QA_generation_prompt.format(context=sampled_context)
        )
    print(output_QA_couple)
    try:
        question = output_QA_couple.split("Factoid question: ")[-1].split("Answer: ")[0]
        answer = output_QA_couple.split("Answer: ")[-1]
        q.put(
            {
                "context": sampled_context,
                "question": question,
                "answer": answer,
            }
        )
    except Exception:
        return


chunks = split_text(doc, text_splitter)
text_lines = [chunk.page_content for chunk in chunks]

QA_generation_prompt = """
Your task is to write a factoid question and an answer given a context.
Your factoid question should be answerable with a specific, concise piece of factual information from the context.
Your factoid question should be formulated in the same style as questions users could ask in a search engine.
This means that your factoid question MUST NOT mention something like "according to the passage" or "context".
Factoid question must be not be some meta question (e.g. "what is the name of the guide for the intro course" or "what to do next"), but question referring to some fact about Skoltech, Skolkovo foundation or student life, which can be answered using provided context without any additional knowledge.

Provide your answer as follows:

Output:::
Factoid question: (your factoid question)
Answer: (your answer to the factoid question)

Now here is the context.

Context: {context}\n
Output:::"""

threads = []
sem = threading.Semaphore(6)
q = Queue()
for sampled_context in tqdm(text_lines):
    for _ in range(6):
        thread = threading.Thread(target=generate_synth, args=(sampled_context, q, sem))
        thread.start()
        threads.append(thread)

[_.join() for _ in threads]

outputs = []
while not q.empty():
    outputs.append(q.get())

pathlib.Path("eval.json").write_text(json.dumps(outputs, indent=2))
