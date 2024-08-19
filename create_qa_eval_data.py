import pandas as pd
import json
import datasets
import pathlib

data = json.loads(pathlib.Path("eval_res.json").read_text())

generated_questions = pd.DataFrame.from_dict(data)

print("Evaluation dataset before filtering:")
print(
    generated_questions[
        [
            "question",
            "answer",
            "groundedness_score",
            "relevance_score",
            "standalone_score",
        ]
    ]
)
generated_questions = generated_questions.loc[
    (generated_questions["groundedness_score"] >= 4)
    & (generated_questions["relevance_score"] >= 4)
    & (generated_questions["standalone_score"] >= 4)
]
print("============================================")
print("Final evaluation dataset:")
print(
    generated_questions[
        [
            "question",
            "answer",
            "groundedness_score",
            "relevance_score",
            "standalone_score",
        ]
    ]
)


eval_dataset = datasets.Dataset.from_pandas(
    generated_questions, split="train", preserve_index=False
)
pathlib.Path("rag_orientation_qa.json").write_text(json.dumps(eval_dataset.to_json()))

eval_dataset.save_to_disk("rag_orientation_qa")
