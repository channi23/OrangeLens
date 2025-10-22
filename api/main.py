import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.cloud import aiplatform
from google.cloud import storage
from google.cloud import bigquery
from google.cloud import secretmanager
from vertexai.preview.generative_models import GenerativeModel, Part
from google.api_core.exceptions import InvalidArgument
import vertexai
import requests
import hashlib
import uuid
import re
from PIL import Image
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    logging.warning("pillow-heif not available, HEIF/HEIC images will not be supported.")
import pytesseract
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor

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
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
SERPER_API_ENDPOINT = os.getenv("SERPER_API_ENDPOINT", "https://google.serper.dev/news")
WEBRISK_API_KEY = os.getenv("WEBRISK_API_KEY", "")
WEBRISK_API_URL = "https://webrisk.googleapis.com/v1/uris:search"

os.environ["GOOGLE_CLOUD_AI_PLATFORM_API_VERSION"] = "v1beta"
vertexai.init(project=PROJECT_ID, location=LOCATION)
try:
    logging.error(f"Startup config: PROJECT_ID={PROJECT_ID}, LOCATION={LOCATION}")
except Exception:
    pass
storage_client = storage.Client()
bigquery_client = bigquery.Client()
secret_client = secretmanager.SecretManagerServiceClient()
executor = ThreadPoolExecutor(max_workers=4)
# --- Link Verification Helpers ---

# --- Claim Verification Cache Helpers (Unified cache_key approach) ---
def get_claim_cache_table():
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

def get_cached_verification(cache_key: str) -> Optional[dict]:
    """Retrieve cached verification result from BigQuery using unified cache_key (30-day TTL)."""
    try:
        _, table_name = get_claim_cache_table()
        query = f"""
            SELECT data FROM `{table_name}`
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
            return json.loads(rows[0]["data"])
    except Exception as e:
        logging.error(f"BigQuery verification cache lookup failed: {e}")
    return None

def cache_verification(cache_key: str, data: dict, text: str):
    """Cache new verification result in BigQuery using unified cache_key."""
    try:
        _, table_name = get_claim_cache_table()
        row = {
            "cache_key": cache_key,
            "text": text[:1000],
            "verdict": data.get("verdict", "unknown"),
            "confidence": float(data.get("confidence", 0.0)),
            "explanation": data.get("explanation", "")[:2000],
            "citations": json.dumps(data.get("citations", [])),
            "timestamp": datetime.utcnow().isoformat(),
            "data": json.dumps(data)
        }
        errors = bigquery_client.insert_rows_json(table_name, [row])
        if errors:
            logging.error(f"BigQuery cache insert errors: {errors}")
    except Exception as e:
        logging.error(f"BigQuery cache insert failed: {e}")
def get_url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()

def get_link_cache_table():
    table_name = f"{PROJECT_ID}.{DATASET_ID}.link_verification_cache"
    return bigquery_client.dataset(DATASET_ID).table("link_verification_cache"), table_name

def cache_link_verification(url: str, data: dict):
    """Cache link verification result in BigQuery"""
    try:
        _, table_name = get_link_cache_table()
        row = {
            "url_hash": get_url_hash(url),
            "url": url,
            "data": json.dumps(data),
            "timestamp": datetime.utcnow().isoformat()
        }
        errors = bigquery_client.insert_rows_json(table_name, [row])
        if errors:
            logging.error(f"BigQuery link cache insert errors: {errors}")
    except Exception as e:
        logging.error(f"BigQuery link cache failed: {e}")

def get_cached_link_verification(url: str) -> Optional[dict]:
    """Retrieve cached link verification result from BigQuery"""
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
        params = {"uri": url, "key": WEBRISK_API_KEY}
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
Headers: {json.dumps(metadata.get('headers',{}))}
"""

async def detect_manipulation_gemini(url: str, metadata: dict) -> dict:
    """Call Gemini to detect manipulation technique for a URL."""
    model = GenerativeModel(GEMINI_MODEL)
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
    """Get secret from Secret Manager"""
    try:
        name = f"projects/{PROJECT_ID}/secrets/{secret_name}/versions/latest"
        response = secret_client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logging.error(f"Failed to get secret {secret_name}: {e}")
        return ""


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
        model = GenerativeModel(GEMINI_MODEL)
        prompt = f"Clean and refine the following OCR text into a single clear factual claim for fact-checking. If not possible, return it unchanged.\n\nText: {raw_text}"
        response = model.generate_content([Part.from_text(prompt)])
        return (response.text or raw_text).strip()
    except Exception as e:
        logging.error(f"Refinement failed: {e}")
        return raw_text


async def upload_image_to_bucket(image_bytes: bytes, mime_type: str, request_id: str) -> Optional[Dict[str, str]]:
    if not image_bytes:
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
    model = GenerativeModel(GEMINI_MODEL)
    caption_prompt = {
        "en": "Describe the image in one neutral sentence so it can be fact checked.",
        "hi": "तथ्य जांच के लिए छवि का एक निष्पक्ष वाक्य में वर्णन करें।",
        "ta": "தகவலை சரிபார்க்க பயன்படுத்த படத்தை ஒரு குறுகிய நடுநிலை வாக்கியமாக விளக்கவும்.",
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
    if not SERPER_API_KEY or not query:
        return []
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query, "num": 5, "hl": language or "en"}
    try:
        resp = requests.post(SERPER_API_ENDPOINT, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logging.error(f"News search failed: {exc}")
        return []

    entries: List[Dict[str, Any]] = []
    for item in data.get("news", [])[:5]:
        entries.append({
            "title": item.get("title", ""),
            "snippet": item.get("snippet", item.get("description", "")),
            "url": item.get("link") or item.get("sourceUrl", ""),
            "source": item.get("source", ""),
        })
    return entries


async def retrieve_supporting_evidence(claim_text: str, language: str) -> Dict[str, Any]:
    fact_data = await check_fact_check_api(claim_text, language)
    citations = fact_data.get("citations", [])
    fact_check_results = fact_data.get("fact_check_results", [])

    evidence_entries: List[Dict[str, Any]] = []
    for item in citations[:5]:
        evidence_entries.append({
            "title": item.get("title", ""),
            "snippet": item.get("rating", ""),
            "url": item.get("url", ""),
            "source": item.get("publisher", ""),
        })

    if not evidence_entries:
        fallback_entries = await search_news_fallback(claim_text, language)
        evidence_entries.extend(fallback_entries)
    else:
        fallback_entries = []

    return {
        "evidence": evidence_entries,
        "citations": citations or fallback_entries,
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
        if not claim_text:
            # First try OCR extraction
            ocr_text = extract_text_from_image_bytes(image_bytes)
            if ocr_text:
                # Refine with Gemini
                claim_text = await refine_text_with_gemini(ocr_text, language)
            else:
                # Use raw bytes for caption generation (not the URL)
                caption = await generate_image_caption(image_bytes, language, image_mime)
                caption = caption.strip()

                if caption:
                    # Refine the caption into a clearer factual claim
                    claim_text = await refine_text_with_gemini(caption, language)
                else:
                    claim_text = "Image-only verification requested."

    if not claim_text:
        raise HTTPException(status_code=400, detail="Unable to determine claim text from request")

    evidence_bundle = await retrieve_supporting_evidence(claim_text, language)
    evidence_entries = evidence_bundle.get("evidence", [])
    citations_raw = evidence_bundle.get("citations", [])
    fact_check_raw = evidence_bundle.get("fact_check_results", [])

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

    gemini_result = await verify_with_gemini(
        claim_text,
        language,
        evidence_entries,
        normalized_fact_checks,
        image_bytes=image_bytes,
        image_mime=image_mime,
    )

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
        model = GenerativeModel(GEMINI_MODEL)
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

# API Key validation
async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key"""
    api_key = get_secret("truthlens-api-key")
    if not api_key or credentials.credentials != api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials

# Language detection
def detect_language(text: str) -> str:
    """Simple language detection"""
    # Basic language detection - can be enhanced with Google Translate API
    if any(char in text for char in "अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह"):
        return "hi"  # Hindi
    elif any(char in text for char in "அஆஇஈஉஊஎஏஐஒஓஔகஙசஜஞடணதநபமயரலவஶஷஸஹ"):
        return "ta"  # Tamil
    else:
        return "en"  # English

# Gemini AI integration
# Allow overriding the model via environment variable
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
GEMINI_MODE = os.getenv("GEMINI_MODE", "vertex")  # vertex recommended (supports text+image)
try:
    logging.info(f"✅ Using Gemini model: {GEMINI_MODEL} (mode={GEMINI_MODE})")
except Exception:
    pass

async def verify_with_gemini(
    claim_text: str,
    language: str,
    evidence: List[Dict[str, Any]],
    fact_check_results: List[Dict[str, Any]],
    image_bytes: Optional[bytes] = None,
    image_mime: str = "image/jpeg",
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

        current_year = datetime.utcnow().year
        prompt = f"""
You are TruthLens, an evidence-driven fact-checking assistant designed to analyze both text and visual information.

Your task:
- Examine the claim, the evidence, and (if provided) the image.
- If an image is included, prioritize its visual context and verify whether the image supports, contradicts, or misleads regarding the claim.
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

Image context:
- If an image is attached, interpret its visual elements (text, symbols, people, or scenes) in relation to the claim.
- Determine if the image is authentic, unrelated, or possibly manipulated.
- If no image is provided, ignore this instruction.

Rules:
- If the claim references a future year beyond {current_year}, set verdict to "unverifiable" with low confidence and explain why.
- If no direct evidence exists, reason using historical and factual context.
- Keep explanations concise and directly related to the claim and any attached image.
"""

        model = GenerativeModel(GEMINI_MODEL)
        generation_parts: List[Any] = [Part.from_text(prompt)]
        if image_bytes:
            generation_parts.append(Part.from_data(data=image_bytes, mime_type=image_mime or "image/jpeg"))
        # Explicit logging before sending parts to Gemini
        logging.error(f"Gemini input parts: {[type(p).__name__ for p in generation_parts]}")
        try:
            response = model.generate_content(generation_parts)
        except InvalidArgument as exc:
            logging.error(f"Gemini verification rejected input: {exc}")
            raise HTTPException(status_code=400, detail="Gemini could not process the supplied media.")
        except Exception as exc:
            logging.error(f"Gemini verification failed: {exc}")
            raise HTTPException(status_code=500, detail="AI verification failed")

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
        logging.error(f"Gemini verification failed: {e}")
        raise HTTPException(status_code=500, detail="AI verification failed")

# Google Fact Check API integration
async def check_fact_check_api(text: str, language: str = "en") -> Dict[str, Any]:
    """Check against Google Fact Check API"""
    try:
        # Map language codes
        lang_map = {"en": "en", "hi": "hi", "ta": "ta"}
        query_lang = lang_map.get(language, "en")

        url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
        # URL encode the query for safety
        safe_text = quote(text, safe="")
        params = {
            "query": safe_text,
            "languageCode": query_lang,
            "pageSize": 5
        }

        # Use API key from environment (preferred for local) or Secret Manager
        api_key = os.getenv("FACT_CHECK_API_KEY") or get_secret("fact-check-api-key")
        if not api_key:
            return {"citations": [], "fact_check_results": []}

        headers = {"X-Goog-Api-Key": api_key, "Content-Type": "application/json; charset=utf-8"}

        response = requests.get(url, params=params, headers=headers)
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
            "fact_check_results": data.get("claims", [])
        }

    except Exception as e:
        logging.error(f"Fact Check API failed: {e}")
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
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        
        # Store image if provided
        if image_data and not existing_image_uri:
            image_blob = bucket.blob(f"images/{request_id}{_guess_extension(image_mime)}")
            image_blob.upload_from_string(image_data, content_type=image_mime or "image/jpeg")
        
        # Store response
        response_blob = bucket.blob(f"responses/{request_id}.json")
        response_blob.upload_from_string(
            json.dumps(response_data, indent=2),
            content_type="application/json"
        )
        
    except Exception as e:
        logging.error(f"Storage operation failed: {e}")

# BigQuery logging
async def log_request(request_id: str, text: str, mode: str, language: str,
                     verdict: str, confidence: float, latency: float, cost: float):
    """Log request to BigQuery"""
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
                model = GenerativeModel(GEMINI_MODEL)
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
        logging.error(f"/verify-test failed: {e}")
        return {"request_id": request_id, "error": "Verification failed", "verdict": "error"}

@app.post("/v1/verify")
async def verify_claim(
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
                model = GenerativeModel(GEMINI_MODEL)
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
            store_evidence(request_id, image_data, final_result, existing_image_uri=bundle.get("image_uri"), image_mime=image_mime) if not local_privacy_mode else asyncio.sleep(0),
            log_request(request_id, text_value, mode, language,
                       final_result["verdict"], final_result["confidence"],
                       latency, cost)
        )

        final_result["metrics"] = {
            "latency_ms": latency,
            "cost_usd": cost
        }
        return final_result
    except Exception as e:
        logging.error(f"Verification failed for request {request_id}: {e}")
        raise HTTPException(status_code=500, detail="Verification failed")
    finally:
        # Restore previous privacy mode to avoid leaking state between requests
        PRIVACY_MODE = prev_privacy_mode

# --- URL Verification Endpoints ---
@app.post("/v1/verify_url")
async def verify_url_endpoint(request: dict, api_key: str = Depends(verify_api_key)):
    """
    Verify a URL for safety and manipulation.
    Request JSON: { "url": "..." }
    Response JSON: { "input_type": "url", "timestamp": "...", "webrisk_status": "...", "manipulation_technique": "...", ... }
    """
    url = request.get("url")
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
    # Run checks
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
            "sources": json.dumps(row.get("sources") or []),
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
        evidence_entries = bundle.get("evidence", [])
        fact_check_raw = bundle.get("fact_check_results", [])
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


from fastapi import Form

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