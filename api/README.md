# TruthLens API Documentation

## Overview
TruthLens is an AI-powered multimedia verification API designed to detect misinformation across **text, images, and videos**.  
It combines **Google Vertex AI Gemini**, **Google Cloud Vision**, and **Serper Search APIs** for fact extraction, manipulation detection, and authenticity verification.

## Architecture
- **Backend**: FastAPI + Uvicorn (Python)
- **Deployment**: Google Cloud Run
- **Storage & Logs**: Google Cloud Storage + Cloud Logging
- **ML Stack**: Vertex AI Gemini, Google Vision API
- **Search Integration**: Serper API (Google Search)
- **Cache Layer**: Redis / Cloud Memorystore
- **Database**: Firestore / BigQuery (for metrics and trending tracking)
- **App Integration**: Android (Jetpack Compose)

---

## Base URL
- **Production**: `https://truthlens-api-276376440888.us-central1.run.app`
- **Development**: `http://localhost:8080`

---

## Authentication
All API requests require a Bearer token:
```bash
Authorization: Bearer your-api-key
```

---

## Endpoints

### Health Check
**GET** `/healthz`
```json
{
  "status": "healthy",
  "timestamp": "2025-11-01T00:00:00Z"
}
```

---

### Verify Claim
Verifies text or image-based claims using AI + factual databases.

**POST** `/v1/verify`

**Request (multipart/form-data):**
- `text` *(optional)*: Claim or statement to verify
- `image` *(optional)*: Image file for forensic + factual verification
- `language` *(optional)*: Default `"en"`
- `mode` *(optional)*: `"fast"` (Gemini only) or `"deep"` (Gemini + Serper + Vision)

**Response:**
```json
{
  "verdict": "true|false|misleading|unverifiable",
  "confidence": 0.95,
  "explanation": "Gemini + Serper + Vision reasoning summary",
  "key_facts": ["Fact 1", "Fact 2"],
  "citations": [{"title": "Source Title", "url": "https://example.com"}],
  "manipulation_technique": "deepfake|photoshop|ai-generated|none",
  "manipulation_explanation": "Detailed forensic analysis",
  "timestamp": "2025-11-02T09:30:00Z",
  "metrics": {"latency_ms": 2100, "cost_usd": 0.003}
}
```

---

### Verify Media
Performs **video-level verification** using Gemini + Serper + Vision + Deepfake Forensics.

**POST** `/v1/verify_media`

**Request:**
- `file` *(required)*: Video file
- `language`, `mode` *(optional)*

**Response:**
```json
{
  "verdict": "true|false|misleading|unverifiable",
  "confidence": 0.92,
  "explanation": "Multiframe forensic analysis summary",
  "media_forensics": {
    "fps": 24,
    "duration_sec": 7.8,
    "frame_count": 187,
    "deepfake_detection": {
      "detected": false,
      "confidence": 0.0,
      "explanation": "No deepfake traces found"
    }
  },
  "citations": [{"title": "CNN", "url": "https://cnn.com"}],
  "timestamp": "2025-11-02T09:40:00Z"
}
```

---

### Feedback
Stores user feedback for model improvement.

**POST** `/v1/feedback`
```json
{
  "request_id": "uuid",
  "feedback": "upvote|downvote",
  "comment": "optional text"
}
```
**Response:**
```json
{"message": "Feedback recorded successfully"}
```

---

## Caching & Trending
- Responses are cached for repeated requests (up to 24 hours)
- Trending claims are recorded and retrievable via `/v1/trending`

---

## Verification Pipeline

| Stage | Description |
|--------|--------------|
| **1. Input Parsing** | Accepts text/image/video inputs |
| **2. Gemini Reasoning** | Generates contextual explanation |
| **3. Serper Search** | Retrieves fact-check sources |
| **4. Vision Analysis** | Detects visual manipulation, objects, faces, OCR |
| **5. Deepfake Detector** | Flags suspicious frame-level anomalies |
| **6. Result Fusion** | Aggregates Gemini + Forensic + Search into unified verdict |
| **7. Caching & Storage** | Saves to Cloud Memorystore / Firestore |

---

## Example Usage

### cURL
```bash
curl -X POST "https://truthlens-api-276376440888.us-central1.run.app/v1/verify" \
  -H "Authorization: Bearer your-api-key" \
  -F "text=Is Gukesh the current world chess champion?" \
  -F "language=en" \
  -F "mode=fast"
```

### Video Verification
```bash
curl -X POST "https://truthlens-api-276376440888.us-central1.run.app/v1/verify_media" \
  -H "Authorization: Bearer your-api-key" \
  -F "file=@sample.mp4;type=video/mp4"
```

---

## Cost & Performance
| Mode | Avg Latency | Cost (USD) | Description |
|------|--------------|-------------|--------------|
| Fast | ~3s | $0.001 | Gemini-based reasoning |
| Deep | ~7s | $0.003 | Gemini + Serper + Vision |
| Media | ~10-20s | $0.005 | Deepfake & frame-level forensics |

---

## Contact
For API support and technical assistance:
- **Email**: support@truthlens.app
- **Docs**: https://docs.truthlens.app
- **Status**: https://status.truthlens.app

---
