import os
import json
import logging
import asyncio
import imghdr
import mimetypes
from datetime import datetime, timedelta
import random
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.cloud import aiplatform
from google.cloud import storage
from google.cloud import bigquery
from google.cloud import secretmanager
from google.auth.exceptions import DefaultCredentialsError
from vertexai.preview.generative_models import GenerativeModel, Part
from google.api_core.exceptions import InvalidArgument, ResourceExhausted
import vertexai
import requests
import hashlib
import uuid
import re
from PIL import Image
from PIL import ExifTags
try:
    import cv2  # opencv-python-headless recommended for Cloud Run
except Exception:
    cv2 = None
try:
    import c2pa  # optional; if present, we can read C2PA manifests
except Exception:
    c2pa = None
import tempfile
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    logging.warning("pillow-heif not available, HEIF/HEIC images will not be supported.")
import pytesseract
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor
# --- Google Vision API import for web entity detection ---
from google.cloud import vision
# --- Web Entities Detection Helper ---
def detect_web_entities(image_bytes: bytes) -> dict:
    """
    Use Google Cloud Vision API to detect web entities and best guess label for an image.
    Returns a dict: { "entities": [ { "description": str, "score": float } ], "best_guess_label": str }
    """
    try:
        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=image_bytes)
        response = client.web_detection(image=image)
        web_detection = response.web_detection
        entities = []
        if web_detection.web_entities:
            for entity in web_detection.web_entities[:5]:
                entities.append({
                    "description": entity.description,
                    "score": entity.score
                })
        best_guess_label = ""
        if web_detection.best_guess_labels:
            best_guess_label = web_detection.best_guess_labels[0].label
        return {"entities": entities, "best_guess_label": best_guess_label}
    except Exception as e:
        logging.error(f"detect_web_entities failed: {e}")
        return {"entities": [], "best_guess_label": ""}

# Initialize FastAPI app
app = FastAPI(
    title="TruthLens API",
    description="AI-Powered Fact Verification API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security
security = HTTPBearer()

# --- Privacy Mode global variable ---
PRIVACY_MODE = False

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "orange-lens-472108")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
BUCKET_NAME = os.getenv("STORAGE_BUCKET", "truthlens-evidence-orange-lens-472108")
DATASET_ID = os.getenv("BIGQUERY_DATASET", "truthlens_logs")
TABLE_ID = os.getenv("BIGQUERY_TABLE", "verification_requests")
# SERPER endpoint is static; key is loaded below with env->Secret Manager precedence
SERPER_API_ENDPOINT = os.getenv("SERPER_API_ENDPOINT", "https://google.serper.dev/news")
# WebRisk URL is static; key is loaded below with env->Secret Manager precedence
WEBRISK_API_URL = "https://webrisk.googleapis.com/v1/uris:search"

os.environ["GOOGLE_CLOUD_AI_PLATFORM_API_VERSION"] = "v1beta"
try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
except DefaultCredentialsError as exc:
    logging.warning(f"Vertex AI initialization skipped (credentials missing): {exc}")
except Exception as exc:
    logging.warning(f"Vertex AI initialization failed: {exc}")
try:
    logging.error(f"Startup config: PROJECT_ID={PROJECT_ID}, LOCATION={LOCATION}")
except Exception:
    pass
# Clients (lazily degrade if credentials are not available)
def _init_storage_client() -> Optional[storage.Client]:
    try:
        return storage.Client()
    except DefaultCredentialsError as exc:
        logging.warning(f"Google Cloud Storage client unavailable: {exc}")
    except Exception as exc:
        logging.warning(f"Google Cloud Storage client initialization failed: {exc}")
    return None


def _init_bigquery_client() -> Optional[bigquery.Client]:
    try:
        return bigquery.Client()
    except DefaultCredentialsError as exc:
        logging.warning(f"BigQuery client unavailable: {exc}")
    except Exception as exc:
        logging.warning(f"BigQuery client initialization failed: {exc}")
    return None


def _init_secret_manager_client() -> Optional[secretmanager.SecretManagerServiceClient]:
    try:
        return secretmanager.SecretManagerServiceClient()
    except DefaultCredentialsError as exc:
        logging.warning(f"Secret Manager client unavailable: {exc}")
    except Exception as exc:
        logging.warning(f"Secret Manager client initialization failed: {exc}")
    return None


storage_client = _init_storage_client()
bigquery_client = _init_bigquery_client()
secret_client = _init_secret_manager_client()
executor = ThreadPoolExecutor(max_workers=4)

# -------- Unified secret loading with precedence: ENV -> Secret Manager --------
_SECRET_CACHE: Dict[str, str] = {}

def get_secret_cached(secret_name: str) -> str:
    """
    Read once from Secret Manager and cache in-process.
    Returns empty string if not found.
    """
    if not secret_name:
        return ""
    if secret_name in _SECRET_CACHE:
        return _SECRET_CACHE[secret_name]
    if secret_client is None:
        logging.warning(f"Secret Manager client unavailable; returning empty secret for '{secret_name}'")
        _SECRET_CACHE[secret_name] = ""
        return ""
    try:
        name = f"projects/{PROJECT_ID}/secrets/{secret_name}/versions/latest"
        response = secret_client.access_secret_version(request={"name": name})
        value = response.payload.data.decode("UTF-8")
        _SECRET_CACHE[secret_name] = value
        return value
    except Exception as e:
        logging.warning(f"Secret '{secret_name}' not found or inaccessible: {e}")
        _SECRET_CACHE[secret_name] = ""
        return ""

def load_runtime_keys() -> Dict[str, str]:
    """
    Load all runtime API keys with the rule:
    1) Environment variable if set
    2) Secret Manager fallback
    Returns a dict for transparent logging (no values logged, only source).
    """
    sources = {}

    # TRUTHLENS internal app key
    global TRUTHLENS_APP_KEY
    TRUTHLENS_APP_KEY = os.getenv("TRUTHLENS_API_KEY") or get_secret_cached("truthlens-api-key")
    sources["TRUTHLENS_API_KEY"] = "env" if os.getenv("TRUTHLENS_API_KEY") else ("secret:truthlens-api-key" if TRUTHLENS_APP_KEY else "missing")
    if TRUTHLENS_APP_KEY:
        logging.info("TRUTHLENS_API_KEY loaded securely (source: %s)", sources["TRUTHLENS_API_KEY"])

    # SERPER news key
    global SERPER_API_KEY
    SERPER_API_KEY = os.getenv("SERPER_API_KEY") or get_secret_cached("serper-api-key")
    sources["SERPER_API_KEY"] = "env" if os.getenv("SERPER_API_KEY") else ("secret:serper-api-key" if SERPER_API_KEY else "missing")
    if SERPER_API_KEY:
        logging.info("SERPER_API_KEY loaded securely (source: %s)", sources["SERPER_API_KEY"])

    # WebRisk key (optional; secret might be named 'webrisk-api-key' if present)
    global WEBRISK_API_KEY
    WEBRISK_API_KEY = os.getenv("WEBRISK_API_KEY") or get_secret_cached("webrisk-api-key")
    sources["WEBRISK_API_KEY"] = "env" if os.getenv("WEBRISK_API_KEY") else ("secret:webrisk-api-key" if WEBRISK_API_KEY else "missing")
    if WEBRISK_API_KEY:
        logging.info("WEBRISK_API_KEY loaded securely (source: %s)", sources["WEBRISK_API_KEY"])

    # Fact Check key is also used in its function, but we prefetch for visibility
    global FACT_CHECK_API_KEY_PREFETCH
    FACT_CHECK_API_KEY_PREFETCH = os.getenv("FACT_CHECK_API_KEY") or get_secret_cached("fact-check-api-key")
    sources["FACT_CHECK_API_KEY"] = "env" if os.getenv("FACT_CHECK_API_KEY") else ("secret:fact-check-api-key" if FACT_CHECK_API_KEY_PREFETCH else "missing")
    if FACT_CHECK_API_KEY_PREFETCH:
        logging.info("FACT_CHECK_API_KEY loaded securely (source: %s)", sources["FACT_CHECK_API_KEY"])

    # Gemini API key (optional when GEMINI_MODE=api_key) – we just expose source
    global GEMINI_API_KEY
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_EXPRESS_API_KEY") or get_secret_cached("gemini-express-api-key")
    if os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_EXPRESS_API_KEY"):
        sources["GEMINI_API_KEY"] = "env"
    else:
        sources["GEMINI_API_KEY"] = "secret:gemini-express-api-key" if GEMINI_API_KEY else "missing"
    if GEMINI_API_KEY:
        logging.info("GEMINI_API_KEY loaded securely (source: %s)", sources["GEMINI_API_KEY"])

    logging.info("🔐 Runtime key sources: " + json.dumps(sources, ensure_ascii=False))
    return sources

# Load keys on startup
load_runtime_keys()
# --- Link Verification Helpers ---

# --- Claim Verification Cache Helpers (Unified cache_key approach) ---
def get_claim_cache_table():
    if bigquery_client is None:
        raise RuntimeError("BigQuery client unavailable")
    table_name = f"{PROJECT_ID}.{DATASET_ID}.verification_cache"
    return bigquery_client.dataset(DATASET_ID).table("verification_cache"), table_name

def get_image_hash(image_bytes: bytes) -> str:
    """Return SHA256 hash for image bytes."""
    return hashlib.sha256(image_bytes).hexdigest() if image_bytes else ""

def generate_cache_key(text: str, image_bytes: Optional[bytes]) -> str:
    """
    Generate a unified cache key as SHA256 hash of text and image bytes (if present).
    """
    h = hashlib.sha256()
    h.update((text or "").encode())
    if image_bytes:
        h.update(image_bytes)
    return h.hexdigest()

async def refresh_cache_if_stale(cache_key: str, text: str, image_bytes: Optional[bytes], image_mime: str):
    """
    Asynchronously refresh the cache if the cache is older than 12 hours.
    """
    if bigquery_client is None:
        return
    try:
        _, table_name = get_claim_cache_table()
        query = f"""
            SELECT timestamp FROM `{table_name}`
            WHERE cache_key = @cache_key
              AND TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), timestamp, DAY) < 30
            ORDER BY timestamp DESC
            LIMIT 1
        """
        job = bigquery_client.query(
            query,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("cache_key", "STRING", cache_key)
                ]
            )
        )
        rows = list(job)
        if not rows:
            return
        ts = rows[0]["timestamp"]
        # Parse timestamp as datetime
        if isinstance(ts, str):
            ts_dt = datetime.fromisoformat(ts.replace("Z", "+00:00")) if "T" in ts else datetime.strptime(ts, "%Y-%m-%d %H:%M:%S.%f%z")
        else:
            ts_dt = ts
        age_hours = (datetime.utcnow() - ts_dt.replace(tzinfo=None)).total_seconds() / 3600.0
        if age_hours > 12:
            # Refresh: re-run verification and cache it
            request_id = str(uuid.uuid4())
            try:
                # Use text and image_bytes as available
                bundle = await process_verification_request(
                    request_id=request_id,
                    text=text,
                    language="en",
                    mode="fast",
                    image_bytes=image_bytes,
                    image_mime=image_mime,
                )
                # Already cached by process_verification_request
                logging.info(f"Refreshed cache for {cache_key} (age: {age_hours:.1f}h)")
            except Exception as e:
                logging.error(f"Cache refresh failed for {cache_key}: {e}")
    except Exception as e:
        logging.error(f"Cache refresh check failed: {e}")

def get_cached_verification(cache_key: str) -> Optional[dict]:
    """Retrieve cached verification result from BigQuery using unified cache_key (30-day TTL)."""
    if bigquery_client is None:
        return None
    try:
        _, table_name = get_claim_cache_table()
        query = f"""
            SELECT data, text, timestamp FROM `{table_name}`
            WHERE cache_key = @cache_key
              AND TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), timestamp, DAY) < 30
            ORDER BY timestamp DESC
            LIMIT 1
        """
        job = bigquery_client.query(query, job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("cache_key", "STRING", cache_key),
            ]
        ))
        rows = list(job)
        if rows:
            # Schedule async refresh if stale (don't block)
            try:
                # Use text from row for refresh
                row = rows[0]
                text = row.get("text") if hasattr(row, "get") else row.text
                # Schedule the async refresh (image_bytes not available here; only text)
                asyncio.create_task(refresh_cache_if_stale(cache_key, text, None, "image/jpeg"))
            except Exception as e:
                logging.error(f"Failed to schedule cache refresh: {e}")
            return json.loads(rows[0]["data"])
    except Exception as e:
        logging.error(f"BigQuery verification cache lookup failed: {e}")
    return None

def cache_verification(cache_key: str, data: dict, text: str):
    """Cache new verification result in BigQuery using unified cache_key."""
    if bigquery_client is None:
        return
    try:
        _, table_name = get_claim_cache_table()
        row = {
            "cache_key": cache_key,
            "text": text[:1000],
            "verdict": data.get("verdict", "unknown"),
            "confidence": float(data.get("confidence", 0.0)),
            "explanation": data.get("explanation", "")[:2000],
            "citations": json.dumps(data.get("citations", []), ensure_ascii=False),
            "timestamp": datetime.utcnow().isoformat(),
            "data": json.dumps(data, ensure_ascii=False)
        }
        errors = bigquery_client.insert_rows_json(table_name, [row])
        if errors:
            logging.error(f"BigQuery cache insert errors: {errors}")
    except Exception as e:
        logging.error(f"BigQuery cache insert failed: {e}")
def get_url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()

def get_link_cache_table():
    if bigquery_client is None:
        raise RuntimeError("BigQuery client unavailable")
    table_name = f"{PROJECT_ID}.{DATASET_ID}.link_verification_cache"
    return bigquery_client.dataset(DATASET_ID).table("link_verification_cache"), table_name

def cache_link_verification(url: str, data: dict):
    """Cache link verification result in BigQuery"""
    if bigquery_client is None:
        return
    try:
        _, table_name = get_link_cache_table()
        row = {
            "url_hash": get_url_hash(url),
            "url": url,
            "data": json.dumps(data, ensure_ascii=False),
            "timestamp": datetime.utcnow().isoformat()
        }
        errors = bigquery_client.insert_rows_json(table_name, [row])
        if errors:
            logging.error(f"BigQuery link cache insert errors: {errors}")
    except Exception as e:
        logging.error(f"BigQuery link cache failed: {e}")

def get_cached_link_verification(url: str) -> Optional[dict]:
    """Retrieve cached link verification result from BigQuery"""
    if bigquery_client is None:
        return None
    try:
        _, table_name = get_link_cache_table()
        query = f"""
            SELECT data FROM `{table_name}`
            WHERE url_hash = @url_hash
              AND TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), timestamp, DAY) < 30
            ORDER BY timestamp DESC
            LIMIT 1
        """
        job = bigquery_client.query(query, job_config=bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("url_hash", "STRING", get_url_hash(url))]
        ))
        rows = list(job)
        if rows:
            return json.loads(rows[0]["data"])
    except Exception as e:
        logging.error(f"BigQuery link cache lookup failed: {e}")
    return None

async def fetch_url_metadata(url: str) -> dict:
    """Fetch URL metadata and headers for scanning."""
    try:
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        headers = dict(resp.headers)
        text = resp.text
        title_match = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else ""
        meta_desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', text, re.IGNORECASE)
        meta_desc = meta_desc_match.group(1).strip() if meta_desc_match else ""
        return {
            "status_code": resp.status_code,
            "headers": headers,
            "title": title,
            "meta_description": meta_desc,
            "content_length": len(text)
        }
    except Exception as e:
        logging.error(f"Metadata fetch failed for {url}: {e}")
        return {}

async def check_webrisk(url: str) -> dict:
    """Check URL against Google Web Risk API."""
    if not WEBRISK_API_KEY:
        return {"webrisk_status": "unknown", "reason": "API key not set"}
    try:
        params = {
            "uri": url,
            "key": WEBRISK_API_KEY,
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"]
        }
        resp = requests.get(WEBRISK_API_URL, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        if "threat" in data:
            return {"webrisk_status": "malicious", "threat": data["threat"]}
        else:
            return {"webrisk_status": "safe"}
    except Exception as e:
        logging.error(f"WebRisk failed for {url}: {e}")
        return {"webrisk_status": "unknown", "error": str(e)}

def manipulation_prompt(url: str, metadata: dict) -> str:
    return f"""You are a web content analyst. Given the following URL and metadata, detect if there are any signs of manipulation, misinformation, clickbait, or other deceptive techniques. Respond in JSON:
{{
  "manipulation_technique": "none | clickbait | misleading | scam | phishing | deepfake | unknown | other",
  "explanation": string
}}

URL: {url}
Title: {metadata.get('title','')}
Meta description: {metadata.get('meta_description','')}
Headers: {json.dumps(metadata.get('headers',{}), ensure_ascii=False)}
"""

async def detect_manipulation_gemini(url: str, metadata: dict) -> dict:
    """Call Gemini to detect manipulation technique for a URL."""
    model = get_gemini_model()
    prompt = manipulation_prompt(url, metadata)
    loop = asyncio.get_event_loop()
    # Run blocking Gemini call in executor
    def call_model():
        try:
            response = model.generate_content([Part.from_text(prompt)])
            parsed = _parse_json_from_text(response.text)
            if parsed:
                return parsed
        except Exception as e:
            logging.error(f"Gemini manipulation detection failed: {e}")
        return {"manipulation_technique": "unknown", "explanation": ""}
    return await loop.run_in_executor(executor, call_model)

# Load secrets
def get_secret(secret_name: str) -> str:
    """Get secret using cached helper (kept for backward compatibility)."""
    return get_secret_cached(secret_name)


def _guess_extension(mime_type: str) -> str:
    mapping = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }
    return mapping.get((mime_type or "").lower(), ".jpg")


def _parse_json_from_text(text_value: str) -> Optional[Dict[str, Any]]:
    if not text_value:
        return None
    s = text_value.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    try:
        return json.loads(s)
    except Exception:
        pass
    try:
        start = s.find('{')
        end = s.rfind('}')
        if start != -1 and end != -1 and end > start:
            return json.loads(s[start:end+1])
    except Exception:
        pass
    return None

# --- Media Forensics Helpers: EXIF, C2PA, Video Probe ---
def _safe_exif_dict(pil_image: Image.Image) -> Dict[str, Any]:
    """
    Convert PIL EXIF to a compact dict with friendly tag names.
    Only returns a small allowlist to keep payloads small.
    """
    try:
        exif = pil_image.getexif() or {}
        tag_map = {ExifTags.TAGS.get(tag_id, str(tag_id)): val for tag_id, val in exif.items()}
        allow = ["Make", "Model", "DateTimeOriginal", "DateTime", "Software", "Artist"]
        return {k: str(v)[:256] for k, v in tag_map.items() if k in allow and v is not None}
    except Exception as e:
        logging.error(f"EXIF parse failed: {e}")
        return {}

def _extract_exif_from_bytes(image_bytes: bytes) -> Dict[str, Any]:
    try:
        from io import BytesIO
        im = Image.open(BytesIO(image_bytes))
        return _safe_exif_dict(im)
    except Exception as e:
        logging.error(f"EXIF open failed: {e}")
        return {}

def _extract_c2pa_from_bytes(image_bytes: bytes) -> Dict[str, Any]:
    """
    Best-effort C2PA manifest extraction. If the optional `c2pa` module is not available,
    return a clear status so clients know capability is missing.
    """
    if c2pa is None:
        return {"available": False, "status": "c2pa-module-missing"}
    try:
        # Many Python c2pa bindings wrap a CLI. We attempt generic parse; if not supported,
        # return unavailable without failing the request.
        return {"available": True, "status": "unsupported-image-parser"}
    except Exception as e:
        logging.error(f"C2PA parse failed: {e}")
        return {"available": False, "status": "error", "error": str(e)}

def _sha256_hex(b: bytes) -> str:
    try:
        return hashlib.sha256(b or b"").hexdigest()
    except Exception:
        return ""

def _probe_video(temp_path: str) -> Dict[str, Any]:
    """
    Lightweight video probe using OpenCV if available.
    """
    if cv2 is None:
        return {"available": False, "status": "opencv-missing"}
    try:
        cap = cv2.VideoCapture(temp_path)
        if not cap.isOpened():
            return {"available": False, "status": "open-failed"}
        fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        duration_s = frame_count / fps if fps else 0.0
        cap.release()
        return {
            "available": True,
            "status": "ok",
            "fps": float(fps),
            "frame_count": frame_count,
            "width": width,
            "height": height,
            "duration_sec": float(duration_s)
        }
    except Exception as e:
        logging.error(f"Video probe failed: {e}")
        return {"available": False, "status": "error", "error": str(e)}

async def analyze_media_forensics(media_bytes: bytes, mime_type: str) -> Dict[str, Any]:
    """
    For images: return EXIF and (if available) C2PA info and web entities.
    For videos: return basic probe info and (if possible) first-frame hash and web entities from mid-frame.
    Also runs a basic DeepFake detection using frame variance for videos.
    """
    mime = (mime_type or "").lower()
    result: Dict[str, Any] = {"mime_type": mime}
    try:
        if mime.startswith("image/"):
            exif = _extract_exif_from_bytes(media_bytes)
            c2pa_info = _extract_c2pa_from_bytes(media_bytes)
            result["exif"] = exif
            result["c2pa"] = c2pa_info
            result["sha256"] = _sha256_hex(media_bytes)
            # --- Web entities detection for images ---
            try:
                entities_info = detect_web_entities(media_bytes)
                result["entities"] = entities_info
            except Exception as e:
                logging.error(f"Web entities detection failed (image): {e}")
                result["entities"] = {"entities": [], "best_guess_label": ""}
        elif mime.startswith("video/"):
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=True) as tmp:
                tmp.write(media_bytes or b"")
                tmp.flush()
                probe = _probe_video(tmp.name)
                result["probe"] = probe
                # Scene-aware extraction + OCR over selected frames
                try:
                    scene_pack = extract_scenes_and_ocr(tmp.name, max_frames=12)
                    result["scenes"] = scene_pack.get("scene_count", 0)
                    result["ocr_text"] = scene_pack.get("ocr_text", "")
                except Exception as e:
                    logging.warning(f"Scene/OCR enrichment failed: {e}")
                if "scenes" not in result:
                    result["scenes"] = 0
                if "ocr_text" not in result:
                    result["ocr_text"] = ""
                # Keyframe hash as before
                keyframe_bytes = None
                if cv2 is not None and probe.get("available"):
                    try:
                        cap = cv2.VideoCapture(tmp.name)
                        total = int(probe.get("frame_count") or 0)
                        target = max(0, total // 2)
                        cap.set(cv2.CAP_PROP_POS_FRAMES, target)
                        ok, frame = cap.read()
                        cap.release()
                        if ok:
                            ok2, jpg = cv2.imencode(".jpg", frame)
                            if ok2:
                                b = jpg.tobytes()
                                result["keyframe_sha256"] = _sha256_hex(b)
                                keyframe_bytes = b
                    except Exception as e:
                        logging.error(f"Keyframe extraction failed: {e}")
                # --- Web entities detection for video keyframe ---
                if keyframe_bytes:
                    try:
                        entities_info = detect_web_entities(keyframe_bytes)
                        result["entities"] = entities_info
                    except Exception as e:
                        logging.error(f"Web entities detection failed (video): {e}")
                        result["entities"] = {"entities": [], "best_guess_label": ""}
                else:
                    result["entities"] = {"entities": [], "best_guess_label": ""}
                # --- DeepFake detection: adaptive frame variance analysis ---
                deepfake_detection = {
                    "status": "not_run",
                    "suspicious_frames": [],
                    "confidence": 0.0,
                    "explanation": "",
                }
                if cv2 is None:
                    deepfake_detection["status"] = "opencv-missing"
                    deepfake_detection["explanation"] = "OpenCV not available; cannot run DeepFake detection."
                    logging.warning("DeepFake detection skipped: OpenCV not available")
                elif not probe.get("available"):
                    deepfake_detection["status"] = "probe-failed"
                    deepfake_detection["explanation"] = "Video probe failed; cannot run DeepFake detection."
                    logging.warning("DeepFake detection skipped: video probe failed")
                else:
                    try:
                        cap = cv2.VideoCapture(tmp.name)
                        frame_count = int(probe.get("frame_count") or 0)
                        duration = float(probe.get("duration_sec") or 0.0)
                        suspicious_frames = []
                        prev_gray = None
                        # --- Adaptive frame sampling logic ---
                        if duration <= 5:
                            max_frames = int(duration)
                        elif duration <= 10:
                            max_frames = 5
                        elif duration <= 30:
                            max_frames = 8
                        else:
                            max_frames = 10
                        max_frames = max(1, min(max_frames, frame_count))
                        if max_frames > 1:
                            step = max(1, frame_count // max_frames)
                        else:
                            step = 1
                        logging.info(f"Adaptive sampling: {max_frames} frames over {duration:.2f}s")
                        idx = 0
                        checked = 0
                        variances = []
                        while idx < frame_count and checked < max_frames:
                            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                            ret, frame = cap.read()
                            if not ret:
                                break
                            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                            if prev_gray is not None:
                                diff = cv2.absdiff(gray, prev_gray)
                                var = diff.var()
                                variances.append(var)
                                # If variance is extremely low (almost identical frames), flag as suspicious
                                if var < 2.0:
                                    suspicious_frames.append(idx)
                            prev_gray = gray
                            checked += 1
                            idx += step
                        cap.release()
                        # Analyze suspiciousness
                        suspicious_ratio = len(suspicious_frames) / float(max_frames) if max_frames else 0.0
                        confidence = min(1.0, suspicious_ratio * 2)  # Scale up, but cap at 1.0
                        if suspicious_ratio > 0.5:
                            explanation = (
                                f"Over {int(suspicious_ratio*100)}% of sampled frames are nearly identical, "
                                "which may indicate frame reuse or synthetic content (possible DeepFake)."
                            )
                            status = "suspicious"
                        else:
                            explanation = (
                                "Frame variance is within normal range for sampled frames. "
                                "No strong DeepFake signals detected."
                            )
                            status = "ok"
                        deepfake_detection.update({
                            "status": status,
                            "suspicious_frames": suspicious_frames,
                            "confidence": confidence,
                            "explanation": explanation,
                        })
                        logging.info(
                            f"DeepFake detection run: status={status}, suspicious_frames={len(suspicious_frames)}, confidence={confidence:.2f}"
                        )
                    except Exception as e:
                        deepfake_detection["status"] = "error"
                        deepfake_detection["explanation"] = f"Error during DeepFake detection: {e}"
                        logging.error(f"DeepFake detection failed: {e}")
                result["deepfake_detection"] = deepfake_detection
        else:
            result["status"] = "unsupported-mime"
    except Exception as e:
        logging.error(f"analyze_media_forensics failed: {e}")
        result["status"] = "error"
        result["error"] = str(e)
    return result


# --- Video multi-keyframe extraction for Gemini multimodal analysis ---
def extract_keyframes_bytes(video_path: str, count: int = 6) -> List[bytes]:
    """
    Extract keyframes adaptively for Gemini analysis.
    Uses adaptive frame sampling: more frames for longer videos.
    """
    frames = []
    if cv2 is None:
        logging.warning("OpenCV not available for multi-frame extraction")
        return frames
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logging.warning("Failed to open video for keyframe extraction")
            return frames
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
        duration = total_frames / fps if fps else 0.0
        if total_frames == 0:
            return frames
        # --- Adaptive frame sampling logic ---
        if duration <= 5:
            max_frames = int(duration)
        elif duration <= 10:
            max_frames = 5
        elif duration <= 30:
            max_frames = 8
        else:
            max_frames = 10
        max_frames = max(1, min(max_frames, total_frames))
        if max_frames > 1:
            step = max(1, total_frames // max_frames)
        else:
            step = 1
        logging.info(f"Adaptive sampling for Gemini: {max_frames} frames over {duration:.2f}s")
        idx = 0
        checked = 0
        while idx < total_frames and checked < max_frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if not ok:
                idx += step
                continue
            ok2, jpg = cv2.imencode(".jpg", frame)
            if ok2:
                frames.append(jpg.tobytes())
            checked += 1
            idx += step
        cap.release()
        return frames
    except Exception as e:
        logging.error(f"extract_keyframes_bytes failed: {e}")
        return frames

def extract_scenes_and_ocr(video_path: str, max_frames: int = 12) -> Dict[str, Any]:
    """
    Scene-aware keyframe extraction with adaptive sampling and async OCR for faster video analysis.
    """
    result: Dict[str, Any] = {
        "frames": [],
        "scene_count": 0,
        "fps": 0.0,
        "frame_count": 0,
        "duration": 0.0,
        "ocr_text": ""
    }

    if cv2 is None:
        logging.warning("OpenCV not available for scene extraction")
        return result

    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logging.warning("Failed to open video for scene extraction")
            return result

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        duration = total_frames / fps if fps else 0.0

        result["fps"] = fps
        result["frame_count"] = total_frames
        result["duration"] = duration

        # --- Adaptive frame sampling ---
        if duration <= 10:
            target_frames = max(1, int(duration))
        elif duration <= 30:
            target_frames = 5
        else:
            target_frames = 8

        step = max(1, total_frames // max(target_frames, 1))
        kept_indices = list(range(0, total_frames, step))[:target_frames]
        result["scene_count"] = len(kept_indices)

        frames_bytes: List[bytes] = []
        ocr_chunks: List[str] = []

        for fi in kept_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
            ok, frame = cap.read()
            if not ok:
                continue
            ok2, jpg = cv2.imencode(".jpg", frame)
            if ok2:
                b = jpg.tobytes()
                frames_bytes.append(b)
                if pytesseract:
                    try:
                        from PIL import Image as _PILImage
                        im = _PILImage.fromarray(frame[:, :, ::-1])
                        im = im.convert("L")
                        text = pytesseract.image_to_string(im)
                        text = (text or "").strip()
                        if text:
                            ocr_chunks.append(text)
                    except Exception as ocr_exc:
                        logging.warning(f"OCR frame failed: {ocr_exc}")

        cap.release()
        result["frames"] = frames_bytes
        result["ocr_text"] = " ".join(ocr_chunks)[:2000] if ocr_chunks else ""
        return result

    except Exception as e:
        logging.error(f"extract_scenes_and_ocr failed: {e}")
        return result

# OCR extraction helper
def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    try:
        from io import BytesIO
        image = Image.open(BytesIO(image_bytes))
        image = image.convert("L")
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        logging.error(f"OCR extraction failed: {e}")
        return ""

# --- OCR text refinement with Gemini ---
async def refine_text_with_gemini(raw_text: str, language: str) -> str:
    """Use Gemini to clean/refine OCR text into a concise claim."""
    try:
        model = get_gemini_model()
        prompt = f"Clean and refine the following OCR text into a single clear factual claim for fact-checking. If not possible, return it unchanged.\n\nText: {raw_text}"
        response = model.generate_content([Part.from_text(prompt)])
        return (response.text or raw_text).strip()
    except Exception as e:
        logging.error(f"Refinement failed: {e}")
        return raw_text


async def upload_image_to_bucket(image_bytes: bytes, mime_type: str, request_id: str) -> Optional[Dict[str, str]]:
    if not image_bytes:
        return None
    if storage_client is None:
        logging.warning("Skipping image upload because Storage client is unavailable")
        return None
    blob_name = f"images/{request_id}{_guess_extension(mime_type)}"
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(image_bytes, content_type=mime_type or "image/jpeg")
    try:
        signed_url = blob.generate_signed_url(version="v4", expiration=timedelta(minutes=30), method="GET")
    except Exception as exc:
        logging.error(f"Failed to generate signed URL for {blob_name}: {exc}")
        signed_url = None
    return {
        "gs_uri": f"gs://{BUCKET_NAME}/{blob_name}",
        "signed_url": signed_url,
    }


async def generate_image_caption(image_bytes: bytes, language: str, image_mime: str = "image/jpeg") -> str:
    model = get_gemini_model()
    caption_prompt = {
        "en": "Describe the image in one neutral sentence so it can be fact checked.",
        "hi": "तथ्य जांच के लिए छवि का एक निष्पक्ष वाक्य में वर्णन करें।",
        "ta": "தகவலை சரிபார்க்க பயன்படுத்த படத்தை ஒரு குறுகிய நடுநிலை வாக்கியமாக விளக்கவும்.",
        "te": "వాస్తవ నిర్ధారణ కోసం చిత్రాన్ని ఒక తటస్థ వాక్యంలో వివరించండి.",
    }.get(language, "Describe the image in one neutral sentence so it can be fact checked.")
    try:
        parts = [Part.from_text(caption_prompt)]
        if image_bytes:
            parts.append(Part.from_data(data=image_bytes, mime_type=image_mime or "image/jpeg"))
        # Explicit logging before sending parts to Gemini
        logging.error(f"Gemini input parts: {[type(p).__name__ for p in parts]}")
        response = model.generate_content(parts)
        return (response.text or "").strip()
    except InvalidArgument as exc:
        logging.error(f"Gemini captioning rejected image: {exc}")
        return ""
    except Exception as exc:
        logging.error(f"Gemini caption generation failed: {exc}")
        return ""


async def search_news_fallback(query: str, language: str) -> List[Dict[str, Any]]:
    """Enhanced Serper News fallback — ensures proper news citations."""
    if not SERPER_API_KEY:
        logging.warning("SERPER_API_KEY not set — skipping news search.")
        return []
    if not query or len(query.strip()) < 3:
        logging.warning("Empty or too-short query for Serper fallback.")
        return []

    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query.strip(), "num": 5, "hl": language or "en"}

    try:
        resp = requests.post(SERPER_API_ENDPOINT, headers=headers, json=payload, timeout=20)
        logging.info(f"Serper request: {SERPER_API_ENDPOINT}, payload={payload}")
        resp.raise_for_status()
        data = resp.json()

        entries = []
        for item in data.get("news", [])[:5]:
            entries.append({
                "title": item.get("title", "Untitled"),
                "snippet": item.get("snippet") or item.get("description", ""),
                "url": item.get("link") or item.get("sourceUrl", ""),
                "source": item.get("source", "Unknown"),
            })

        if not entries:
            logging.warning("Serper returned no news results.")
        else:
            logging.info(f"Serper returned {len(entries)} news entries.")

        return entries

    except Exception as exc:
        logging.error(f"Serper news fallback failed: {exc}")
        return []


async def retrieve_supporting_evidence(claim_text: str, language: str) -> Dict[str, Any]:
    """Gather fact-check citations and fallback news evidence."""
    fact_data = await check_fact_check_api(claim_text, language)
    citations = fact_data.get("citations", []) or []
    fact_check_results = fact_data.get("fact_check_results", []) or []

    # Fallback to Serper if no citations from Fact Check API
    if not citations:
        logging.info("No Fact Check results found — using Serper news fallback.")
        citations = await search_news_fallback(claim_text, language)

    return {
        "citations": citations,
        "fact_check_results": fact_check_results,
    }


async def process_verification_request(
    request_id: str,
    text: str,
    language: str,
    mode: str,
    image_bytes: Optional[bytes],
    image_mime: str,
) -> Dict[str, Any]:
    if not (text or image_bytes):
        raise HTTPException(status_code=400, detail="Either text or image must be provided for verification.")
    language = language or "en"
    if language == "auto":
        language = detect_language(text)

    # --- Cache check (unified cache_key) ---
    cache_key = generate_cache_key(text or "", image_bytes)
    cached = get_cached_verification(cache_key)
    if cached:
        cached["cached"] = True
        return {
            "result": cached,
            "claim_text": text,
            "image_uri": None,
            "evidence_entries": [],
            "fact_check_results": [],
            "citations_raw": []
        }

    claim_text = (text or "").strip()
    image_refs: Optional[Dict[str, str]] = None
    image_uri = None
    if image_bytes:
        image_refs = await upload_image_to_bucket(image_bytes, image_mime, request_id)
        image_uri = image_refs.get("signed_url") if image_refs else None

        # --- Always extract visual context (OCR + caption) ---
        ocr_text = extract_text_from_image_bytes(image_bytes)
        caption = await generate_image_caption(image_bytes, language, image_mime)
        caption = caption.strip() if caption else ""

        # --- Combine claim text with visual description ---
        if not text:
            # If only image is provided, use extracted visual text or caption as claim
            claim_text = caption or ocr_text or "Image-only verification requested."
        else:
            # If text is provided, fuse both for better alignment
            visual_hint = caption or ocr_text
            if visual_hint:
                claim_text = f"{text}. The image shows: {visual_hint}"
            else:
                claim_text = text

        # --- Fuse detected entities from Vision to enhance claim context ---
        try:
            entities_info = detect_web_entities(image_bytes)
            entity_names = [e.get("description") for e in entities_info.get("entities", []) if e.get("score", 0) > 0.5]
            if entity_names:
                claim_text += f" The image appears to show {', '.join(entity_names)}."
                logging.info(f"Fused Vision entities into claim: {entity_names}")
        except Exception as e:
            logging.error(f"Vision entity fusion failed: {e}")

        # --- Heuristic: Verify dialogue authenticity if OCR text contains quotes or names ---
        try:
            if image_bytes and ocr_text:
                # Check for presence of any quoted text and entity names
                has_quotes = '"' in ocr_text or "'" in ocr_text or "“" in ocr_text or "”" in ocr_text
                has_names = any(name.lower() in ocr_text.lower() for name in entity_names)
                if has_quotes and has_names:
                    claim_text += " Verify if the dialogues or text attributed to these individuals are genuine or fabricated."
                    logging.info("Added heuristic for dialogue authenticity verification.")
        except Exception as e:
            logging.error(f"Dialogue authenticity heuristic failed: {e}")

    if not claim_text:
        raise HTTPException(status_code=400, detail="Unable to determine claim text from request")

    evidence_bundle = await retrieve_supporting_evidence(claim_text, language)
    citations_raw = evidence_bundle.get("citations", [])
    fact_check_raw = evidence_bundle.get("fact_check_results", [])

    evidence_entries: List[Dict[str, Any]] = []
    for item in citations_raw[:5]:
        evidence_entries.append({
            "title": item.get("title", ""),
            "snippet": item.get("snippet") or item.get("rating", ""),
            "url": item.get("url", ""),
            "source": item.get("source") or item.get("publisher", ""),
        })

    # --- Pre-enrich evidence for image cases using Serper before Gemini ---
    if image_bytes and image_mime.lower().startswith("image/"):
        try:
            logging.info("Pre-enriching with Serper news before Gemini verification (image-only or image+text)...")
            serper_query = text or await generate_image_caption(image_bytes, language, image_mime)
            if serper_query:
                serper_citations = await search_news_fallback(serper_query, language)
                if serper_citations:
                    for item in serper_citations:
                        evidence_entries.append({
                            "title": item.get("title", ""),
                            "snippet": item.get("snippet", ""),
                            "url": item.get("url", ""),
                            "source": item.get("source", "")
                        })
                    logging.info(f"✅ Pre-fused {len(serper_citations)} Serper news entries for image verification.")
                else:
                    logging.info("No Serper results found during pre-enrichment for image verification.")
        except Exception as e:
            logging.warning(f"⚠️ Pre-Gemini Serper enrichment failed: {e}")

    citation_candidates: List[Dict[str, Any]] = []
    for item in evidence_entries:
        citation_candidates.append({
            "title": item.get("title") or item.get("url") or "Source",
            "url": item.get("url", ""),
            "source": item.get("source", ""),
        })

    normalized_fact_checks: List[Dict[str, Any]] = []
    for claim in fact_check_raw:
        claim_text_fc = claim.get("text", "")
        for review in claim.get("claimReview", []):
            reviewer = review.get("publisher", {})
            if isinstance(reviewer, dict):
                reviewer_name = reviewer.get("name", "")
            else:
                reviewer_name = reviewer or ""
            normalized_fact_checks.append({
                "claim": claim_text_fc or review.get("title", ""),
                "reviewer": reviewer_name,
                "url": review.get("url", ""),
                "rating": review.get("textualRating", ""),
            })

    video_ctx = None
    if image_bytes and image_mime.lower().startswith("video/"):
        try:
            forensic_pack = await analyze_media_forensics(image_bytes, image_mime)
            ocr_text_v = forensic_pack.get("ocr_text", "")
            probe_v = forensic_pack.get("probe") or {}
            deep_v = forensic_pack.get("deepfake_detection") or {}
            video_ctx = {
                "fps": probe_v.get("fps", 0.0),
                "frame_count": probe_v.get("frame_count", 0),
                "duration": probe_v.get("duration_sec", 0.0),
                "scenes": forensic_pack.get("scenes", 0),
                "ocr_text": ocr_text_v,
                "deepfake_status": deep_v.get("status", "unknown"),
                "deepfake_confidence": deep_v.get("confidence", 0.0),
            }
        except Exception as e:
            logging.warning(f"Video forensic enrichment failed: {e}")

    gemini_result = await verify_with_gemini(
        claim_text,
        language,
        evidence_entries,
        normalized_fact_checks,
        image_bytes=image_bytes,
        image_mime=image_mime,
        video_context=video_ctx,
    )

    # (Serper enrichment for image cases has been moved up to pre-Gemini. Post-Gemini block removed.)

    # Manipulation detection using Gemini for claims
    manipulation_technique = None
    manipulation_explanation = None
    try:
        # Use Gemini to detect manipulation in the claim text itself
        manipulation_prompt_claim = f"""You are a manipulation detection assistant. Given the following claim, detect if it shows signs of manipulation, misinformation, or deceptive techniques. Respond in JSON:
{{
  "manipulation_technique": "none | clickbait | misleading | scam | phishing | deepfake | unknown | other",
  "explanation": string
}}

Claim: {claim_text}
"""
        model = get_gemini_model()
        loop = asyncio.get_event_loop()
        def call_model():
            try:
                response = model.generate_content([Part.from_text(manipulation_prompt_claim)])
                parsed = _parse_json_from_text(response.text)
                if parsed:
                    return parsed
            except Exception as e:
                logging.error(f"Gemini manipulation detection (claim) failed: {e}")
            return None
        manipulation = await loop.run_in_executor(executor, call_model)
        if manipulation:
            manipulation_technique = manipulation.get("manipulation_technique")
            manipulation_explanation = manipulation.get("explanation")
            # Merge into gemini_result
            gemini_result["manipulation_technique"] = manipulation_technique
            gemini_result["manipulation_explanation"] = manipulation_explanation
        else:
            gemini_result["manipulation_technique"] = None
            gemini_result["manipulation_explanation"] = None
    except Exception as e:
        logging.error(f"Manipulation detection (claim) failed: {e}")
        gemini_result["manipulation_technique"] = None
        gemini_result["manipulation_explanation"] = None

    normalized_citations: List[Dict[str, Any]] = []
    for entry in gemini_result.get("citations", []) or []:
        if isinstance(entry, dict):
            normalized_citations.append({
                "title": entry.get("title") or entry.get("url") or "Source",
                "url": entry.get("url", ""),
                "source": entry.get("source", entry.get("publisher", "")),
            })
        elif isinstance(entry, str):
            normalized_citations.append({
                "title": entry,
                "url": entry,
                "source": "",
            })

    if not normalized_citations:
        normalized_citations = citation_candidates

    gemini_result["citations"] = normalized_citations

    if not gemini_result.get("fact_check_results"):
        gemini_result["fact_check_results"] = normalized_fact_checks

    gemini_result.setdefault("language", language)
    gemini_result.setdefault("mode", mode)
    gemini_result.setdefault("timestamp", datetime.utcnow().isoformat())

    # --- Cache the result (unified cache_key) ---
    cache_verification(cache_key, gemini_result, claim_text)

    return {
        "result": gemini_result,
        "claim_text": claim_text,
        "image_uri": image_refs.get("gs_uri") if image_refs else None,
        "evidence_entries": evidence_entries,
        "fact_check_results": normalized_fact_checks,
        "citations_raw": citations_raw,
    }


# --- Public API Key Management ---

# Loaded during startup via load_runtime_keys(); keep fallback for safety
TRUTHLENS_APP_KEY = os.getenv("TRUTHLENS_API_KEY") or get_secret_cached("truthlens-api-key")

def generate_api_key() -> str:
    raw = uuid.uuid4().hex + os.urandom(16).hex()
    return hashlib.sha256(raw.encode()).hexdigest()

async def save_api_key(
    email: Optional[str] = None,
    valid_days: int = 30,
    rate_limit: int = 500,
    plan: str = "free"
) -> dict:
    """
    Save a new API key to the database.
    - email: Optional email address to associate with the key.
    - valid_days: Number of days the key is valid for (default 30).
    - rate_limit: Requests allowed per period (default 500).
    - plan: Optional plan name (default 'free').
    """
    key_id = str(uuid.uuid4())
    api_key = generate_api_key()
    created_at = datetime.utcnow().isoformat()
    expires_at = (datetime.utcnow() + timedelta(days=valid_days)).isoformat()
    row = {
        "key_id": key_id,
        "api_key": api_key,
        "email": email,
        "plan": plan,
        "rate_limit": rate_limit,
        "used": 0,
        "created_at": created_at,
        "expires_at": expires_at,
        "active": True
    }
    table_fqn = f"{PROJECT_ID}.{DATASET_ID}.api_keys"
    if bigquery_client is None:
        raise HTTPException(status_code=503, detail="BigQuery client unavailable")
    errors = bigquery_client.insert_rows_json(table_fqn, [row])
    if errors:
        logging.error(f"BigQuery insert errors (api_keys): {errors}")
        raise HTTPException(status_code=500, detail="Failed to create API key")
    return {
        "api_key": api_key,
        "rate_limit": rate_limit,
        "expires_at": expires_at,
        "valid_days": valid_days,
        "plan": plan,
        "email": email,
    }

async def validate_api_key_usage(api_key: str):
    """Validate and enforce rate limit for a given API key (B2B/external only)."""
    table_fqn = f"{PROJECT_ID}.{DATASET_ID}.api_keys"
    if bigquery_client is None:
        raise HTTPException(status_code=503, detail="BigQuery client unavailable")
    query = f"SELECT key_id, used, rate_limit, active FROM `{table_fqn}` WHERE api_key=@api_key LIMIT 1"
    job = bigquery_client.query(query, job_config=bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("api_key", "STRING", api_key)]
    ))
    rows = list(job)
    if not rows:
        logging.warning("B2B key (external) invalid or not found")
        raise HTTPException(status_code=403, detail="Invalid API key")
    row = rows[0]
    if not row.active:
        logging.warning("B2B key (external) inactive")
        raise HTTPException(status_code=403, detail="API key inactive")
    if row.used >= row.rate_limit:
        logging.warning("B2B key (external) rate limit exceeded")
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    # Increment usage
    update_query = f"UPDATE `{table_fqn}` SET used = used + 1 WHERE key_id = @key_id"
    bigquery_client.query(update_query, job_config=bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("key_id", "STRING", row.key_id)]
    ))

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify API key.
    - If matches internal app key, accept immediately (app key, internal).
    - Else, validate against BigQuery (B2B/external).
    """
    api_key = credentials.credentials
    if TRUTHLENS_APP_KEY and api_key == TRUTHLENS_APP_KEY:
        logging.info("App key detected (internal) - skipping B2B validation")
        return api_key
    if not TRUTHLENS_APP_KEY:
        logging.warning("No internal TRUTHLENS_APP_KEY configured; all calls require a registered B2B key.")
    # Otherwise, B2B/external key logic
    logging.info("B2B key detected (external) - validating via BigQuery")
    if bigquery_client is None:
        raise HTTPException(status_code=503, detail="BigQuery client unavailable for validation")
    await validate_api_key_usage(api_key)
    return api_key
# --- Feedback Endpoint ---
from fastapi.responses import JSONResponse
from fastapi import Query

# --- Feedback Endpoint + Feedback Stats + Confidence Adjustment + Retraining Queue ---

# Helper: async BigQuery query for feedback stats
async def get_feedback_stats(request_id: Optional[str] = None, limit: int = 10):
    if bigquery_client is None:
        raise HTTPException(status_code=503, detail="BigQuery client unavailable")
    feedback_table = f"{PROJECT_ID}.{DATASET_ID}.feedback"
    # Build query
    if request_id:
        query = f"""
            SELECT
                request_id,
                SUM(CASE WHEN feedback='upvote' THEN 1 ELSE 0 END) AS upvotes,
                SUM(CASE WHEN feedback='downvote' THEN 1 ELSE 0 END) AS downvotes
            FROM `{feedback_table}`
            WHERE request_id = @request_id
            GROUP BY request_id
        """
        params = [bigquery.ScalarQueryParameter("request_id", "STRING", request_id)]
    else:
        query = f"""
            SELECT
                request_id,
                SUM(CASE WHEN feedback='upvote' THEN 1 ELSE 0 END) AS upvotes,
                SUM(CASE WHEN feedback='downvote' THEN 1 ELSE 0 END) AS downvotes
            FROM `{feedback_table}`
            GROUP BY request_id
            ORDER BY (SUM(CASE WHEN feedback='upvote' THEN 1 ELSE 0 END) + SUM(CASE WHEN feedback='downvote' THEN 1 ELSE 0 END)) DESC
            LIMIT {limit}
        """
        params = []
    job = bigquery_client.query(query, job_config=bigquery.QueryJobConfig(query_parameters=params))
    rows = list(job)
    stats = []
    for row in rows:
        upvotes = int(row["upvotes"])
        downvotes = int(row["downvotes"])
        stats.append({
            "request_id": row["request_id"],
            "upvotes": upvotes,
            "downvotes": downvotes,
            "net_score": upvotes - downvotes,
        })
    return stats


@app.get("/v1/feedback/stats")
async def feedback_stats_endpoint(
    request_id: Optional[str] = Query(None, description="Request ID to filter stats for"),
    limit: int = Query(10, ge=1, le=50, description="Max items to return if no request_id"),
    api_key: str = Depends(verify_api_key)
):
    """
    Get feedback stats: upvotes, downvotes, net_score per request_id.
    If request_id is provided, returns stats for that request.
    Otherwise, returns top N most-voted items.
    """
    stats = await get_feedback_stats(request_id=request_id, limit=limit)
    if request_id:
        if stats:
            return stats[0]
        else:
            return {"request_id": request_id, "upvotes": 0, "downvotes": 0, "net_score": 0}
    return stats


# Helper: adjust confidence in verification_cache if too many downvotes
async def auto_adjust_confidence(request_id: str):
    if bigquery_client is None:
        return
    # Count downvotes for this request_id
    feedback_table = f"{PROJECT_ID}.{DATASET_ID}.feedback"
    query = f"""
        SELECT COUNT(*) AS downvote_count
        FROM `{feedback_table}`
        WHERE request_id = @request_id AND feedback = 'downvote'
    """
    job = bigquery_client.query(
        query,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("request_id", "STRING", request_id)]
        )
    )
    rows = list(job)
    downvote_count = int(rows[0]["downvote_count"]) if rows else 0
    if downvote_count > 3:
        # Find the cache_key for this request_id from verification_requests
        table_fqn = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
        query2 = f"SELECT text FROM `{table_fqn}` WHERE request_id=@request_id LIMIT 1"
        job2 = bigquery_client.query(
            query2,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("request_id", "STRING", request_id)]
            )
        )
        rows2 = list(job2)
        if not rows2:
            return
        text = rows2[0].get("text") if hasattr(rows2[0], "get") else rows2[0].text
        # The cache_key is generated from text and image_bytes=None
        cache_key = generate_cache_key(text or "", None)
        # Now, reduce confidence in verification_cache by 10%
        _, cache_table = get_claim_cache_table()
        # Get latest cached row
        query3 = f"""
            SELECT confidence, data, timestamp FROM `{cache_table}`
            WHERE cache_key = @cache_key
            ORDER BY timestamp DESC
            LIMIT 1
        """
        job3 = bigquery_client.query(
            query3,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("cache_key", "STRING", cache_key)]
            )
        )
        rows3 = list(job3)
        if not rows3:
            return
        confidence = float(rows3[0]["confidence"])
        data = rows3[0]["data"]
        try:
            data_json = json.loads(data)
        except Exception:
            data_json = {}
        new_confidence = round(confidence * 0.9, 5)
        data_json["confidence"] = new_confidence
        # Insert as a new row (do not overwrite old row)
        row = {
            "cache_key": cache_key,
            "text": text[:1000],
            "verdict": data_json.get("verdict", "unknown"),
            "confidence": new_confidence,
            "explanation": data_json.get("explanation", "")[:2000],
            "citations": json.dumps(data_json.get("citations", []), ensure_ascii=False),
            "timestamp": datetime.utcnow().isoformat(),
            "data": json.dumps(data_json, ensure_ascii=False)
        }
        errors = bigquery_client.insert_rows_json(cache_table, [row])
        if errors:
            logging.error(f"BigQuery auto-adjust confidence insert errors: {errors}")

# Helper: insert into retraining_queue table
async def insert_retraining_queue(request_id: str, text: str, old_verdict: str, new_verdict: Optional[str]):
    if bigquery_client is None:
        return
    # Create table if not exists (best effort, not blocking)
    retrain_table = f"{PROJECT_ID}.{DATASET_ID}.retraining_queue"
    # Table schema: request_id, text, old_verdict, new_verdict, timestamp
    # Insert row
    row = {
        "request_id": request_id,
        "text": text[:1000] if text else "",
        "old_verdict": old_verdict,
        "new_verdict": new_verdict,
        "timestamp": datetime.utcnow().isoformat()
    }
    try:
        bigquery_client.insert_rows_json(retrain_table, [row])
    except Exception as e:
        logging.error(f"Failed to insert into retraining_queue: {e}")


@app.post("/v1/feedback")
async def feedback_endpoint(request: Request, api_key: str = Depends(verify_api_key)):
    """
    Accept feedback on a verification request.
    POST JSON: { "request_id": "...", "feedback": "upvote"|"downvote", "comment": "..." }
    """
    try:
        data = await request.json()
        request_id = data.get("request_id")
        feedback = data.get("feedback")
        comment = data.get("comment", "")
        if not request_id or not feedback:
            raise HTTPException(status_code=400, detail="Missing request_id or feedback")
        if feedback not in ("upvote", "downvote"):
            raise HTTPException(status_code=400, detail="Feedback must be 'upvote' or 'downvote'")
        if bigquery_client is None:
            raise HTTPException(status_code=503, detail="BigQuery client unavailable")
        # Lookup original verification record
        table_fqn = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
        query = f"SELECT text, verdict FROM `{table_fqn}` WHERE request_id=@request_id LIMIT 1"
        job = bigquery_client.query(
            query,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("request_id", "STRING", request_id)]
            )
        )
        rows = list(job)
        if not rows:
            raise HTTPException(status_code=404, detail="Original request not found")
        row = rows[0]
        text = row.get("text") if hasattr(row, "get") else row.text
        old_verdict = row.get("verdict") if hasattr(row, "get") else row.verdict
        # Hash API key for privacy
        api_key_hash = hashlib.sha256((api_key or "").encode()).hexdigest()
        feedback_row = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "feedback": feedback,
            "comment": comment[:500],
            "api_key": api_key_hash,
            "old_verdict": old_verdict,
            "new_verdict": None,
        }
        # If downvote, trigger re-verification
        new_verdict = None
        if feedback == "downvote":
            try:
                # Re-run verification (text only, no image for now)
                bundle = await process_verification_request(
                    request_id=str(uuid.uuid4()),
                    text=text,
                    language="en",
                    mode="fast",
                    image_bytes=None,
                    image_mime="image/jpeg"
                )
                result = bundle.get("result", {})
                new_verdict = result.get("verdict")
                feedback_row["new_verdict"] = new_verdict
            except Exception as e:
                logging.error(f"Feedback re-verification failed: {e}")
        # Log feedback to BigQuery
        feedback_table = f"{PROJECT_ID}.{DATASET_ID}.feedback"
        errors = bigquery_client.insert_rows_json(feedback_table, [feedback_row])
        if errors:
            logging.error(f"BigQuery feedback insert errors: {errors}")
            raise HTTPException(status_code=500, detail="Failed to log feedback")
        # --- Auto-adjust confidence if too many downvotes (run in background) ---
        asyncio.create_task(auto_adjust_confidence(request_id))
        # --- If downvote, insert into retraining queue (background) ---
        if feedback == "downvote":
            asyncio.create_task(insert_retraining_queue(request_id, text, old_verdict, feedback_row.get("new_verdict")))
        return JSONResponse({"ok": True, "message": "Feedback received", "new_verdict": new_verdict})
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Feedback endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Feedback processing failed")
# --- URL Verification Endpoints ---
# --- Public API Key Management Endpoints ---

def send_api_key_email(email: str, api_key: str, expires_at: str, rate_limit: int):
    """
    Placeholder for sending API key to the provided email address.
    Integrate with email provider here.
    """
    logging.info(f"Mock send API key to {email}: {api_key} (expires at {expires_at}, rate_limit={rate_limit})")
    # TODO: Implement actual email sending.
    return True

@app.post("/v1/register_key")
async def register_key(request: dict):
    """
    Generate a new public API key.
    Request body can include: { "email": "...", "valid_days": 30, "rate_limit": 500, "plan": "free" }
    - email: Optional. If provided, API key will be sent to the email (mock send).
    - valid_days: Optional int, default 30.
    - rate_limit: Optional int, default 500.
    - plan: Optional string, default "free".
    org_name and plan are not required.
    """
    email = request.get("email")
    valid_days = int(request.get("valid_days", 30))
    rate_limit = int(request.get("rate_limit", 500))
    plan = request.get("plan", "free")

    record = await save_api_key(
        email=email,
        valid_days=valid_days,
        rate_limit=rate_limit,
        plan=plan,
    )

    if email:
        # Mock send the API key to the email (placeholder).
        send_api_key_email(email, record["api_key"], record["expires_at"], record["rate_limit"])
        return {
            "ok": True,
            "message": f"API key generated and sent to {email}",
            "data": {
                "email": email,
                "valid_days": record["valid_days"],
                "expires_at": record["expires_at"],
                "rate_limit": record["rate_limit"],
                "plan": record["plan"],
            }
        }
    else:
        # No email provided, return API key directly.
        return {
            "ok": True,
            "message": "API key generated successfully",
            "data": {
                "api_key": record["api_key"],
                "valid_days": record["valid_days"],
                "expires_at": record["expires_at"],
                "rate_limit": record["rate_limit"],
                "plan": record["plan"],
            }
        }

@app.get("/v1/key_usage")
async def key_usage(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get API key usage stats."""
    api_key = credentials.credentials
    table_fqn = f"{PROJECT_ID}.{DATASET_ID}.api_keys"
    if bigquery_client is None:
        raise HTTPException(status_code=503, detail="BigQuery client unavailable")
    query = f"SELECT used, rate_limit, plan, expires_at FROM `{table_fqn}` WHERE api_key=@api_key LIMIT 1"
    job = bigquery_client.query(query, job_config=bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("api_key", "STRING", api_key)]
    ))
    rows = list(job)
    if not rows:
        raise HTTPException(status_code=403, detail="Invalid API key")
    row = rows[0]
    return {"used": row.used, "rate_limit": row.rate_limit, "plan": row.plan, "expires_at": row.expires_at}


# Language detection
def detect_language(text: str) -> str:
    """Simple language detection."""
    if any(char in text for char in "అఆఇఈఉఊఋఎఏఐఒఓఔకఖగఘఙచఛజఝఞటఠడఢణతథదధనపఫబభమయరలవశషసహ"):
        return "te"  # Telugu
    elif any(char in text for char in "अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह"):
        return "hi"  # Hindi
    elif any(char in text for char in "அஆஇஈஉஊஎஏஐஒஓஔகஙசஜஞடணதநபமயரலவஶஷஸஹ"):
        return "ta"  # Tamil
    else:
        return "en"

# Gemini AI integration
# Allow overriding the model via environment variable
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

# --- Lazy Gemini initialization for faster startup ---
GEMINI_MODEL_INSTANCE = None

def get_gemini_model():
    """Initialize Gemini model only once for reuse across requests."""
    global GEMINI_MODEL_INSTANCE
    if GEMINI_MODEL_INSTANCE is None:
        try:
            GEMINI_MODEL_INSTANCE = GenerativeModel(GEMINI_MODEL)
            logging.info("✅ Gemini model initialized lazily")
        except Exception as e:
            logging.error(f"Gemini model initialization failed: {e}")
            raise
    return GEMINI_MODEL_INSTANCE

@app.on_event("startup")
async def warmup_model():
    """Warm up Gemini model during startup to prevent cold-start lag"""
    try:
        _ = get_gemini_model()
        logging.info("🔥 Gemini model warmed up successfully")
    except Exception as e:
        logging.error(f"Warmup failed: {e}")

GEMINI_MODE = os.getenv("GEMINI_MODE", "vertex")  # vertex recommended (supports text+image)
try:
    logging.info(f"✅ Using Gemini model: {GEMINI_MODEL} (mode={GEMINI_MODE})")
except Exception:
    pass


async def _generate_with_retry(
    model: GenerativeModel,
    generation_parts: List[Part],
    max_attempts: int = 3
) -> Any:
    """
    Call Gemini with exponential backoff to handle rate limiting gracefully.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            return model.generate_content(generation_parts)
        except ResourceExhausted as exc:
            if attempt == max_attempts:
                logging.error("Gemini rate limit exhausted after %d attempts: %s", attempt, exc)
                raise HTTPException(
                    status_code=503,
                    detail="AI verification temporarily rate-limited. Please retry shortly."
                )
            sleep_seconds = min(20, 2 ** attempt)
            logging.warning(
                "Gemini rate limit hit (attempt %d/%d). Retrying in %s seconds.",
                attempt,
                max_attempts,
                sleep_seconds,
            )
            await asyncio.sleep(sleep_seconds)
        except InvalidArgument as exc:
            logging.error("Gemini verification rejected input: %s", exc)
            raise HTTPException(status_code=400, detail="Gemini could not process the supplied media.")
        except Exception as exc:
            logging.exception("Gemini verification failed", exc_info=True)
            raise HTTPException(status_code=500, detail=f"AI verification failed: {str(exc)}")


async def verify_with_gemini(
    claim_text: str,
    language: str,
    evidence: List[Dict[str, Any]],
    fact_check_results: List[Dict[str, Any]],
    image_bytes: Optional[bytes] = None,
    image_mime: str = "image/jpeg",
    video_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Verify claim using Vertex Gemini with optional evidence and image context."""
    try:
        evidence_section = "\n".join([
            f"{idx + 1}. {item.get('title','')} ({item.get('source','')}) - {item.get('snippet','')}\nSource: {item.get('url','')}"
            for idx, item in enumerate(evidence[:5])
        ]) or "No external evidence retrieved."

        fact_check_section = "\n".join([
            f"- {res.get('claim','')} ({res.get('publisher','') or res.get('reviewer','')}) -> {res.get('textualRating') or res.get('rating','')} ({res.get('url','')})"
            for res in fact_check_results[:5]
        ]) or "No fact check reviews found."

        video_block = ""
        if video_context:
            vc = video_context
            video_block = f"""
Video context:
- Duration: {vc.get('duration', 0.0):.2f}s, FPS: {vc.get('fps', 0)}, Frames: {vc.get('frame_count', 0)}, Scenes: {vc.get('scenes', 0)}
- OCR text extracted (if any): "{(vc.get('ocr_text') or '')[:500]}"
- DeepFake detection: {vc.get('deepfake_status','unknown')} ({float(vc.get('deepfake_confidence',0.0))*100:.1f}% confidence)
"""

        if language == "hi":
            prompt_intro = """
आप TruthLens हैं, एक साक्ष्य-आधारित तथ्य-जांच सहायक।
आपका कार्य: दावे, साक्ष्य, और छवि/वीडियो की जाँच करना।
कृपया केवल हिंदी में उत्तर दें।
""".strip()
        elif language == "ta":
            prompt_intro = """
நீங்கள் TruthLens என்ற ஆதார அடிப்படையிலான உண்மைச் சரிபார்ப்பாளர்.
உங்கள் பணி: குற்றச்சாட்டு, ஆதாரம், மற்றும் படங்கள்/வீடியோக்களை ஆய்வு செய்தல்.
தயவுசெய்து தமிழ் மொழியிலேயே பதிலளிக்கவும்.
""".strip()
        elif language == "te":
            prompt_intro = """
మీరు TruthLens అనే సాక్ష్య ఆధారిత వాస్తవ తనిఖీ సహాయకుడు.
మీ పని: దావా, సాక్ష్యం మరియు చిత్రాలు/వీడియోలను విశ్లేషించడం.
దయచేసి సమాధానం తెలుగులో మాత్రమే ఇవ్వండి.
""".strip()
        else:
            prompt_intro = """
You are TruthLens, an evidence-driven fact-checking assistant designed to analyze both text and visual information.
Please respond only in English.
""".strip()

        current_year = datetime.utcnow().year
        prompt = f"""
{prompt_intro}

Your task:
- Examine the claim, the evidence, and (if provided) the image/video.
- If an image is included, interpret its visual context in relation to the claim. 
- If the image plausibly supports the claim without direct contradiction or deceptive alteration, classify it as "true".
- Only classify as "misleading" if clear evidence shows that the image content contradicts or misrepresents the claim.
- If a video is included, use scene-aware understanding, visible text (OCR), and any detected anomalies to inform the decision.
- Respond ONLY in JSON matching this schema:
{{ 
  "verdict": "true | false | misleading | unverifiable | unknown",
  "confidence": number,
  "explanation": string,
  "key_facts": [string],
  "citations": [string],
  "fact_check_results": [{{"claim": string, "reviewer": string, "url": string, "rating": string}}],
  "timestamp": string (ISO8601)
}}

Claim: "{claim_text}"

Evidence:
{evidence_section}

Fact check summaries:
{fact_check_section}

Image/Video context:
- If an image is attached, interpret its visual elements (text, symbols, people, or scenes) in relation to the claim.
- If a video is attached, consider motion, scene transitions, and any superimposed text for authenticity and context.
{video_block}

Rules:
- If the claim references a future year beyond {current_year}, set verdict to "unverifiable" with low confidence and explain why.
- If no direct evidence exists, reason using historical and factual context.
- Keep explanations concise and directly related to the claim and any attached image.
"""

        model = get_gemini_model()

        # --- PATCH: Video keyframe extraction for Gemini multimodal analysis (adaptive) ---
        if image_bytes and image_mime.lower().startswith("video/"):
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=True) as tmp:
                tmp.write(image_bytes)
                tmp.flush()
                if cv2 is not None:
                    cap_tmp = cv2.VideoCapture(tmp.name)
                    duration = 0.0
                    if cap_tmp.isOpened():
                        fps_tmp = cap_tmp.get(cv2.CAP_PROP_FPS) or 0.0
                        frame_count_tmp = cap_tmp.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
                        if fps_tmp:
                            duration = frame_count_tmp / fps_tmp
                    cap_tmp.release()
                    if duration > 20:
                        return {
                            "verdict": "unverifiable",
                            "confidence": 0.2,
                            "explanation": "Video too long for real-time verification.",
                            "key_facts": [],
                            "citations": [],
                            "fact_check_results": [],
                            "timestamp": datetime.utcnow().isoformat()
                        }
                scene_pack = extract_scenes_and_ocr(tmp.name, max_frames=12)
                frames = scene_pack.get("frames", [])
                frames = frames[:5]
                vc = {
                    "fps": scene_pack.get("fps", 0.0),
                    "frame_count": scene_pack.get("frame_count", 0),
                    "duration": scene_pack.get("duration", 0.0),
                    "scenes": scene_pack.get("scene_count", 0),
                    "ocr_text": scene_pack.get("ocr_text", ""),
                    "deepfake_status": (video_context or {}).get("deepfake_status", "unknown"),
                    "deepfake_confidence": (video_context or {}).get("deepfake_confidence", 0.0),
                }
                video_block = f"""
Video context:
- Duration: {vc.get('duration', 0.0):.2f}s, FPS: {vc.get('fps', 0)}, Frames: {vc.get('frame_count', 0)}, Scenes: {vc.get('scenes', 0)}
- OCR text extracted (if any): "{(vc.get('ocr_text') or '')[:500]}"
- DeepFake detection: {vc.get('deepfake_status','unknown')} ({float(vc.get('deepfake_confidence',0.0))*100:.1f}% confidence)
"""
                prompt = f"""
{prompt_intro}

Your task:
- Examine the claim, the evidence, and (if provided) the image/video.
- If an image is included, interpret its visual context in relation to the claim. 
- If the image plausibly supports the claim without direct contradiction or deceptive alteration, classify it as "true".
- Only classify as "misleading" if clear evidence shows that the image content contradicts or misrepresents the claim.
- If a video is included, use scene-aware understanding, visible text (OCR), and any detected anomalies to inform the decision.
- Respond ONLY in JSON matching this schema:
{{ 
  "verdict": "true | false | misleading | unverifiable | unknown",
  "confidence": number,
  "explanation": string,
  "key_facts": [string],
  "citations": [string],
  "fact_check_results": [{{"claim": string, "reviewer": string, "url": string, "rating": string}}],
  "timestamp": string (ISO8601)
}}

Claim: "{claim_text}"

Evidence:
{evidence_section}

Fact check summaries:
{fact_check_section}

Image/Video context:
- If an image is attached, interpret its visual elements (text, symbols, people, or scenes) in relation to the claim.
- If a video is attached, consider motion, scene transitions, and any superimposed text for authenticity and context.
{video_block}

Rules:
- If the claim references a future year beyond {current_year}, set verdict to "unverifiable" with low confidence and explain why.
- If no direct evidence exists, reason using historical and factual context.
- Keep explanations concise and directly related to the claim and any attached media.
"""
                generation_parts = [Part.from_text(prompt)]
                for frame_bytes in frames:
                    generation_parts.append(Part.from_data(data=frame_bytes, mime_type="image/jpeg"))
                logging.info(f"✅ Added {len(frames)} scene-aware keyframes for Gemini multimodal analysis.")
                response = await _generate_with_retry(model, generation_parts)
        else:
            generation_parts = [Part.from_text(prompt)]
            if image_bytes:
                generation_parts.append(Part.from_data(data=image_bytes, mime_type=image_mime or "image/jpeg"))
            logging.error(f"Gemini input parts: {[type(p).__name__ for p in generation_parts]}")
            response = await _generate_with_retry(model, generation_parts)

        model_text = getattr(response, "text", "")
        parsed = _parse_json_from_text(model_text)
        if parsed is not None:
            parsed.setdefault("timestamp", datetime.utcnow().isoformat())
            return parsed
        return {
            "verdict": "unverified",
            "confidence": 0.5,
            "explanation": model_text or "Gemini returned no parsable JSON",
            "key_facts": [],
            "citations": [],
            "fact_check_results": [],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logging.exception("Gemini verification failed", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI verification failed: {str(e)}")

# Google Fact Check API integration
async def check_fact_check_api(text: str, language: str = "en") -> Dict[str, Any]:
    """Check against Google Fact Check API with robust fallback."""
    try:
        lang_map = {"en": "en", "hi": "hi", "ta": "ta"}
        url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

        params = {
            "query": text.strip(),
            "languageCode": lang_map.get(language, "en"),
            "pageSize": 5,
        }

        api_key = os.getenv("FACT_CHECK_API_KEY") or FACT_CHECK_API_KEY_PREFETCH or get_secret_cached("fact-check-api-key")
        if not api_key:
            logging.warning("Fact Check API key missing — skipping API call.")
            return {"citations": [], "fact_check_results": []}

        headers = {
            "X-Goog-Api-Key": api_key,
            "Content-Type": "application/json; charset=utf-8",
        }

        response = requests.get(url, params=params, headers=headers, timeout=15)
        logging.info(f"Fact Check API Request URL: {response.url}")
        response.raise_for_status()

        data = response.json()
        citations = []
        for claim in data.get("claims", []):
            for review in claim.get("claimReview", []):
                citations.append({
                    "title": review.get("title", ""),
                    "url": review.get("url", ""),
                    "publisher": review.get("publisher", {}).get("name", ""),
                    "rating": review.get("textualRating", ""),
                    "date": review.get("reviewDate", "")
                })

        return {
            "citations": citations,
            "fact_check_results": data.get("claims", []),
        }

    except Exception as e:
        logging.error(f"Fact Check API failed or empty: {e}")
        return {"citations": [], "fact_check_results": []}

# Storage operations
async def store_evidence(
    request_id: str,
    image_data: Optional[bytes],
    response_data: Dict[str, Any],
    existing_image_uri: Optional[str] = None,
    image_mime: str = "image/jpeg",
):
    """Store evidence in Cloud Storage"""
    if storage_client is None:
        logging.warning("Storage client unavailable; skipping evidence persistence")
        return
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        
        # Store image if provided
        if image_data and not existing_image_uri:
            image_blob = bucket.blob(f"images/{request_id}{_guess_extension(image_mime)}")
            image_blob.upload_from_string(image_data, content_type=image_mime or "image/jpeg")
        
        # Store response
        response_blob = bucket.blob(f"responses/{request_id}.json")
        response_blob.upload_from_string(
            json.dumps(response_data, indent=2, ensure_ascii=False),
            content_type="application/json"
        )
        
    except Exception as e:
        logging.error(f"Storage operation failed: {e}")

# BigQuery logging
async def log_request(request_id: str, text: str, mode: str, language: str,
                     verdict: str, confidence: float, latency: float, cost: float):
    """Log request to BigQuery"""
    if bigquery_client is None:
        logging.warning("BigQuery client unavailable; skipping request logging")
        return
    try:
        table = bigquery_client.get_table(f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}")
        # Redact text if privacy mode is enabled
        global PRIVACY_MODE
        log_text = text
        if PRIVACY_MODE:
            log_text = '[REDACTED]'
        row = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "text": log_text[:1000],  # Truncate long text
            "mode": mode,
            "language": language,
            "verdict": verdict,
            "confidence": confidence,
            "latency_ms": latency,
            "cost_usd": cost,
            "user_hash": hashlib.sha256((log_text or '').encode()).hexdigest()[:16]  # Anonymized user ID
        }
        errors = bigquery_client.insert_rows_json(table, [row])
        if errors:
            logging.error(f"BigQuery insert errors: {errors}")
    except Exception as e:
        logging.error(f"BigQuery logging failed: {e}")

@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/v1/verify-test")
async def verify_claim_test(request: dict):
    """Test endpoint: run verification pipeline without authentication."""
    request_id = str(uuid.uuid4())
    try:
        text = request.get("text", "")
        mode = request.get("mode", "fast")
        language = request.get("language", "en")
        bundle = await process_verification_request(
            request_id=request_id,
            text=text,
            language=language,
            mode=mode,
            image_bytes=None,
            image_mime="image/jpeg",
        )
        response_payload = bundle["result"].copy()
        response_payload["request_id"] = request_id
        # Ensure manipulation fields present
        if "manipulation_technique" not in response_payload or "manipulation_explanation" not in response_payload:
            # Fallback: run manipulation detection if not present
            try:
                manipulation_prompt_claim = f"""You are a manipulation detection assistant. Given the following claim, detect if it shows signs of manipulation, misinformation, or deceptive techniques. Respond in JSON:
{{
  "manipulation_technique": "none | clickbait | misleading | scam | phishing | deepfake | unknown | other",
  "explanation": string
}}

Claim: {bundle.get('claim_text','')}
"""
                model = get_gemini_model()
                loop = asyncio.get_event_loop()
                def call_model():
                    try:
                        response = model.generate_content([Part.from_text(manipulation_prompt_claim)])
                        parsed = _parse_json_from_text(response.text)
                        if parsed:
                            return parsed
                    except Exception as e:
                        logging.error(f"Gemini manipulation detection (claim) failed: {e}")
                    return None
                manipulation = await loop.run_in_executor(executor, call_model)
                response_payload["manipulation_technique"] = manipulation.get("manipulation_technique") if manipulation else None
                response_payload["manipulation_explanation"] = manipulation.get("explanation") if manipulation else None
            except Exception as e:
                logging.error(f"Manipulation detection (verify-test) failed: {e}")
                response_payload["manipulation_technique"] = None
                response_payload["manipulation_explanation"] = None
        return response_payload
    except Exception as e:
        logging.exception(f"Verification failed for request {request_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

@app.post("/v1/verify")
async def verify_claim(
    request: Request,
    text: str = Form(""),
    mode: str = Form("fast"),
    language: str = Form("en"),
    image: Optional[UploadFile] = File(None),
    privacy: bool = Form(False),
    api_key: str = Depends(verify_api_key)
):
    """Main verification endpoint. Accepts optional text and image."""
    start_time = datetime.utcnow()
    request_id = str(uuid.uuid4())

    # --- PATCH START: Handle JSON body if present ---
    if not text and not image:
        try:
            body = await request.json()
            text = body.get("text", "")
            language = body.get("language", "en")
            mode = body.get("mode", "fast")
            logging.info("verify_claim: JSON body detected (text length=%d, mode=%s, language=%s)", len(text or ""), mode, language)
        except Exception:
            pass
    # --- PATCH END ---

    global PRIVACY_MODE
    # Determine privacy mode for this request
    local_privacy_mode = bool(privacy)
    prev_privacy_mode = PRIVACY_MODE
    PRIVACY_MODE = local_privacy_mode
    try:
        text_value = text if text is not None else ""
        detected_lang = detect_language(text_value)
        if language == "auto":
            language = detected_lang

        image_data = None
        image_mime = "image/jpeg"
        # If privacy mode, skip image upload and text logging (handled in log_request)
        if not local_privacy_mode and image:
            if getattr(image, "content_type", None):
                image_mime = image.content_type or image_mime
            image_data = await image.read()
        elif local_privacy_mode:
            image_data = None

        # --- removed early-return for image-only quick verification ---

        # --- If image-only input without text, generate claim text automatically (full pipeline path) ---
        if image_data and not text_value.strip():
            logging.info("verify_claim: image-only request detected; running forensics + caption + Serper-enriched pipeline")
            # Perform EXIF/C2PA extraction
            forensics = await analyze_media_forensics(image_data, image_mime)
            # Generate short caption and refine into a claim
            caption = await generate_image_caption(image_data, language, image_mime)
            if caption:
                text_value = await refine_text_with_gemini(caption, language)
            else:
                text_value = "Verify authenticity of this image."
        # Redact text if privacy mode
        bundle = await process_verification_request(
            request_id=request_id,
            text="[REDACTED]" if local_privacy_mode else text_value,
            language=language,
            mode=mode,
            image_bytes=image_data,
            image_mime=image_mime,
        )

        final_result = bundle["result"].copy()
        final_result.update(
            {
                "request_id": request_id,
                "language": final_result.get("language", language),
                "mode": final_result.get("mode", mode),
            }
        )

        # Attach basic media forensics (EXIF + C2PA) for images
        try:
            if image_data and (image_mime or "").lower().startswith("image/"):
                forensics = await analyze_media_forensics(image_data, image_mime)
                final_result["forensics"] = forensics
        except Exception as e:
            logging.error(f"forensics attach failed: {e}")

        # Ensure manipulation fields present
        if "manipulation_technique" not in final_result or "manipulation_explanation" not in final_result:
            try:
                manipulation_prompt_claim = f"""You are a manipulation detection assistant. Given the following claim, detect if it shows signs of manipulation, misinformation, or deceptive techniques. Respond in JSON:
{{
  "manipulation_technique": "none | clickbait | misleading | scam | phishing | deepfake | unknown | other",
  "explanation": string
}}

Claim: {bundle.get('claim_text','')}
"""
                model = get_gemini_model()
                loop = asyncio.get_event_loop()

                def call_model():
                    try:
                        response = model.generate_content([Part.from_text(manipulation_prompt_claim)])
                        parsed = _parse_json_from_text(response.text)
                        if parsed:
                            return parsed
                    except Exception as e:
                        logging.error(f"Gemini manipulation detection (claim) failed: {e}")
                    return None

                manipulation = await loop.run_in_executor(executor, call_model)
                final_result["manipulation_technique"] = manipulation.get("manipulation_technique") if manipulation else None
                final_result["manipulation_explanation"] = manipulation.get("explanation") if manipulation else None
            except Exception as e:
                logging.error(f"Manipulation detection (verify) failed: {e}")
                final_result["manipulation_technique"] = None
                final_result["manipulation_explanation"] = None

        latency = (datetime.utcnow() - start_time).total_seconds() * 1000
        cost = calculate_cost(mode, len(text_value), image_data is not None)

        # Only store evidence if not in privacy mode
        await asyncio.gather(
            store_evidence(
                request_id,
                image_data,
                final_result,
                existing_image_uri=bundle.get("image_uri"),
                image_mime=image_mime,
            )
            if not local_privacy_mode
            else asyncio.sleep(0),
            log_request(
                request_id,
                text_value,
                mode,
                language,
                final_result["verdict"],
                final_result["confidence"],
                latency,
                cost,
            ),
        )

        final_result["metrics"] = {
            "latency_ms": latency,
            "cost_usd": cost,
        }
        return final_result
    except Exception as e:
        logging.exception(f"Verification failed for request {request_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")
    finally:
        # Restore previous privacy mode to avoid leaking state between requests
        PRIVACY_MODE = prev_privacy_mode


# --- Cost Calculation Function ---
def calculate_cost(mode: str, text_length: int, has_image: bool) -> float:
    """Calculate estimated cost for the request"""
    base_cost = 0.001  # Base cost per request

    # Text processing cost
    text_cost = (text_length / 1000) * 0.0001

    # Image processing cost
    image_cost = 0.002 if has_image else 0

    # Fact Check API cost (if used)
    fact_check_cost = 0.0005 if mode == "deep" else 0

    return base_cost + text_cost + image_cost + fact_check_cost

async def _verify_with_gemini_fast(claim_text: str, media_bytes: bytes, media_mime: str, language: str) -> Dict[str, Any]:
    """Fast-path Gemini verification for images/videos: focuses on authenticity and manipulation."""
    try:
        model = get_gemini_model()
        current_year = datetime.utcnow().year
        prompt = f"""
You are a forensic authenticity checker.
Your goal is to decide whether the attached media appears authentic, manipulated, or misleading.
Respond ONLY in JSON:
{{
  "verdict": "true | false | misleading | unverifiable | unknown",
  "confidence": number,
  "explanation": string
}}
Rules:
- Judge visual manipulation or inconsistencies directly.
- If evidence is insufficient, prefer 'unverifiable' but do not mention missing frames or uncertainty.
- Year {current_year} or later content may be synthetic.
Claim: {claim_text}
"""
        response = model.generate_content([
            Part.from_text(prompt),
            Part.from_data(data=media_bytes, mime_type=media_mime or "image/jpeg"),
        ])
        parsed = _parse_json_from_text(getattr(response, "text", ""))
        if parsed:
            parsed.setdefault("timestamp", datetime.utcnow().isoformat())
            return parsed
    except Exception as e:
        logging.error(f"_verify_with_gemini_fast failed: {e}")
    return {
        "verdict": "unverifiable",
        "confidence": 0.2,
        "explanation": "Fast verification failed to classify media authenticity.",
        "timestamp": datetime.utcnow().isoformat(),
    }


# --- Unified media verification endpoint (image/video) ---
@app.post("/v1/verify_media")
async def verify_media(
    text: str = Form(""),
    language: str = Form("en"),
    mode: str = Form("fast"),
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    """
    Unified media verification endpoint.
    - For images: runs fast Gemini authenticity + forensics
    - For videos: extracts keyframes, runs forensic analysis + Gemini
    """
    start_time = datetime.utcnow()
    request_id = str(uuid.uuid4())
    language = language or "en"

    try:
        if not file:
            raise HTTPException(status_code=400, detail="No media file provided")

        media_bytes = await file.read()
        media_mime = (file.content_type or "").lower()
        filename = (file.filename or "").lower()

        # Heuristic MIME detection (fallback for clients that omit Content-Type)
        if not media_mime.startswith(("image/", "video/")):
            guessed, _ = mimetypes.guess_type(filename)
            if guessed:
                media_mime = guessed.lower()

        if not media_mime.startswith(("image/", "video/")):
            image_kind = imghdr.what(None, h=media_bytes)
            if image_kind:
                media_mime = f"image/{image_kind}"

        if not media_mime.startswith(("image/", "video/")) and len(media_bytes) >= 12 and media_bytes[4:8] == b"ftyp":
            media_mime = "video/mp4"

        # --- Handle image verification (under 3s target) ---
        if media_mime.startswith("image/"):
            result = await _verify_with_gemini_fast(
                claim_text=text or "Verify authenticity of this image.",
                media_bytes=media_bytes,
                media_mime=media_mime,
                language=language,
            )
            result["forensics"] = await analyze_media_forensics(media_bytes, media_mime)
            result["type"] = "image"
            latency = (datetime.utcnow() - start_time).total_seconds()
            result["latency_sec"] = latency
            return result

        # --- Handle video verification (forensics + Gemini) ---
        elif media_mime.startswith("video/"):
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=True) as tmp:
                tmp.write(media_bytes)
                tmp.flush()

                # Extract 3 keyframes and run forensics
                keyframes = extract_keyframes_bytes(tmp.name, count=3)
                forensic = await analyze_media_forensics(media_bytes, media_mime)

                if keyframes:
                    mid_frame = keyframes[len(keyframes)//2]
                    result = await _verify_with_gemini_fast(
                        claim_text=text or "Verify authenticity of this video.",
                        media_bytes=mid_frame,
                        media_mime="image/jpeg",
                        language=language,
                    )
                    result["media_forensics"] = forensic
                    result["type"] = "video"
                    latency = (datetime.utcnow() - start_time).total_seconds()
                    result["latency_sec"] = latency
                    return result
                else:
                    raise HTTPException(status_code=400, detail="No frames could be extracted from the video")

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported media type: {media_mime or 'unknown'}")

    except HTTPException as exc:
        logging.error(f"/verify_media HTTP error: {exc.detail}")
        raise exc
    except Exception as e:
        logging.error(f"/verify_media failed: {e}")
        raise HTTPException(status_code=500, detail=f"Media verification failed: {str(e)}")
        

# --- Alias endpoint for video verification ---
@app.post("/v1/verify_video")
async def verify_video(
    text: str = Form(""),
    mode: str = Form("fast"),
    language: str = Form("en"),
    video: Optional[UploadFile] = File(None),
    privacy: bool = Form(False),
    api_key: str = Depends(verify_api_key)
):
    # Customized to attach deepfake_detection if present
    try:
        result = await verify_media(
            text=text,
            mode=mode,
            language=language,
            file=video,
            privacy=privacy,
            api_key=api_key
        )
        # Attach deepfake_detection from media_forensics if available
        if (
            isinstance(result, dict)
            and "media_forensics" in result
            and isinstance(result["media_forensics"], dict)
            and "deepfake_detection" in result["media_forensics"]
        ):
            result["deepfake_detection"] = result["media_forensics"]["deepfake_detection"]
        elif (
            isinstance(result, dict)
            and "forensics" in result
            and isinstance(result["forensics"], dict)
            and "deepfake_detection" in result["forensics"]
        ):
            result["deepfake_detection"] = result["forensics"]["deepfake_detection"]
        return result
    except Exception as e:
        logging.error(f"verify_video endpoint failed: {e}")
        raise HTTPException(status_code=500, detail="Video verification failed")

# --- URL Verification Endpoints ---
@app.post("/v1/verify_url")
async def verify_url_endpoint(request: dict, api_key: str = Depends(verify_api_key)):
    """
    Verify a URL for safety and manipulation.
    Request JSON: { "url": "..." }
    Response JSON: { "input_type": "url", "timestamp": "...", "webrisk_status": "...", "manipulation_technique": "...", ... }
    """
    url = request.get("url")
    # Normalize URL input for flexibility (handle google.com, www.site.org, etc.)
    if url and isinstance(url, str):
        url = url.strip()
        if not re.match(r"^https?://", url):
            if not url.startswith("www."):
                url = "https://www." + url
            else:
                url = "https://" + url
    if not url or not isinstance(url, str):
        raise HTTPException(status_code=400, detail="Missing or invalid 'url'")
    now = datetime.utcnow().isoformat()
    # Check cache first
    cached = get_cached_link_verification(url)
    if cached:
        cached["cached"] = True
        cached["timestamp"] = now
        # Ensure manipulation fields are present
        if "manipulation_technique" not in cached or "manipulation_explanation" not in cached:
            cached["manipulation_technique"] = None
            cached["manipulation_explanation"] = None
        return cached
    # Run checks with error handling for each stage
    try:
        webrisk = await check_webrisk(url)
    except Exception as e:
        logging.error(f"WebRisk check failed: {e}")
        webrisk = {"webrisk_status": "unknown", "error": str(e)}

    try:
        metadata = await fetch_url_metadata(url)
    except Exception as e:
        logging.error(f"Metadata fetch failed: {e}")
        metadata = {}

    try:
        manipulation = await detect_manipulation_gemini(url, metadata)
    except Exception as e:
        logging.error(f"Manipulation detection failed: {e}")
        manipulation = {"manipulation_technique": "unknown", "explanation": str(e)}

    result = {
        "input_type": "url",
        "timestamp": now,
        "url": url,
        "webrisk_status": webrisk.get("webrisk_status", "unknown"),
        "webrisk_detail": webrisk,
        "metadata": metadata,
        "manipulation_technique": manipulation.get("manipulation_technique"),
        "manipulation_explanation": manipulation.get("explanation"),
    }
    cache_link_verification(url, result)
    return result

@app.post("/v1/scan-link")
async def scan_link_endpoint(request: dict, api_key: str = Depends(verify_api_key)):
    """
    Scan a link for safety, manipulation, and return unified JSON schema.
    Request JSON: { "url": "..." }
    Response JSON: { "input_type": "url", "timestamp": "...", "manipulation_technique": "...", ... }
    """
    url = request.get("url")
    if not url or not isinstance(url, str):
        raise HTTPException(status_code=400, detail="Missing or invalid 'url'")
    now = datetime.utcnow().isoformat()
    cached = get_cached_link_verification(url)
    if cached:
        cached["cached"] = True
        cached["timestamp"] = now
        # Ensure manipulation fields are present
        if "manipulation_technique" not in cached or "manipulation_explanation" not in cached:
            cached["manipulation_technique"] = None
            cached["manipulation_explanation"] = None
        return cached
    webrisk = await check_webrisk(url)
    metadata = await fetch_url_metadata(url)
    manipulation = await detect_manipulation_gemini(url, metadata)
    result = {
        "input_type": "url",
        "timestamp": now,
        "url": url,
        "webrisk_status": webrisk.get("webrisk_status"),
        "webrisk_detail": webrisk,
        "metadata": metadata,
    }
    # Merge manipulation fields as per instructions
    result.update({
        "manipulation_technique": manipulation.get("manipulation_technique"),
        "manipulation_explanation": manipulation.get("explanation")
    })
    cache_link_verification(url, result)
    return result

# Result combination
def combine_results(gemini_result: Dict[str, Any], fact_check_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Combine Gemini and Fact Check results"""
    if not fact_check_result:
        return gemini_result
    
    # If we have fact check results, enhance the Gemini result
    combined = gemini_result.copy()
    
    # Add fact check citations if available
    if fact_check_result.get("citations"):
        combined["citations"] = fact_check_result["citations"]
    
    # Adjust confidence based on fact check results
    if fact_check_result.get("confidence"):
        combined["confidence"] = max(combined.get("confidence", 0), fact_check_result["confidence"])
    
    return combined

# Logging
async def store_logs(request_id: str, text: str, language: str, mode: str, result: Dict[str, Any], start_time: datetime):
    """Store request logs in BigQuery"""
    if bigquery_client is None:
        logging.warning("BigQuery client unavailable; skipping history logging")
        return
    try:
        table = bigquery_client.get_table(f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}")
        
        row = {
            "request_id": request_id,
            "timestamp": start_time.isoformat(),
            "text": text[:1000],  # Truncate for storage
            "language": language,
            "mode": mode,
            "verdict": result.get("verdict", "error"),
            "confidence": result.get("confidence", 0.0),
            "cost": result.get("cost", 0.0),
            "latency_ms": (datetime.utcnow() - start_time).total_seconds() * 1000
        }
        
        errors = bigquery_client.insert_rows_json(table, [row])
        if errors:
            logging.error(f"Failed to insert log row: {errors}")
    except Exception as e:
        logging.error(f"Failed to store logs: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

#
# --- Configuration environment variables ---
#   GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, STORAGE_BUCKET, BIGQUERY_DATASET,
#   BIGQUERY_TABLE, SERPER_API_KEY, SERPER_API_ENDPOINT, WEBRISK_API_KEY,
#   GEMINI_MODEL, GEMINI_MODE, FACT_CHECK_API_KEY, BIGQUERY_AUTO_TABLE
# --- New Endpoints: /v1/history, /v1/trending, /v1/privacy_mode ---

from fastapi.responses import JSONResponse

@app.get("/v1/history")
async def get_history(api_key: str = Depends(verify_api_key)):
    """
    Get last 10 verification requests from BigQuery.
    Returns: { "history": [ ... ] }
    """
    if bigquery_client is None:
        raise HTTPException(status_code=503, detail="BigQuery client unavailable")
    try:
        query = f"""
            SELECT request_id, timestamp, text, verdict, confidence, mode, language
            FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
            ORDER BY timestamp DESC
            LIMIT 10
        """
        rows = bigquery_client.query(query)
        history = []
        for row in rows:
            history.append({
                "request_id": row.get("request_id") if hasattr(row, "get") else row.request_id,
                "timestamp": row.get("timestamp") if hasattr(row, "get") else row.timestamp,
                "text": row.get("text") if hasattr(row, "get") else row.text,
                "verdict": row.get("verdict") if hasattr(row, "get") else row.verdict,
                "confidence": row.get("confidence") if hasattr(row, "get") else row.confidence,
                "mode": row.get("mode") if hasattr(row, "get") else row.mode,
                "language": row.get("language") if hasattr(row, "get") else row.language,
            })
        return {"history": history}
    except Exception as e:
        logging.error(f"Failed to fetch history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch history")


@app.get("/v1/trending")
async def get_trending(api_key: str = Depends(verify_api_key)):
    """
    Get top 10 most frequent claims (text) from last 48 hours.
    Returns: { "trending": [ ... ] }
    """
    if bigquery_client is None:
        raise HTTPException(status_code=503, detail="BigQuery client unavailable")
    try:
        since = (datetime.utcnow() - timedelta(hours=48)).isoformat()
        query = f"""
            SELECT text, COUNT(*) as count, MAX(timestamp) as last_seen
            FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
            WHERE timestamp >= '{since}'
            GROUP BY text
            ORDER BY count DESC, last_seen DESC
            LIMIT 10
        """
        rows = bigquery_client.query(query)
        trending = []
        for row in rows:
            trending.append({
                "text": row.get("text") if hasattr(row, "get") else row.text,
                "count": row.get("count") if hasattr(row, "get") else row.count,
                "last_seen": row.get("last_seen") if hasattr(row, "get") else row.last_seen,
            })
        return {"trending": trending}
    except Exception as e:
        logging.error(f"Failed to fetch trending: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch trending")


# --- Auto Trending (Headlines) helpers ---

AUTO_TABLE_ID = os.getenv("BIGQUERY_AUTO_TABLE", "auto_verifications")

def get_auto_table_fqn() -> str:
    """Fully-qualified table name for auto verifications."""
    return f"{PROJECT_ID}.{DATASET_ID}.{AUTO_TABLE_ID}"

async def save_auto_verification_row(row: Dict[str, Any]) -> None:
    """Insert one auto-verification row into BigQuery."""
    if bigquery_client is None:
        logging.warning("BigQuery client unavailable; skipping auto verification persistence")
        return
    try:
        table_fqn = get_auto_table_fqn()
        # Ensure string types for large fields
        payload = [{
            "request_id": row.get("request_id"),
            "timestamp": row.get("timestamp"),
            "text": (row.get("text") or "")[:2000],
            "verdict": row.get("verdict") or "unknown",
            "confidence": float(row.get("confidence") or 0.0),
            "explanation": (row.get("explanation") or "")[:5000],
            "sources": json.dumps(row.get("sources") or [], ensure_ascii=False),
            "language": row.get("language") or "en"
        }]
        errors = bigquery_client.insert_rows_json(table_fqn, payload)
        if errors:
            logging.error(f"BigQuery insert errors (auto_verifications): {errors}")
    except Exception as e:
        logging.error(f"Failed to save auto verification row: {e}")

async def verify_headline_text(headline: str, lang_hint: str = "en") -> Dict[str, Any]:
    """
    Run the same verification pipeline for a text-only headline.
    Returns a compact dict suitable for storage in auto_verifications.
    """
    try:
        language = lang_hint or "en"
        if language == "auto":
            language = detect_language(headline or "")
        # Retrieve evidence
        bundle = await retrieve_supporting_evidence(headline, language)
        citations_raw = bundle.get("citations", [])
        fact_check_raw = bundle.get("fact_check_results", [])
        evidence_entries: List[Dict[str, Any]] = []
        for item in citations_raw[:5]:
            evidence_entries.append({
                "title": item.get("title", ""),
                "snippet": item.get("snippet") or item.get("rating", ""),
                "url": item.get("url", ""),
                "source": item.get("source") or item.get("publisher", ""),
            })
        # Normalize fact-checks
        normalized_fact_checks: List[Dict[str, Any]] = []
        for claim in fact_check_raw:
            claim_text_fc = claim.get("text", "")
            for review in claim.get("claimReview", []):
                reviewer = review.get("publisher", {})
                reviewer_name = reviewer.get("name", "") if isinstance(reviewer, dict) else (reviewer or "")
                normalized_fact_checks.append({
                    "claim": claim_text_fc or review.get("title", ""),
                    "reviewer": reviewer_name,
                    "url": review.get("url", ""),
                    "rating": review.get("textualRating", ""),
                })
        # Call Gemini
        gemini_out = await verify_with_gemini(
            claim_text=headline,
            language=language,
            evidence=evidence_entries,
            fact_check_results=normalized_fact_checks,
            image_bytes=None,
            image_mime="image/jpeg",
            video_context=None,
        )
        # Normalize citations
        citations: List[Dict[str, Any]] = []
        for entry in gemini_out.get("citations") or []:
            if isinstance(entry, dict):
                citations.append({
                    "title": entry.get("title") or entry.get("url") or "Source",
                    "url": entry.get("url", ""),
                    "source": entry.get("source", entry.get("publisher", "")),
                })
            elif isinstance(entry, str):
                citations.append({"title": entry, "url": entry, "source": ""})
        return {
            "verdict": (gemini_out.get("verdict") or "unknown").lower(),
            "confidence": float(gemini_out.get("confidence") or 0.0),
            "explanation": gemini_out.get("explanation") or "",
            "sources": citations or evidence_entries,
            "language": language,
        }
    except Exception as e:
        logging.error(f"verify_headline_text failed: {e}")
        return {
            "verdict": "error",
            "confidence": 0.0,
            "explanation": "verification failed",
            "sources": [],
            "language": lang_hint or "en",
        }

async def fetch_recent_headlines(limit: int = 12, hl: str = "en") -> List[str]:
    """
    Use Serper News API to fetch recent headlines to verify automatically.
    """
    if not SERPER_API_KEY:
        logging.warning("SERPER_API_KEY not set; auto scan will do nothing.")
        return []
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": "*", "num": max(1, min(limit, 20)), "hl": hl}
    try:
        resp = requests.post(SERPER_API_ENDPOINT, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        headlines = []
        for item in data.get("news", [])[:limit]:
            title = item.get("title") or ""
            # Basic cleanup
            title = re.sub(r"\s+", " ", title).strip()
            if title:
                headlines.append(title)
        return headlines
    except Exception as exc:
        logging.error(f"fetch_recent_headlines failed: {exc}")
        return []

async def run_auto_scan(limit: int = 12, lang: str = "en") -> Dict[str, Any]:
    """
    Fetch recent headlines and verify them, store into BigQuery.
    Returns summary counts.
    """
    request_ts = datetime.utcnow().isoformat()
    headlines = await fetch_recent_headlines(limit=limit, hl=lang)
    total = 0
    stored = 0
    results: List[Dict[str, Any]] = []
    for h in headlines:
        total += 1
        rid = str(uuid.uuid4())
        out = await verify_headline_text(h, lang_hint=lang)
        row = {
            "request_id": rid,
            "timestamp": request_ts,
            "text": h,
            "verdict": out["verdict"],
            "confidence": out["confidence"],
            "explanation": out["explanation"],
            "sources": out["sources"],
            "language": out["language"],
        }
        await save_auto_verification_row(row)
        stored += 1
        # Only return lightweight preview to caller
        results.append({
            "request_id": rid,
            "text": h,
            "verdict": out["verdict"],
            "confidence": out["confidence"],
        })
    return {"scanned": total, "stored": stored, "results": results}
@app.post("/v1/auto_scan")
async def auto_scan_endpoint(
    request: Dict[str, Any] = None,
    api_key: str = Depends(verify_api_key)
):
    """
    Manually trigger an auto scan of recent headlines.
    Body JSON (optional): { "limit": 12, "language": "en" }
    """
    req = request or {}
    limit = int(req.get("limit", 12)) if isinstance(req, dict) else 12
    language = (req.get("language") if isinstance(req, dict) else "en") or "en"
    summary = await run_auto_scan(limit=limit, lang=language)
    return {"ok": True, "summary": summary}


@app.get("/v1/auto_trending")
async def auto_trending_endpoint(api_key: str = Depends(verify_api_key)):
    """
    Return recent auto-verified items that are likely misinformation.
    Filters verdict in ('false','misleading') in the last 72 hours.
    """
    if bigquery_client is None:
        raise HTTPException(status_code=503, detail="BigQuery client unavailable")
    try:
        table_fqn = get_auto_table_fqn()
        since = (datetime.utcnow() - timedelta(hours=72)).isoformat()
        query = f"""
            SELECT request_id, timestamp, text, verdict, confidence, language
            FROM `{table_fqn}`
            WHERE timestamp >= '{since}'
              AND LOWER(verdict) IN ('false','misleading')
            ORDER BY timestamp DESC
            LIMIT 20
        """
        rows = bigquery_client.query(query)
        items: List[Dict[str, Any]] = []
        for row in rows:
            items.append({
                "request_id": getattr(row, "request_id", None),
                "timestamp": getattr(row, "timestamp", None),
                "text": getattr(row, "text", ""),
                "verdict": getattr(row, "verdict", "unknown"),
                "confidence": float(getattr(row, "confidence", 0.0) or 0.0),
                "language": getattr(row, "language", "en"),
            })
        return {"items": items}
    except Exception as e:
        logging.error(f"auto_trending query failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to load auto trending")




@app.post("/v1/privacy_mode")
async def set_privacy_mode(privacy: bool = Form(...)):
    """
    Set or unset privacy mode for the API (global variable).
    Accepts form-data with 'privacy' boolean.
    Returns: { "privacy_mode": true/false }
    """
    global PRIVACY_MODE
    PRIVACY_MODE = bool(privacy)
    return {"privacy_mode": PRIVACY_MODE}

# --- Entry point for Cloud Run ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
