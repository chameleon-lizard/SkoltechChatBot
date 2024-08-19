import openai
import json
import pathlib
import tqdm


flattened_data = json.loads(pathlib.Path("eval_result.json").read_text())


def send_question(
    prompt: str,
):
    token = "sk-or-vv-666948b23392de00e062663b513b8b50ef62720b9e6d88f855271f685eae42e1"

    client = openai.OpenAI(
        api_key=token,
        base_url="https://api.vsegpt.ru:7090/v1",
    )

    messages = []
    messages.append({"role": "user", "content": prompt})

    response_big = client.chat.completions.create(
        model="openai/gpt-4o-2024-08-06",
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

res = []
for item in tqdm.tqdm(flattened_data):
    print(json.dumps(item, indent=2))
    eval = send_question(
        EVALUATION_PROMPT.format(
            instruction=item["question"],
            response=item["generated_answer"],
            reference_answer=item["true_answer"],
        )
    )
    feedback, score = [i.strip() for i in eval.split("[RESULT]")]
    item["feedback"] = feedback
    item["score"] = score
    res.append(item)


with open("output_scored.json", "w") as f:
    json.dump(res, f, indent=4)
