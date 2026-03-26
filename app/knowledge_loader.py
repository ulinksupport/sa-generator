# knowledge_loader.py

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def load_knowledge() -> list[dict[str, Any]]:
    knowledge_dir = Path(os.getenv("KNOWLEDGE_DIR", Path(__file__).parent / "knowledge"))
    documents: list[dict[str, Any]] = []

    if not knowledge_dir.exists():
        return documents

    for path in sorted(knowledge_dir.glob("*")):
        if not path.is_file():
            continue

        suffix = path.suffix.lower()

        try:
            if suffix == ".json":
                documents.append(
                    {
                        "name": path.name,
                        "content": json.loads(path.read_text(encoding="utf-8")),
                    }
                )
            elif suffix in {".txt", ".md"}:
                documents.append(
                    {
                        "name": path.name,
                        "content": path.read_text(encoding="utf-8"),
                    }
                )
        except Exception:
            continue

    return documents