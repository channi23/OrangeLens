#!/bin/bash

# TruthLens Quick Setup for orange-lens-472108
# This script sets up your specific GCP project

set -e

PROJECT_ID="orange-lens-472108"
REGION="us-central1"

echo "🔍 TruthLens Setup for Project: $PROJECT_ID"
echo "============================================="

# Set the project
echo "📋 Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Verify project is set
CURRENT_PROJECT=$(gcloud config get-value project)
if [ "$CURRENT_PROJECT" != "$PROJECT_ID" ]; then
    echo "❌ Failed to set project. Please check your authentication."
    exit 1
fi

echo "✅ Project set to: $CURRENT_PROJECT"

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

echo "✅ All APIs enabled"

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
    --role="roles/aiplatform.user" \
    --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:truthlens-api@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin" \
    --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:truthlens-api@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor" \
    --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:truthlens-api@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.jobUser" \
    --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:truthlens-api@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet

echo "✅ Permissions granted"

# Create storage bucket
BUCKET_NAME="truthlens-evidence-$PROJECT_ID"
echo "🪣 Creating storage bucket: $BUCKET_NAME"
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
DATASET_ID="truthlens_logs"
echo "📊 Creating BigQuery dataset: $DATASET_ID"
bq mk --dataset --location=US $PROJECT_ID:$DATASET_ID || echo "Dataset already exists"

# Create BigQuery table
TABLE_ID="verification_requests"
echo "📋 Creating BigQuery table: $TABLE_ID"
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

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "📋 Your Project Details:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Storage Bucket: gs://$BUCKET_NAME"
echo "  BigQuery Dataset: $DATASET_ID"
echo "  Service Account: truthlens-api@$PROJECT_ID.iam.gserviceaccount.com"
echo ""
echo "🔑 Next Steps:"
echo "1. Get API keys:"
echo "   - Vertex AI: https://console.cloud.google.com/vertex-ai"
echo "   - Fact Check: https://developers.google.com/fact-check/tools/api"
echo ""
echo "2. Update secrets with real API keys:"
echo "   echo 'your-real-api-key' | gcloud secrets versions add truthlens-api-key --data-file=-"
echo "   echo 'your-real-fact-check-key' | gcloud secrets versions add fact-check-api-key --data-file=-"
echo ""
echo "3. Deploy the application:"
echo "   ./scripts/deploy.sh"
echo ""
echo "4. Test the platform:"
echo "   ./scripts/test-api.sh"
