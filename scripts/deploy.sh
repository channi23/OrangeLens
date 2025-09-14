#!/bin/bash

# TruthLens Deployment Script
# This script deploys the TruthLens application to Google Cloud

set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"orange-lens-472108"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME="truthlens-api"
BUCKET_NAME="truthlens-evidence"
DATASET_ID="truthlens_logs"
TABLE_ID="verification_requests"
GEMINI_MODEL=${GEMINI_MODEL:-"gemini-1.5-flash-002"}
GEMINI_MODE=${GEMINI_MODE:-"express"}

echo "🚀 Starting TruthLens deployment..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "🔐 Please authenticate with gcloud first:"
    echo "   gcloud auth login"
    exit 1
fi

# Set project
echo "📋 Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required APIs..."
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

# Create service account
echo "👤 Creating service account..."
gcloud iam service-accounts create truthlens-api \
    --display-name="TruthLens API Service Account" \
    --description="Service account for TruthLens API" \
    --quiet || echo "Service account already exists"

# Grant permissions
echo "🔑 Granting permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:truthlens-api@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:truthlens-api@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:truthlens-api@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:truthlens-api@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.jobUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:truthlens-api@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Create Cloud Storage bucket
echo "🪣 Creating Cloud Storage bucket..."
gsutil mb -p $PROJECT_ID -c STANDARD -l US gs://$BUCKET_NAME || echo "Bucket already exists"

# Set lifecycle policy
echo "⏰ Setting lifecycle policy..."
cat > lifecycle.json << EOF
{
  "rule": [
    {
      "action": {"type": "Delete"},
      "condition": {"age": 14}
    }
  ]
}
EOF
gsutil lifecycle set lifecycle.json gs://$BUCKET_NAME
rm lifecycle.json

# Create BigQuery dataset
echo "📊 Creating BigQuery dataset..."
bq mk --dataset --location=US $PROJECT_ID:$DATASET_ID || echo "Dataset already exists"

# Create BigQuery table
echo "📋 Creating BigQuery table..."
bq mk --table \
    --time_partitioning_field=timestamp \
    --time_partitioning_type=DAY \
    $PROJECT_ID:$DATASET_ID.$TABLE_ID \
    request_id:STRING,timestamp:TIMESTAMP,text:STRING,mode:STRING,language:STRING,verdict:STRING,confidence:FLOAT,latency_ms:FLOAT,cost_usd:FLOAT,user_hash:STRING \
    || echo "Table already exists"

# Create secrets
echo "🔐 Creating secrets..."
echo "your-api-key-here" | gcloud secrets create truthlens-api-key --data-file=- || echo "Secret already exists"
echo "your-fact-check-api-key-here" | gcloud secrets create fact-check-api-key --data-file=- || echo "Secret already exists"
echo "placeholder-gemini-express-key" | gcloud secrets create gemini-express-api-key --data-file=- || echo "Secret already exists"

# Build and deploy API
echo "🏗️ Building and deploying API..."
cd api
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --min-instances 0 \
    --max-instances 10 \
    --concurrency 100 \
    --timeout 300 \
    --port 8080 \
    --service-account truthlens-api@$PROJECT_ID.iam.gserviceaccount.com \
    --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID \
    --set-env-vars GOOGLE_CLOUD_LOCATION=$REGION \
    --set-env-vars STORAGE_BUCKET=$BUCKET_NAME \
    --set-env-vars BIGQUERY_DATASET=$DATASET_ID \
    --set-env-vars BIGQUERY_TABLE=$TABLE_ID \
    --set-env-vars GEMINI_MODEL=$GEMINI_MODEL,GEMINI_MODE=$GEMINI_MODE \
    --set-secrets GEMINI_API_KEY=gemini-express-api-key:latest

# Get Cloud Run URL
CLOUD_RUN_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
echo "🌐 Cloud Run URL: $CLOUD_RUN_URL"

# Deploy API Gateway
echo "🌉 Deploying API Gateway..."
cd ../infra

# Update API Gateway config with actual Cloud Run URL
sed "s/{hash}/$(echo $CLOUD_RUN_URL | sed 's/.*-\([^-]*\)-uc\.a\.run\.app/\1/')/g" api-gateway.yaml > api-gateway-updated.yaml
sed -i "s/{project-id}/$PROJECT_ID/g" api-gateway-updated.yaml

# Create API Gateway
gcloud api-gateway api-configs create truthlens-config \
    --api=truthlens-api \
    --openapi-spec=api-gateway-updated.yaml \
    --backend-auth-service-account=truthlens-api@$PROJECT_ID.iam.gserviceaccount.com \
    || echo "API config already exists"

gcloud api-gateway gateways create truthlens-gateway \
    --api=truthlens-api \
    --api-config=truthlens-config \
    --location=$REGION \
    || echo "Gateway already exists"

# Get API Gateway URL
API_GATEWAY_URL=$(gcloud api-gateway gateways describe truthlens-gateway --location=$REGION --format="value(defaultHostname)")
echo "🌐 API Gateway URL: https://$API_GATEWAY_URL"

# Deploy PWA
echo "📱 Deploying PWA..."
cd ../app

# Update API URL in environment
echo "REACT_APP_API_URL=https://$API_GATEWAY_URL" > .env.production

# Build PWA
npm install
npm run build

# Deploy to Firebase Hosting (if configured)
if command -v firebase &> /dev/null; then
    echo "🔥 Deploying to Firebase Hosting..."
    firebase deploy --only hosting
else
    echo "📁 PWA built in ./build directory. Deploy manually to your hosting service."
fi

# Cleanup
rm -f ../infra/api-gateway-updated.yaml

echo "✅ Deployment completed!"
echo ""
echo "📋 Summary:"
echo "   Project ID: $PROJECT_ID"
echo "   Region: $REGION"
echo "   Cloud Run URL: $CLOUD_RUN_URL"
echo "   API Gateway URL: https://$API_GATEWAY_URL"
echo "   Storage Bucket: gs://$BUCKET_NAME"
echo "   BigQuery Dataset: $DATASET_ID"
echo ""
echo "🔧 Next steps:"
echo "   1. Update API keys in Secret Manager"
echo "   2. Configure custom domain for API Gateway"
echo "   3. Set up monitoring alerts"
echo "   4. Deploy PWA to your hosting service"
echo ""
echo "🧪 Test the API:"
echo "   curl -H \"Authorization: Bearer your-api-key\" \\"
echo "        -F \"text=The Earth is round\" \\"
echo "        https://$API_GATEWAY_URL/v1/verify"
