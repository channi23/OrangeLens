#!/bin/bash

# TruthLens Quick Setup Script
# This script helps you set up the prerequisites for TruthLens deployment

set -e

echo "🚀 TruthLens Quick Setup"
echo "========================="

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is designed for macOS. Please follow manual setup instructions."
    exit 1
fi

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "📦 Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "✅ Homebrew is already installed"
fi

# Install Google Cloud SDK
echo "☁️ Installing Google Cloud SDK..."
if ! command -v gcloud &> /dev/null; then
    brew install --cask google-cloud-sdk
    echo 'export PATH="$HOME/google-cloud-sdk/bin:$PATH"' >> ~/.zshrc
    source ~/.zshrc
else
    echo "✅ Google Cloud SDK is already installed"
fi

# Install Node.js
echo "📦 Installing Node.js..."
if ! command -v node &> /dev/null; then
    brew install node
else
    echo "✅ Node.js is already installed"
fi

# Install Python
echo "🐍 Installing Python..."
if ! command -v python3 &> /dev/null; then
    brew install python
else
    echo "✅ Python is already installed"
fi

# Install jq for JSON processing
echo "🔧 Installing jq..."
if ! command -v jq &> /dev/null; then
    brew install jq
else
    echo "✅ jq is already installed"
fi

echo ""
echo "✅ Prerequisites installation completed!"
echo ""
echo "📋 Next steps:"
echo "1. Authenticate with Google Cloud:"
echo "   gcloud auth login"
echo "   gcloud auth application-default login"
echo ""
echo "2. Create a GCP project:"
echo "   gcloud projects create truthlens-project-\$(date +%s)"
echo ""
echo "3. Enable billing in Google Cloud Console:"
echo "   https://console.cloud.google.com/billing"
echo ""
echo "4. Get API keys:"
echo "   - Vertex AI: https://console.cloud.google.com/vertex-ai"
echo "   - Fact Check: https://developers.google.com/fact-check/tools/api"
echo ""
echo "5. Run deployment:"
echo "   ./scripts/deploy.sh"
echo ""
echo "📚 For detailed instructions, see DEPLOYMENT_CHECKLIST.md"
