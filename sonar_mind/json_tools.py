"""Turn model text into JSON, including replies wrapped in markdown fences."""

import json
import re
from typing import Any


def parse_model_json(payload: Any) -> Any:
    if isinstance(payload, (list, dict)):
        return payload
    text = str(payload).strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()
    start_candidates = [index for index in (text.find("["), text.find("{")) if index >= 0]
    if start_candidates:
        text = text[min(start_candidates) :]
    return json.loads(text)


def as_item_list(payload: Any) -> list[dict]:
    data = parse_model_json(payload)
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        for key in ("questions", "quiz", "flashcards", "cards", "items", "branches"):
            if isinstance(data.get(key), list) and key != "branches":
                items = data[key]
                break
        else:
            if "question" in data:
                items = [data]
            else:
                raise ValueError("Model JSON did not contain a list of study items.")
    else:
        raise ValueError("Model JSON was neither a list nor an object.")

    cleaned = [item for item in items if isinstance(item, dict)]
    if not cleaned:
        raise ValueError("Model JSON list did not contain objects.")
    return cleaned
