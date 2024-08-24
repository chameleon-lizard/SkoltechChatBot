import openai
from langchain_core.documents.base import Document
import re


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


def is_link_or_email(text):
    return bool(re.match(r"^(\w+\.)?\w+\.(ru|com|net|org|gov)(\/.+)?|[\w\.-]+@[\w\.-]+\.\w+$", text, re.IGNORECASE))


def send_question(
    prompt: str,
    model: str,
    api_link: str,
    token: str,
    temperature: float,
    max_tokens: int,
):
    client = openai.OpenAI(
        api_key=token,
        base_url=api_link,
    )

    messages = []
    messages.append({"role": "user", "content": prompt})

    response_big = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        n=1,
        max_tokens=max_tokens,
    )

    response = response_big.choices[0].message.content

    return response


def split_text(text: str, document_path: str) -> list[Document]:
    res = text.split("\n")

    return [
        Document(
            page_content=_,
            metadata={"source": document_path},
        )
        for _ in res
        if len(_) > 70
    ]


