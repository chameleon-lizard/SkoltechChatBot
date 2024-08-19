import pathlib
import json
from main import Chatbot
from tqdm import tqdm

import os
import dotenv

dotenv.load_dotenv("env")


c = Chatbot(
    f"{os.environ.get('CHATBOT_MODEL')}",
    f"{os.environ.get('API_LINK')}",
    f"{os.environ.get('VSEGPT_TOKEN')}",
    ["orientation.md"],
)
c.build_database()
print(c.question("Which scholarships are available in Skoltech?"))

data = json.loads(pathlib.Path("output.json").read_text())

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

with open("eval_result.json", "w") as f:
    json.dump(outputs, f)
