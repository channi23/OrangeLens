from __future__ import annotations

from typing import Any, Dict, Iterable, List

from api.hash_utils import stable_json, sha256_hex


def aggregate_results(results: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    results_list = list(results)
    if not results_list:
        return {
            "verdict": "unknown",
            "truth_score": 0.5,
            "confidence": "low",
            "explanation": "No verifier results available.",
            "citations": [],
        }

    truth_scores = [float(r.get("truth_score", 0.5)) for r in results_list]
    avg_score = sum(truth_scores) / len(truth_scores)
    avg_score = max(0.0, min(1.0, avg_score))

    if avg_score >= 0.7:
        verdict = "true"
        confidence = "high"
    elif avg_score <= 0.3:
        verdict = "misleading"
        confidence = "high"
    else:
        verdict = "unknown"
        confidence = "low"

    explanation = results_list[0].get("explanation") or "Aggregated verification results."
    citations = _merge_citations(results_list)

    return {
        "verdict": verdict,
        "truth_score": avg_score,
        "confidence": confidence,
        "explanation": explanation,
        "citations": citations,
    }


def stable_verdict_hash(payload: Dict[str, Any]) -> str:
    return sha256_hex(stable_json(payload))


def _merge_citations(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    merged: List[Dict[str, Any]] = []
    for result in results:
        for citation in result.get("citations", []) or []:
            url = citation.get("url")
            title = citation.get("title")
            key = (title or "", url or "")
            if key in seen or (not title and not url):
                continue
            seen.add(key)
            merged.append({"title": title, "url": url})
    return merged
