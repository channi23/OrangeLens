#!/bin/bash

# TruthLens Development Setup Script
# This script sets up the development environment for TruthLens

set -e

echo "🛠️ Setting up TruthLens development environment..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    echo "   Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if Tesseract OCR is installed (used for image text extraction)
if ! command -v tesseract &> /dev/null; then
    echo "🔍 Installing Tesseract OCR..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install tesseract
        else
            echo "⚠️ Homebrew not found. Please install Tesseract manually: https://tesseract-ocr.github.io/tessdoc/Installation.html"
            exit 1
        fi
    elif [[ -f "/etc/debian_version" ]]; then
        sudo apt-get update && sudo apt-get install -y tesseract-ocr
    else
        echo "⚠️ Unsupported OS for automatic Tesseract install. Install it manually before continuing."
        exit 1
    fi
fi

echo "✅ Prerequisites check passed"

# Setup API environment
echo "🐍 Setting up Python API environment..."
cd api

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
if [ ! -f .env ]; then
    cp config.env.example .env
    echo "📝 Created .env file. Please update with your configuration."
fi

cd ..

# Setup PWA environment
echo "⚛️ Setting up React PWA environment..."
cd app

# Install dependencies
npm install

# Create .env file
if [ ! -f .env ]; then
    echo "REACT_APP_API_URL=http://localhost:8080" > .env
    echo "📝 Created .env file for PWA."
fi

cd ..

# Setup development scripts
echo "📜 Creating development scripts..."

# Create start-dev.sh
cat > scripts/start-dev.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting TruthLens development servers..."

# Start API server in background
cd api
source venv/bin/activate
python simple_main.py &
API_PID=$!

# Start PWA server
cd ../app
npm start &
PWA_PID=$!

echo "✅ Development servers started!"
echo "   API: http://localhost:8080"
echo "   PWA: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for interrupt
trap "kill $API_PID $PWA_PID; exit" INT
wait
EOF

chmod +x scripts/start-dev.sh

# Create test-api.sh
cat > scripts/test-api.sh << 'EOF'
#!/bin/bash

API_URL=${1:-"http://localhost:8080"}
API_KEY=${2:-"test-key"}

echo "🧪 Testing TruthLens API at $API_URL"

# Test health endpoint
echo "Testing health endpoint..."
curl -s "$API_URL/healthz" | jq '.' || echo "Health check failed"

echo ""

# Test verification endpoint
echo "Testing verification endpoint..."
curl -s -H "Authorization: Bearer $API_KEY" \
     -F "text=The Earth is round" \
     -F "mode=fast" \
     -F "language=en" \
     "$API_URL/v1/verify" | jq '.' || echo "Verification test failed"
EOF

chmod +x scripts/test-api.sh

echo "✅ Development environment setup completed!"
echo ""
echo "📋 Next steps:"
echo "   1. Update API configuration in api/.env"
echo "   2. Update PWA configuration in app/.env"
echo "   3. Run './scripts/start-dev.sh' to start development servers"
echo "   4. Run './scripts/test-api.sh' to test the API"
echo ""
echo "🔧 Configuration files:"
echo "   - api/.env - API configuration"
echo "   - app/.env - PWA configuration"
echo "   - infra/terraform/ - Infrastructure configuration"
echo ""
echo "📚 Documentation:"
echo "   - README.md - Project overview"
echo "   - api/README.md - API documentation"
echo "   - app/README.md - PWA documentation"
