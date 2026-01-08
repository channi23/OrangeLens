from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


_URL_RE = re.compile(r"(https?://\\S+)")
_SENSATIONAL_TERMS = {
    "breaking",
    "shocking",
    "unbelievable",
    "miracle",
    "secret",
    "guaranteed",
    "limited time",
    "click here",
}


def _extract_urls(text: str) -> List[str]:
    return _URL_RE.findall(text or "")


def verify_text(text: Optional[str]) -> Dict[str, Any]:
    normalized = (text or "").strip()
    lower = normalized.lower()
    urls = _extract_urls(normalized)

    if not normalized:
        return {
            "verdict": "unknown",
            "truth_score": 0.4,
            "confidence": "low",
            "explanation": "Text content is missing or empty.",
            "citations": [],
        }

    sensational = any(term in lower for term in _SENSATIONAL_TERMS)
    if sensational:
        verdict = "misleading"
        truth_score = 0.2
        confidence = "medium"
        explanation = "Text contains sensational indicators; requires additional corroboration."
    else:
        verdict = "unknown"
        truth_score = 0.5
        confidence = "low"
        explanation = "Text requires independent verification."

    citations = [{"title": None, "url": url} for url in urls]

    return {
        "verdict": verdict,
        "truth_score": truth_score,
        "confidence": confidence,
        "explanation": explanation,
        "citations": citations,
    }
