import json
import threading
import pathlib
from openai import OpenAI
from tqdm import tqdm
from queue import Queue
import dotenv

dotenv.load_dotenv("env")


question_groundedness_critique_prompt = """
You will be given a context and a question.
Your task is to provide a 'total rating' scoring how well one can answer the given question unambiguously with the given context.
Give your answer on a scale of 1 to 5, where 1 means that the question is not answerable at all given the context, and 5 means that the question is clearly and unambiguously answerable with the context.

Provide your answer as follows:

Answer:::
Evaluation: (your rationale for the rating, as a text)
Total rating: (your rating, as a number between 1 and 5)

You MUST provide values for 'Evaluation:' and 'Total rating:' in your answer.

Now here are the question and context.

Question: {question}\n
Context: {context}\n
Answer::: """

question_relevance_critique_prompt = """
You will be given a question.
Your task is to provide a 'total rating' representing how useful this question can be to first year MSc students of Skoltech University.
Give your answer on a scale of 1 to 5, where 1 means that the question is not useful at all, and 5 means that the question is extremely useful.

Provide your answer as follows:

Answer:::
Evaluation: (your rationale for the rating, as a text)
Total rating: (your rating, as a number between 1 and 5)

You MUST provide values for 'Evaluation:' and 'Total rating:' in your answer.

Now here is the question.

Question: {question}\n
Answer::: """

question_standalone_critique_prompt = """
You will be given a question.
Your task is to provide a 'total rating' representing how context-independant this question is.
Give your answer on a scale of 1 to 5, where 1 means that the question depends on additional information to be understood, and 5 means that the question makes sense by itself.
For instance, if the question refers to a particular setting, like 'in the context' or 'in the document', the rating must be 1.
The questions can contain obscure technical nouns or acronyms like Skoltech, Skolkovo and E2 R2 2036 and still be a 5: it must simply be clear to an operator with access to documentation what the question is about.

For instance, "What should we do next?" should receive a 1, since there is an implicit mention of a context, thus the question is not independant from the context.

Provide your answer as follows:

Answer:::
Evaluation: (your rationale for the rating, as a text)
Total rating: (your rating, as a number between 1 and 5)

You MUST provide values for 'Evaluation:' and 'Total rating:' in your answer.

Now here is the question.

Question: {question}\n
Answer::: """


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


def generate_synth(output, q):
    with sem:
        evaluations = {
            "groundedness": send_question(
                question_groundedness_critique_prompt.format(
                    context=output["context"], question=output["question"]
                ),
            ),
            "relevance": send_question(
                question_relevance_critique_prompt.format(question=output["question"]),
            ),
            "standalone": send_question(
                question_standalone_critique_prompt.format(question=output["question"]),
            ),
        }
        print(json.dumps(evaluations, indent=2))
    try:
        for criterion, evaluation in evaluations.items():
            score, eval = (
                int(evaluation.split("Total rating: ")[-1].strip()),
                evaluation.split("Total rating: ")[-2].split("Evaluation: ")[1],
            )
            output.update(
                {
                    f"{criterion}_score": score,
                    f"{criterion}_eval": eval,
                }
            )
        q.put(output)
    except Exception:
        return


eval_data = json.loads(pathlib.Path("eval.json").read_text())

threads = []
sem = threading.Semaphore(6)
q = Queue()
for sampled_context in tqdm(eval_data):
    thread = threading.Thread(target=generate_synth, args=(sampled_context, q))
    thread.start()
    threads.append(thread)

[_.join() for _ in threads]

outputs = []
while not q.empty():
    outputs.append(q.get())

pathlib.Path("eval_res.json").write_text(json.dumps(outputs, indent=2))
