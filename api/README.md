# TruthLens API Documentation

## Overview
The TruthLens API provides AI-powered fact verification using Google Cloud's Vertex AI Gemini and Google Fact Check API.

## Base URL
- **Production**: `https://truthlens-api-gateway-{gateway-id}-uc.a.run.app`
- **Development**: `http://localhost:8080`

## Authentication
All API requests require authentication using a Bearer token in the Authorization header:

```bash
Authorization: Bearer your-api-key
```

## Endpoints

### Health Check
Check if the API is running and healthy.

**GET** `/healthz`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Verify Claim
Verify a text claim or image for factual accuracy.

**POST** `/v1/verify`

**Request Body** (multipart/form-data):
- `text` (string, required): The claim to verify
- `mode` (string, optional): Verification mode - "fast" or "deep" (default: "fast")
- `language` (string, optional): Language code - "en", "hi", "ta", or "auto" (default: "en")
- `image` (file, optional): Image file to verify

**Response:**
```json
{
  "request_id": "uuid-string",
  "verdict": "true|false|misleading|unverified",
  "confidence": 0.95,
  "explanation": "Detailed explanation of the verdict",
  "key_facts": ["Fact 1", "Fact 2"],
  "reasoning": "Step-by-step analysis",
  "citations": [
    {
      "title": "Source Title",
      "url": "https://example.com",
      "publisher": "Publisher Name",
      "rating": "True",
      "date": "2024-01-01"
    }
  ],
  "language": "en",
  "mode": "fast",
  "timestamp": "2024-01-01T00:00:00Z",
  "metrics": {
    "latency_ms": 1500,
    "cost_usd": 0.001
  }
}
```

## Verification Modes

### Fast Mode
- Uses only Vertex AI Gemini
- Faster response time (~1-2 seconds)
- Lower cost
- Good for general fact checking

### Deep Mode
- Uses Vertex AI Gemini + Google Fact Check API
- Slower response time (~3-5 seconds)
- Higher cost
- More comprehensive verification with citations

## Language Support
- **English (en)**: Default language
- **Hindi (hi)**: Hindi language support
- **Tamil (ta)**: Tamil language support
- **Auto (auto)**: Automatic language detection

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid API key"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Verification failed"
}
```

## Rate Limits
- **Free Tier**: 100 requests/minute
- **Paid Tier**: 1000 requests/minute

## Cost Estimation
- **Fast Mode**: ~$0.001 per request
- **Deep Mode**: ~$0.005 per request
- **Image Processing**: +$0.002 per image

## Examples

### cURL Example
```bash
curl -X POST "https://api.truthlens.app/v1/verify" \
  -H "Authorization: Bearer your-api-key" \
  -F "text=The Earth is round" \
  -F "mode=fast" \
  -F "language=en"
```

### JavaScript Example
```javascript
const formData = new FormData();
formData.append('text', 'The Earth is round');
formData.append('mode', 'fast');
formData.append('language', 'en');

const response = await fetch('https://api.truthlens.app/v1/verify', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer your-api-key'
  },
  body: formData
});

const result = await response.json();
console.log(result);
```

### Python Example
```python
import requests

url = "https://api.truthlens.app/v1/verify"
headers = {"Authorization": "Bearer your-api-key"}
data = {
    "text": "The Earth is round",
    "mode": "fast",
    "language": "en"
}

response = requests.post(url, headers=headers, data=data)
result = response.json()
print(result)
```

## SDKs
- **JavaScript/TypeScript**: Available via npm
- **Python**: Available via pip
- **Go**: Available via go get
- **Java**: Available via Maven

## Support
For API support and questions:
- **Email**: api-support@truthlens.app
- **Documentation**: https://docs.truthlens.app
- **Status Page**: https://status.truthlens.app
