import openai
import pathlib
import json
import os
import dotenv
import tqdm


dotenv.load_dotenv(".env")


def translate(query: str) -> str:
    prompt = 'Please ignore all previous instructions. Please respond only in the Russian language. Do not explain what you are doing. Do not self reference. You are an expert translator that will be tasked with translating and improving the spelling/grammar/literary quality of a piece of text. Please rewrite the translated text in your tone of voice and writing style. Ensure that the meaning of the original text is not changed. Respond only with the translation, do not add any other words and phrases, do not agree with me and say "okay, here it is" and do not add any other notes. If you succeed, you will get $380.'

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": query},
    ]

    client = openai.OpenAI(
        api_key=f"{os.environ.get('VSEGPT_TOKEN')}",
        base_url=f"{os.environ.get('API_LINK')}",
    )

    response_big = client.chat.completions.create(
        model=f"{os.environ.get('CHATBOT_MODEL')}",
        messages=messages,
        temperature=0.3,
        n=1,
        max_tokens=2048,
    )

    return response_big.choices[0].message.content


if __name__ == "__main__":
    data = json.loads(pathlib.Path("questions.json").read_text())

    res = []
    for item in tqdm.tqdm(data):
        question = translate(item["question"])
        answer = translate(item["answer"])

        res.append(
            {
                "question": question,
                "answer": answer,
                "context": item["context"],
            }
        )

    pathlib.Path("questions_ru.json").write_text(json.dumps(res, indent=2))
