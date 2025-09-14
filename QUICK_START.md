# TruthLens - Quick Start Guide

## 🚀 Get TruthLens Running in 5 Minutes

### Prerequisites
- Google Cloud Project with billing enabled
- gcloud CLI installed and authenticated
- Node.js 16+ and Python 3.11+

### Step 1: Clone and Setup
```bash
git clone https://github.com/truthlens/truthlens.git
cd truthlens
chmod +x scripts/*.sh
```

### Step 2: Configure Project
```bash
# Set your GCP project ID
export PROJECT_ID="your-project-id"

# Update project ID in deployment script
sed -i "s/truthlens-project/$PROJECT_ID/g" scripts/deploy.sh
```

### Step 3: Deploy Everything
```bash
# This will create all infrastructure and deploy the app
./scripts/deploy.sh
```

### Step 4: Get API Keys
1. **Vertex AI API Key**: Get from Google Cloud Console
2. **Fact Check API Key**: Get from Google Fact Check Tools
3. **Update Secrets**:
```bash
echo "your-vertex-ai-key" | gcloud secrets versions add truthlens-api-key --data-file=-
echo "your-fact-check-key" | gcloud secrets versions add fact-check-api-key --data-file=-
```

### Step 5: Test the API
```bash
# Get your API Gateway URL from deployment output
API_URL="https://your-gateway-url"

# Test verification
curl -H "Authorization: Bearer your-api-key" \
     -F "text=The Earth is round" \
     -F "mode=fast" \
     -F "language=en" \
     "$API_URL/v1/verify"
```

## 🎯 What You Get

### ✅ Complete Infrastructure
- **Cloud Run**: Serverless API backend
- **API Gateway**: Managed API with security
- **BigQuery**: Analytics and logging
- **Cloud Storage**: Evidence storage
- **Monitoring**: Dashboards and alerts

### ✅ Working Applications
- **PWA**: Progressive Web App with share functionality
- **API**: RESTful API with AI integration
- **Monitoring**: Real-time metrics and alerting

### ✅ Production Ready
- **Security**: API keys, IAM, encryption
- **Scalability**: Auto-scaling, cost optimization
- **Monitoring**: Comprehensive observability
- **Documentation**: Complete documentation

## 🔧 Customization

### Environment Variables
```bash
# API Configuration
export GOOGLE_CLOUD_PROJECT="your-project"
export REGION="us-central1"
export BUCKET_NAME="your-bucket"
```

### API Endpoints
- `GET /healthz` - Health check
- `POST /v1/verify` - Fact verification

### PWA Features
- Share target integration
- Offline support
- Multi-language support
- Real-time metrics

## 📊 Cost Estimate
- **Development**: ~$50/month
- **Production**: ~$200/month for 50k queries
- **Scaling**: Pay-per-use model

## 🆘 Troubleshooting

### Common Issues
1. **API Key Errors**: Check Secret Manager configuration
2. **Permission Errors**: Verify IAM roles
3. **Deployment Failures**: Check Cloud Build logs
4. **API Timeouts**: Increase Cloud Run timeout

### Debug Commands
```bash
# Check deployment status
gcloud run services list

# View logs
gcloud logs read --service=truthlens-api

# Check API Gateway
gcloud api-gateway gateways list
```

## 📚 Next Steps
1. **Customize**: Update branding and configuration
2. **Scale**: Configure auto-scaling parameters
3. **Monitor**: Set up custom alerts
4. **Extend**: Add new features and integrations

## 🎉 Success!
You now have a complete AI-powered fact verification platform running on Google Cloud!

**API URL**: `https://your-gateway-url`
**PWA URL**: `https://your-pwa-url`
**Monitoring**: Google Cloud Console → Monitoring
