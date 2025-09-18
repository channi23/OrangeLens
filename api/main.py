import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
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

# Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "orange-lens-472108")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
BUCKET_NAME = os.getenv("STORAGE_BUCKET", "truthlens-evidence-orange-lens-472108")
DATASET_ID = os.getenv("BIGQUERY_DATASET", "truthlens_logs")
TABLE_ID = os.getenv("BIGQUERY_TABLE", "verification_requests")
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
SERPER_API_ENDPOINT = os.getenv("SERPER_API_ENDPOINT", "https://google.serper.dev/news")

# Initialize clients
# Set API version to beta for Gemini 1.5 models (Vertex path kept for backwards compatibility)
os.environ["GOOGLE_CLOUD_AI_PLATFORM_API_VERSION"] = "v1beta"
vertexai.init(project=PROJECT_ID, location=LOCATION)
try:
    logging.error(f"Startup config: PROJECT_ID={PROJECT_ID}, LOCATION={LOCATION}")
except Exception:
    pass
storage_client = storage.Client()
bigquery_client = bigquery.Client()
secret_client = secretmanager.SecretManagerServiceClient()

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
                caption = await generate_image_caption(image_uri, language)
                claim_text = caption.strip() or "Image-only verification requested."

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
You are TruthLens, an evidence-driven fact checking assistant.
Analyze the claim and the provided evidence. Respond ONLY with JSON matching this schema:
{{
  "verdict": "true | false | misleading | unknown",
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

Rules:
- If the claim references a year greater than {current_year}, set verdict to "unknown" with low confidence and explain it refers to a future event.
- If no direct evidence is available, analyze plausibility using historical knowledge up to {current_year}.
- Use only the evidence provided or well-established knowledge.
- Include reasoning in the explanation even when evidence is missing.
- Include relevant URLs in the citations array when available.
- Keep the explanation clear and concise.
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
        
        row = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "text": text[:1000],  # Truncate long text
            "mode": mode,
            "language": language,
            "verdict": verdict,
            "confidence": confidence,
            "latency_ms": latency,
            "cost_usd": cost,
            "user_hash": hashlib.sha256(text.encode()).hexdigest()[:16]  # Anonymized user ID
        }
        
        errors = bigquery_client.insert_rows_json(table, [row])
        if errors:
            logging.error(f"BigQuery insert errors: {errors}")
            
    except Exception as e:
        logging.error(f"BigQuery logging failed: {e}")

# API Endpoints
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
    api_key: str = Depends(verify_api_key)
):
    """Main verification endpoint. Accepts optional text and image."""
    start_time = datetime.utcnow()
    request_id = str(uuid.uuid4())

    try:
        # Input preprocessing
        # If text is None or missing, set to empty string
        text_value = text if text is not None else ""
        detected_lang = detect_language(text_value)
        if language == "auto":
            language = detected_lang

        image_data = None
        image_mime = "image/jpeg"
        if image:
            if getattr(image, "content_type", None):
                image_mime = image.content_type or image_mime
            image_data = await image.read()

        bundle = await process_verification_request(
            request_id=request_id,
            text=text_value,
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

        # Calculate metrics
        latency = (datetime.utcnow() - start_time).total_seconds() * 1000
        cost = calculate_cost(mode, len(text_value), image_data is not None)

        # Store evidence and log request
        await asyncio.gather(
            store_evidence(request_id, image_data, final_result, existing_image_uri=bundle.get("image_uri"), image_mime=image_mime),
            log_request(request_id, text_value, mode, language,
                       final_result["verdict"], final_result["confidence"],
                       latency, cost)
        )

        # Add metrics to response
        final_result["metrics"] = {
            "latency_ms": latency,
            "cost_usd": cost
        }

        return final_result

    except Exception as e:
        logging.error(f"Verification failed for request {request_id}: {e}")
        raise HTTPException(status_code=500, detail="Verification failed")

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
