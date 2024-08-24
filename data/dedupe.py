from collections import defaultdict
from difflib import SequenceMatcher

import json
import pathlib


def difference(a, b):
    return 1 - SequenceMatcher(None, a, b).ratio()


def are_duplicates(a, b, threshold=0.1):
    return difference(a, b) < threshold


def dedupe(data, threshold=0.4):
    deduped_data = defaultdict(list)
    seen = set()

    for key, values in data.items():
        deduped_values = []
        for value in values:
            answer = value["answer"]
            if answer not in seen:
                seen.add(answer)
                deduped_values.append(value)
            else:
                for existing_value in deduped_values:
                    if are_duplicates(answer, existing_value["answer"], threshold):
                        break
                else:
                    deduped_values.append(value)
        deduped_data[key] = deduped_values

    return deduped_data


data = json.loads(pathlib.Path("rag_orientation_qa.json").read_text())
grouped = defaultdict(list)
for item in data:
    grouped[item["context"]].append(item)

deduped_data = dedupe(grouped)


def flatten(data):
    return [value for values in data.values() for value in values]


flattened_data = flatten(deduped_data)
with open("output.json", "w") as f:
    json.dump(flattened_data, f, indent=4)
