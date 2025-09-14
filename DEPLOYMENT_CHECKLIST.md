# TruthLens Deployment Checklist

## Prerequisites Setup

### 1. Install Google Cloud SDK
```bash
# Option 1: Homebrew (Recommended)
brew install --cask google-cloud-sdk

# Option 2: Manual installation
curl https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-456.0.0-darwin-x86_64.tar.gz | tar xz
./google-cloud-sdk/install.sh

# Add to PATH
echo 'export PATH="$HOME/google-cloud-sdk/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### 2. Authenticate with Google Cloud
```bash
gcloud auth login
gcloud auth application-default login
```

### 3. Set Your Project (Already Created!)
```bash
# Your project is already created: orange-lens-472108
gcloud config set project orange-lens-472108

# Verify project is set correctly
gcloud config get-value project
```

### 4. Enable Required APIs
```bash
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    containerregistry.googleapis.com \
    bigquery.googleapis.com \
    storage.googleapis.com \
    secretmanager.googleapis.com \
    aiplatform.googleapis.com \
    apigateway.googleapis.com \
    servicecontrol.googleapis.com \
    servicemanagement.googleapis.com \
    monitoring.googleapis.com \
    logging.googleapis.com
```

## API Keys Setup

### 1. Vertex AI API Key
- Go to: https://console.cloud.google.com/vertex-ai
- Enable Vertex AI API
- Create service account with Vertex AI User role
- Download service account key

### 2. Google Fact Check API Key
- Go to: https://developers.google.com/fact-check/tools/api
- Enable Fact Check Tools API
- Create API key
- Restrict API key to Fact Check Tools API

## Deployment Steps

### 1. Update Project Configuration
```bash
# Your project ID is already set: orange-lens-472108
export PROJECT_ID="orange-lens-472108"
echo "export PROJECT_ID=\"$PROJECT_ID\"" >> ~/.zshrc

# Verify project is set correctly
gcloud config get-value project
```

### 2. Run Deployment Script
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### 3. Configure Secrets
```bash
# Set API keys in Secret Manager
echo "your-vertex-ai-key" | gcloud secrets versions add truthlens-api-key --data-file=-
echo "your-fact-check-api-key" | gcloud secrets versions add fact-check-api-key --data-file=-
```

### 4. Test the Platform
```bash
# Get API Gateway URL
API_URL=$(gcloud api-gateway gateways describe truthlens-gateway --location=us-central1 --format="value(defaultHostname)")

# Test health endpoint
curl "https://$API_URL/healthz"

# Test verification endpoint
curl -H "Authorization: Bearer your-api-key" \
     -F "text=The Earth is round" \
     -F "mode=fast" \
     -F "language=en" \
     "https://$API_URL/v1/verify"
```

## Troubleshooting

### Common Issues
1. **Permission Denied**: Check IAM roles
2. **API Not Enabled**: Enable required APIs
3. **Billing Not Enabled**: Link project to billing account
4. **Quota Exceeded**: Request quota increase

### Debug Commands
```bash
# Check project status
gcloud config list

# Check enabled APIs
gcloud services list --enabled

# Check Cloud Run services
gcloud run services list

# Check logs
gcloud logs read --service=truthlens-api --limit=50
```

## Cost Estimation
- **Free Tier**: $300 GCP credits
- **Development**: ~$50/month
- **Production**: ~$200/month for 50k queries
- **Scaling**: Pay-per-use model

## Next Steps After Deployment
1. Configure custom domain
2. Set up monitoring alerts
3. Configure CI/CD pipeline
4. Set up backup and disaster recovery
5. Performance optimization
