from __future__ import annotations

from typing import Any, Dict, Optional


def verify_image(media_url: Optional[str], source_url: Optional[str]) -> Dict[str, Any]:
    url = (media_url or source_url or "").lower()

    if not url:
        return {
            "verdict": "unknown",
            "truth_score": 0.4,
            "confidence": "low",
            "explanation": "Image reference missing; unable to analyze.",
            "citations": [],
        }

    if any(token in url for token in ("ai", "generated", "deepfake")):
        return {
            "verdict": "misleading",
            "truth_score": 0.2,
            "confidence": "medium",
            "explanation": "Image source indicates possible synthetic origin.",
            "citations": [{"title": None, "url": media_url or source_url}],
        }

    return {
        "verdict": "unknown",
        "truth_score": 0.5,
        "confidence": "low",
        "explanation": "Image verification requires forensic analysis beyond MVP.",
        "citations": [{"title": None, "url": media_url or source_url}],
    }
