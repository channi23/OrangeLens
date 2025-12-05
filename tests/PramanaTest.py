import os
import requests
import time
from pathlib import Path
from statistics import mean
import pandas as pd
import matplotlib.pyplot as plt

API_URL = "https://truthlens-api-276376440888.us-central1.run.app/v1"
API_KEY = os.getenv("PRAMANA_API_KEY") or os.getenv("TRUTHLENS_API_KEY") or ""

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "misinformation_final.csv"
OUTPUT_RESULTS = BASE_DIR / "truthlens_results.csv"
OUTPUT_PLOT = BASE_DIR / "truthlens_accuracy_plot.png"

TYPE_MAP = {
    "text": "text",
    "link": "link",
    "img": "image",
    "image": "image",
    "vid": "video",
    "video": "video",
}


def resolve_media_path(raw_path: str) -> Path:
    """Resolve relative paths from the CSV to actual media files."""
    candidate = Path(raw_path.strip())
    if not candidate.is_absolute():
        candidate = (BASE_DIR / candidate).resolve()
    if candidate.exists():
        return candidate

    # If file with provided suffix is missing, try to locate by stem (helps mismatched extensions)
    stem = candidate.stem if candidate.suffix else candidate.name
    search_dir = candidate.parent
    matches = list(search_dir.glob(f"{stem}.*"))
    if matches:
        return matches[0]

    raise FileNotFoundError(f"Media file not found for entry '{raw_path}' (looked in {search_dir})")


def require_api_key() -> str:
    if not API_KEY:
        raise RuntimeError("API key missing. Set PRAMANA_API_KEY or TRUTHLENS_API_KEY in your environment.")
    return API_KEY


def verify_text(text: str) -> requests.Response:
    key = require_api_key()
    return requests.post(
        f"{API_URL}/verify",
        headers={"Authorization": f"Bearer {key}"},
        data={"language": "en", "mode": "fast", "text": text},
        timeout=60,
    )


def verify_media(filepath: Path) -> requests.Response:
    key = require_api_key()
    with filepath.open("rb") as file_handle:
        return requests.post(
            f"{API_URL}/verify_media",
            headers={"Authorization": f"Bearer {key}"},
            files={"file": (filepath.name, file_handle)},
            data={"language": "en", "mode": "fast"},
            timeout=180,
        )


def load_dataset() -> pd.DataFrame:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Dataset CSV not found at {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    expected_cols = {"SNO", "type_of_verification", "content", "label", "category"}
    missing = expected_cols - set(df.columns)
    if missing:
        raise ValueError(f"Dataset missing required columns: {', '.join(sorted(missing))}")
    return df


def run_evaluation():
    df = load_dataset()
    results = []

    for _, row in df.iterrows():
        raw_type = str(row["type_of_verification"]).strip().lower()
        mapped_type = TYPE_MAP.get(raw_type)
        if not mapped_type:
            print(f"⚠️ Skipping unsupported type '{raw_type}' for row {row.get('SNO')}")
            continue
        if mapped_type == "video":
            print(f"⏭️ Skipping video row {row.get('SNO')}: video evaluations disabled for this run.")
            continue

        content = str(row["content"]).strip()
        expected = str(row["label"]).strip().lower()
        category = str(row.get("category", "")).strip()

        print(f"🔍 Verifying [{mapped_type}] → {content}")

        try:
            if mapped_type in {"text", "link"}:
                response = verify_text(content)
            elif mapped_type in {"image", "video"}:
                media_path = resolve_media_path(content)
                response = verify_media(media_path)
            else:
                print(f"⚠️ No handler for type '{mapped_type}'")
                continue

            if not response.ok:
                print(f"❌ API returned status {response.status_code}: {response.text}")
                actual_verdict = "error"
                confidence = 0
            else:
                payload = response.json()
                actual_verdict = str(payload.get("verdict", "unverifiable")).lower()
                confidence = payload.get("confidence", 0)

            results.append(
                {
                    "sno": row["SNO"],
                    "type": mapped_type,
                    "category": category,
                    "input": content,
                    "expected": expected,
                    "actual": actual_verdict,
                    "match": actual_verdict == expected,
                    "confidence": confidence,
                }
            )

        except FileNotFoundError as fnf_err:
            print(f"❌ {fnf_err}")
        except Exception as exc:
            print(f"❌ Unexpected error for row {row.get('SNO')}: {exc}")

        time.sleep(2)  # prevent rate limiting

    if not results:
        print("⚠️ No results collected. Please check dataset and API connectivity.")
        return

    matches = [r["match"] for r in results]
    accuracy = mean(matches)
    print(f"\n✅ Overall Accuracy: {accuracy * 100:.2f}%")

    results_df = pd.DataFrame(results)
    results_df.to_csv(OUTPUT_RESULTS, index=False)
    print(f"📁 Results saved to {OUTPUT_RESULTS}")

    type_groups = results_df.groupby("type")["match"].mean().mul(100)
    plt.figure(figsize=(8, 5))
    plt.bar(type_groups.index, type_groups.values)
    plt.title("TruthLens Accuracy by Verification Type")
    plt.ylabel("Accuracy (%)")
    plt.xlabel("Verification Type")
    plt.ylim(0, 100)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(OUTPUT_PLOT)
    print(f"📊 Accuracy plot saved to {OUTPUT_PLOT}")
    plt.show()


if __name__ == "__main__":
    run_evaluation()
