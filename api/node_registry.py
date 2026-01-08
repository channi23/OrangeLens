from __future__ import annotations

import os
from typing import Any, Dict, List

import yaml


def load_node_registry(path: str) -> List[Dict[str, Any]]:
    if not path:
        return []
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    verifiers = data.get("verifiers", [])
    nodes: List[Dict[str, Any]] = []
    for entry in verifiers:
        url = str(entry.get("url", "")).strip()
        if not url:
            continue
        nodes.append(
            {
                "name": str(entry.get("name", "verifier")),
                "url": url,
                "capabilities": entry.get("capabilities", []),
            }
        )
    return nodes
