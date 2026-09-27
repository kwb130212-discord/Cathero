from __future__ import annotations

import json
from pathlib import Path

from core.engine import ActionRule


def load_action_rules(path: str = "config/actions.json") -> list[ActionRule]:
    file = Path(path)
    if not file.exists():
        return []
    data = json.loads(file.read_text(encoding="utf-8"))
    return [
        ActionRule(
            template=str(item.get("template", "")),
            enabled=bool(item.get("enabled", False)),
            click=bool(item.get("click", False)),
        )
        for item in data.get("rules", [])
        if item.get("template")
    ]
