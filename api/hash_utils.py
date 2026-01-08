from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict


_WHITESPACE_RE = re.compile(r"\s+")


def canonicalize_text(text: str) -> str:
    if text is None:
        return ""
    trimmed = text.strip()
    return _WHITESPACE_RE.sub(" ", trimmed)


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def stable_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def hash_media_placeholder(data: bytes) -> str:
    if not data:
        return ""
    return hashlib.sha256(data).hexdigest()
