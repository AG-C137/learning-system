import json


def load_sources(path):

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data["sources"]