#!/bin/bash

# TruthLens Interactive Setup Script
# This script guides you through the complete setup process

set -e

echo "🔍 TruthLens Interactive Setup"
echo "==============================="
echo ""

# Function to prompt user
prompt_user() {
    local prompt="$1"
    local default="$2"
    local response
    
    if [ -n "$default" ]; then
        read -p "$prompt [$default]: " response
        echo "${response:-$default}"
    else
        read -p "$prompt: " response
        echo "$response"
    fi
}

# Step 1: Check prerequisites
echo "📋 Step 1: Checking Prerequisites"
echo "----------------------------------"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud SDK not found"
    echo "Please run: ./scripts/setup-prerequisites.sh"
    exit 1
else
    echo "✅ Google Cloud SDK found"
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Not authenticated with Google Cloud"
    echo "Please run: gcloud auth login"
    exit 1
else
    echo "✅ Authenticated with Google Cloud"
fi

# Step 2: Project setup
echo ""
echo "📋 Step 2: Project Setup"
echo "------------------------"

# Get current project
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
if [ -z "$CURRENT_PROJECT" ]; then
    echo "❌ No project set"
    PROJECT_ID=$(prompt_user "Enter your GCP project ID")
    gcloud config set project "$PROJECT_ID"
else
    echo "✅ Current project: $CURRENT_PROJECT"
    PROJECT_ID="$CURRENT_PROJECT"
fi

# Step 3: Enable APIs
echo ""
echo "📋 Step 3: Enabling Required APIs"
echo "----------------------------------"

APIS=(
    "run.googleapis.com"
    "cloudbuild.googleapis.com"
    "containerregistry.googleapis.com"
    "bigquery.googleapis.com"
    "storage.googleapis.com"
    "secretmanager.googleapis.com"
    "aiplatform.googleapis.com"
    "apigateway.googleapis.com"
    "servicecontrol.googleapis.com"
    "servicemanagement.googleapis.com"
    "monitoring.googleapis.com"
    "logging.googleapis.com"
)

echo "Enabling required APIs..."
for api in "${APIS[@]}"; do
    echo "  Enabling $api..."
    gcloud services enable "$api" --quiet
done

echo "✅ All APIs enabled"

# Step 4: Create service account
echo ""
echo "📋 Step 4: Creating Service Account"
echo "-----------------------------------"

SERVICE_ACCOUNT="truthlens-api@$PROJECT_ID.iam.gserviceaccount.com"

if gcloud iam service-accounts describe "$SERVICE_ACCOUNT" &>/dev/null; then
    echo "✅ Service account already exists"
else
    echo "Creating service account..."
    gcloud iam service-accounts create truthlens-api \
        --display-name="TruthLens API Service Account" \
        --description="Service account for TruthLens API"
    echo "✅ Service account created"
fi

# Step 5: Grant permissions
echo ""
echo "📋 Step 5: Granting Permissions"
echo "--------------------------------"

ROLES=(
    "roles/aiplatform.user"
    "roles/storage.objectAdmin"
    "roles/bigquery.dataEditor"
    "roles/bigquery.jobUser"
    "roles/secretmanager.secretAccessor"
)

for role in "${ROLES[@]}"; do
    echo "  Granting $role..."
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="$role" \
        --quiet
done

echo "✅ Permissions granted"

# Step 6: Create infrastructure
echo ""
echo "📋 Step 6: Creating Infrastructure"
echo "----------------------------------"

# Create storage bucket
BUCKET_NAME="truthlens-evidence-$PROJECT_ID"
if gsutil ls "gs://$BUCKET_NAME" &>/dev/null; then
    echo "✅ Storage bucket already exists"
else
    echo "Creating storage bucket..."
    gsutil mb -p "$PROJECT_ID" -c STANDARD -l US "gs://$BUCKET_NAME"
    echo "✅ Storage bucket created"
fi

# Create BigQuery dataset
DATASET_ID="truthlens_logs"
if bq ls -d "$PROJECT_ID:$DATASET_ID" &>/dev/null; then
    echo "✅ BigQuery dataset already exists"
else
    echo "Creating BigQuery dataset..."
    bq mk --dataset --location=US "$PROJECT_ID:$DATASET_ID"
    echo "✅ BigQuery dataset created"
fi

# Create BigQuery table
TABLE_ID="verification_requests"
if bq ls -t "$PROJECT_ID:$DATASET_ID.$TABLE_ID" &>/dev/null; then
    echo "✅ BigQuery table already exists"
else
    echo "Creating BigQuery table..."
    bq mk --table \
        --time_partitioning_field=timestamp \
        --time_partitioning_type=DAY \
        "$PROJECT_ID:$DATASET_ID.$TABLE_ID" \
        request_id:STRING,timestamp:TIMESTAMP,text:STRING,mode:STRING,language:STRING,verdict:STRING,confidence:FLOAT,latency_ms:FLOAT,cost_usd:FLOAT,user_hash:STRING
    echo "✅ BigQuery table created"
fi

# Step 7: Create secrets
echo ""
echo "📋 Step 7: Creating Secrets"
echo "---------------------------"

# Create API key secret
if gcloud secrets describe truthlens-api-key &>/dev/null; then
    echo "✅ API key secret already exists"
else
    echo "Creating API key secret..."
    echo "your-api-key-here" | gcloud secrets create truthlens-api-key --data-file=-
    echo "✅ API key secret created"
fi

# Create Fact Check API key secret
if gcloud secrets describe fact-check-api-key &>/dev/null; then
    echo "✅ Fact Check API key secret already exists"
else
    echo "Creating Fact Check API key secret..."
    echo "your-fact-check-api-key-here" | gcloud secrets create fact-check-api-key --data-file=-
    echo "✅ Fact Check API key secret created"
fi

# Step 8: Update deployment script
echo ""
echo "📋 Step 8: Updating Deployment Script"
echo "--------------------------------------"

# Update project ID in deployment script
sed -i.bak "s/truthlens-project/$PROJECT_ID/g" scripts/deploy.sh
echo "✅ Deployment script updated"

# Step 9: Summary
echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "📋 Summary:"
echo "  Project ID: $PROJECT_ID"
echo "  Service Account: $SERVICE_ACCOUNT"
echo "  Storage Bucket: gs://$BUCKET_NAME"
echo "  BigQuery Dataset: $DATASET_ID"
echo "  BigQuery Table: $TABLE_ID"
echo ""
echo "🔑 Next Steps:"
echo "1. Update API keys in Secret Manager:"
echo "   gcloud secrets versions add truthlens-api-key --data-file=-"
echo "   gcloud secrets versions add fact-check-api-key --data-file=-"
echo ""
echo "2. Deploy the application:"
echo "   ./scripts/deploy.sh"
echo ""
echo "3. Test the platform:"
echo "   ./scripts/test-api.sh"
echo ""
echo "📚 For detailed instructions, see DEPLOYMENT_CHECKLIST.md"
