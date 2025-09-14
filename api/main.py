import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.cloud import aiplatform
from google.cloud import storage
from google.cloud import bigquery
from google.cloud import secretmanager
import vertexai
from vertexai.generative_models import GenerativeModel
import requests
import hashlib
import uuid

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
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "truthlens-project")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
BUCKET_NAME = os.getenv("STORAGE_BUCKET", "truthlens-evidence")
DATASET_ID = os.getenv("BIGQUERY_DATASET", "truthlens_logs")
TABLE_ID = os.getenv("BIGQUERY_TABLE", "verification_requests")

# Initialize clients
vertexai.init(project=PROJECT_ID, location=LOCATION)
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
async def verify_with_gemini(text: str, image_data: Optional[bytes] = None, language: str = "en") -> Dict[str, Any]:
    """Verify claim using Vertex AI Gemini"""
    try:
        model = GenerativeModel("gemini-1.5-flash")
        
        # Construct prompt based on language
        prompts = {
            "en": f"""
            Analyze the following claim for factual accuracy and provide a JSON response:
            
            Claim: "{text}"
            
            Respond with a JSON object containing:
            - verdict: "true", "false", "misleading", or "unverified"
            - confidence: float between 0.0 and 1.0
            - explanation: detailed explanation of your reasoning
            - key_facts: array of key facts you identified
            - reasoning: step-by-step analysis
            
            Be objective, cite specific evidence, and explain your confidence level.
            """,
            "hi": f"""
            निम्नलिखित दावे का तथ्यात्मक सटीकता के लिए विश्लेषण करें और JSON प्रतिक्रिया दें:
            
            दावा: "{text}"
            
            JSON ऑब्जेक्ट के साथ प्रतिक्रिया दें जिसमें शामिल है:
            - verdict: "true", "false", "misleading", या "unverified"
            - confidence: 0.0 और 1.0 के बीच float
            - explanation: आपके तर्क की विस्तृत व्याख्या
            - key_facts: आपके द्वारा पहचाने गए मुख्य तथ्यों की सरणी
            - reasoning: चरण-दर-चरण विश्लेषण
            
            वस्तुनिष्ठ रहें, विशिष्ट साक्ष्य का हवाला दें, और अपने आत्मविश्वास स्तर की व्याख्या करें।
            """,
            "ta": f"""
            பின்வரும் கூற்றின் உண்மைத் துல்லியத்தை பகுப்பாய்வு செய்து JSON பதிலை வழங்கவும்:
            
            கூற்று: "{text}"
            
            JSON பொருளுடன் பதிலளிக்கவும்:
            - verdict: "true", "false", "misleading", அல்லது "unverified"
            - confidence: 0.0 மற்றும் 1.0 க்கு இடையே float
            - explanation: உங்கள் பகுத்தறிவின் விரிவான விளக்கம்
            - key_facts: நீங்கள் அடையாளம் கண்ட முக்கிய உண்மைகளின் வரிசை
            - reasoning: படிப்படியான பகுப்பாய்வு
            
            புறநிலையாக இருங்கள், குறிப்பிட்ட ஆதாரங்களை மேற்கோள் காட்டுங்கள், மற்றும் உங்கள் நம்பிக்கை நிலையை விளக்குங்கள்।
            """
        }
        
        prompt = prompts.get(language, prompts["en"])
        
        # Prepare content
        content = [prompt]
        if image_data:
            content.append({
                "mime_type": "image/jpeg",
                "data": image_data
            })
        
        # Generate response
        response = model.generate_content(content)
        
        # Parse JSON response
        try:
            result = json.loads(response.text)
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "verdict": "unverified",
                "confidence": 0.5,
                "explanation": response.text,
                "key_facts": [],
                "reasoning": "AI response could not be parsed as JSON"
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
        params = {
            "query": text,
            "languageCode": query_lang,
            "pageSize": 5
        }
        
        # Use API key from Secret Manager
        api_key = get_secret("fact-check-api-key")
        if not api_key:
            return {"citations": [], "fact_check_results": []}
        
        headers = {"X-Goog-Api-Key": api_key}
        
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
async def store_evidence(request_id: str, image_data: Optional[bytes], response_data: Dict[str, Any]):
    """Store evidence in Cloud Storage"""
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        
        # Store image if provided
        if image_data:
            image_blob = bucket.blob(f"images/{request_id}.jpg")
            image_blob.upload_from_string(image_data, content_type="image/jpeg")
        
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

@app.post("/v1/verify")
async def verify_claim(
    text: str = Form(...),
    mode: str = Form("fast"),
    language: str = Form("en"),
    image: Optional[UploadFile] = File(None),
    api_key: str = Depends(verify_api_key)
):
    """Main verification endpoint"""
    start_time = datetime.utcnow()
    request_id = str(uuid.uuid4())
    
    try:
        # Input preprocessing
        detected_lang = detect_language(text)
        if language == "auto":
            language = detected_lang
        
        # Read image data if provided
        image_data = None
        if image:
            image_data = await image.read()
        
        # Step 1: Gemini AI verification
        gemini_result = await verify_with_gemini(text, image_data, language)
        
        # Step 2: Fact Check API (if confidence < 75% or mode is deep)
        citations = []
        fact_check_results = []
        
        if mode == "deep" or gemini_result.get("confidence", 0) < 0.75:
            fact_check_data = await check_fact_check_api(text, language)
            citations = fact_check_data.get("citations", [])
            fact_check_results = fact_check_data.get("fact_check_results", [])
        
        # Step 3: Combine results
        final_result = {
            "request_id": request_id,
            "verdict": gemini_result.get("verdict", "unverified"),
            "confidence": gemini_result.get("confidence", 0.5),
            "explanation": gemini_result.get("explanation", ""),
            "key_facts": gemini_result.get("key_facts", []),
            "reasoning": gemini_result.get("reasoning", ""),
            "citations": citations,
            "fact_check_results": fact_check_results,
            "language": language,
            "mode": mode,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Calculate metrics
        latency = (datetime.utcnow() - start_time).total_seconds() * 1000
        cost = calculate_cost(mode, len(text), image_data is not None)
        
        # Store evidence and log request
        await asyncio.gather(
            store_evidence(request_id, image_data, final_result),
            log_request(request_id, text, mode, language, 
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
