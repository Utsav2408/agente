import json
from pathlib import Path
from typing import Any, Dict, List

def load_dataset(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # handle common wrappers like {"data": [...]}
        for key in ("data", "items", "records", "rows", "examples"):
            if key in data and isinstance(data[key], list):
                return data[key]
        # single object -> wrap it
        return [data]

    raise ValueError("merged.json must contain a JSON array or an object (optionally wrapping a list).")
