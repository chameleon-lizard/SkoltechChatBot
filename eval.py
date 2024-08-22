import pathlib
import json
from main import Chatbot
from tqdm import tqdm
import openai

import pandas as pd

import os
import dotenv
import threading
from queue import Queue

dotenv.load_dotenv("env")

judge_model = "openai/gpt-4o-mini"

c = Chatbot(
    f"{os.environ.get('CHATBOT_MODEL')}",
    f"{os.environ.get('API_LINK')}",
    f"{os.environ.get('VSEGPT_TOKEN')}",
    ["orientation.md"],
    verbose=False,
)
c.build_database()

eval_file = "questions_ru.json"
data = json.loads(pathlib.Path(eval_file).read_text())

outputs = []
for example in tqdm(data):
    question = example["question"]
    if question in [output["question"] for output in outputs]:
        continue

    answer = c.question(question)

    result = {
        "question": question,
        "true_answer": example["answer"],
        "source_doc": example["context"],
        "generated_answer": answer,
    }

    outputs.append(result)

with open("eval_ans.json", "w") as f:
    json.dump(outputs, f)

flattened_data = json.loads(pathlib.Path("eval_ans.json").read_text())


def send_question(
    prompt: str,
):
    token = f"{os.environ.get('VSEGPT_TOKEN')}"

    client = openai.OpenAI(
        api_key=token,
        base_url="https://api.vsegpt.ru:7090/v1",
    )

    messages = []
    messages.append({"role": "user", "content": prompt})

    response_big = client.chat.completions.create(
        model=judge_model,
        messages=messages,
        temperature=0.7,
        n=1,
        max_tokens=512,
    )

    response = response_big.choices[0].message.content

    return response


EVALUATION_PROMPT = """###Task Description:
An instruction (might include an Input inside it), a response to evaluate, a reference answer that gets a score of 5, and a score rubric representing a evaluation criteria are given.
1. Write a detailed feedback that assess the quality of the response strictly based on the given score rubric, not evaluating in general.
2. After writing a feedback, write a score that is an integer between 0 and 5. You should refer to the score rubric.
3. The output format should look as follows: \"Feedback: {{write a feedback for criteria}} [RESULT] {{an integer number between 0 and 5}}\"
4. Please do not generate any other opening, closing, and explanations. Be sure to include [RESULT] in your output.

###The instruction to evaluate:
{instruction}

###Response to evaluate:
{response}

###Reference Answer (Score 5):
{reference_answer}

###Score Rubrics:
[Is the response correct, accurate, and factual based on the reference answer?]
Score 0: The response is a recommendation to refer to Education Department.
Score 1: The response is completely incorrect, inaccurate, and/or not factual.
Score 2: The response is mostly incorrect, inaccurate, and/or not factual.
Score 3: The response is somewhat correct, accurate, and/or factual.
Score 4: The response is mostly correct, accurate, and factual.
Score 5: The response is completely correct, accurate, and factual.

###Feedback:"""


sem = threading.Semaphore(6)

q_lock = threading.Lock()


def judge(item, q):
    with sem:
        eval = send_question(
            EVALUATION_PROMPT.format(
                instruction=item["question"],
                response=item["generated_answer"],
                reference_answer=item["true_answer"],
            )
        )

    try:
        feedback, score = [i.strip() for i in eval.split("[RESULT]")]
        print(f"Score: {score}\nFeedback: {feedback}")
        item["feedback"] = feedback
        item["score"] = score

        with q_lock:
            q.put(item)
    except Exception:
        return


threads = []
q = Queue()
for item in tqdm(flattened_data):
    thread = threading.Thread(target=judge, args=(item, q))
    thread.start()
    threads.append(thread)

[_.join() for _ in threads]

res = []
while not q.empty():
    res.append(q.get())

with open("eval_res.json", "w") as f:
    json.dump(res, f, indent=4)

df = pd.read_json("eval_res.json")

print(f"Eval file: {eval_file}")
print(f"Model: {os.environ.get('CHATBOT_MODEL')}\n")
print(f"Judge: {judge_model}\n")
print(df.score.value_counts(), end="\n\n")
print("Mean score: " + str(df.score[df.score != 0].mean()))
print("Median score: " + str(df.score[df.score != 0].median()))
print("Percentage: " + str(df.score[df.score != 0].mean() / 5 * 100))
