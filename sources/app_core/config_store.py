from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def save_json_config(file_path: str, payload: dict[str, Any]) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=4), encoding="utf-8")


def load_json_config(file_path: str) -> dict[str, Any]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {file_path}")
    return json.loads(path.read_text(encoding="utf-8"))

