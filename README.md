# TruthLens - AI-Powered Fact Verification

A Progressive Web App that provides one-tap fact verification from any mobile app via the system Share sheet, with transparent AI explanations and verified citations.

## 🎯 USP
One-tap fact verification from any mobile app via the system Share sheet, with transparent AI explanations and verified citations. Powered by Google Cloud for scalability, cost-efficiency, and transparency.

## 🏗️ Architecture

```
TruthLens/
├── app/                    # Progressive Web App (React)
│   ├── src/               # React source code
│   ├── public/             # Static assets
│   ├── manifest.json       # PWA manifest
│   └── sw.js              # Service worker
├── api/                    # Backend API (Cloud Run)
│   ├── main.py            # FastAPI application
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile        # Container configuration
├── infra/                  # Infrastructure configs
│   ├── terraform/         # Terraform configurations
│   ├── cloudbuild.yaml   # Cloud Build config
│   └── api-gateway.yaml  # API Gateway spec
├── scripts/               # Deployment scripts
└── docs/                  # Documentation
```

## 🚀 Quick Start

### Prerequisites
- Node.js 16+
- Python 3.11+
- Google Cloud SDK
- GCP Project with billing enabled

### Development Setup
```bash
# Clone the repository
git clone https://github.com/channi23/OrangeLens.git
cd OrangeLens

# Setup development environment
./scripts/setup-dev.sh

# Start development servers
./scripts/start-dev.sh
```

### Production Deployment
```bash
# Deploy to Google Cloud
./scripts/deploy.sh
```

## 📱 Features
- ✅ **One-tap verification** from any app via Share sheet
- ✅ **Text and image verification** using AI
- ✅ **Fast/Deep verification modes**
- ✅ **Multi-language support** (English, Hindi, Tamil)
- ✅ **Offline support** with service worker
- ✅ **Real-time metrics** (latency, cost)
- ✅ **Transparent AI explanations**
- ✅ **Verified citations** from fact-check databases

## 🔧 Tech Stack
- **Frontend**: React PWA, Service Worker, Web Share Target
- **Backend**: Cloud Run, API Gateway, Vertex AI Gemini
- **Data**: BigQuery, Cloud Storage, Google Fact Check API
- **Security**: Secret Manager, API Keys/JWT
- **Monitoring**: Cloud Logging, Cloud Monitoring
- **Infrastructure**: Terraform, Cloud Build

## 📊 Cost Estimate
~$200/month for 50k queries (covered by GCP credits)

## 🏃‍♂️ Getting Started

### 1. Setup Development Environment
```bash
./scripts/setup-dev.sh
```

### 2. Configure Environment Variables
```bash
# API Configuration
cd api
cp config.env.example .env
# Edit .env with your configuration

# PWA Configuration
cd ../app
echo "REACT_APP_API_URL=http://localhost:8080" > .env
```

### 3. Start Development Servers
```bash
./scripts/start-dev.sh
```

### 4. Test the API
```bash
./scripts/test-api.sh
```

## 🚀 Deployment

### Prerequisites
1. GCP Project with billing enabled
2. gcloud CLI installed and authenticated
3. Required APIs enabled

### Deploy to Production
```bash
# Set your project ID
export PROJECT_ID="your-project-id"

# Deploy everything
./scripts/deploy.sh
```

### Manual Deployment Steps
1. **Enable APIs**: Run the deployment script
2. **Create Infrastructure**: Deploy Terraform configurations
3. **Build & Deploy API**: Cloud Build + Cloud Run
4. **Deploy PWA**: Build and deploy to hosting service
5. **Configure Monitoring**: Set up alerts and dashboards

## 📚 Documentation
- [API Documentation](api/README.md)
- [PWA Documentation](app/README.md)
- [Infrastructure Documentation](infra/README.md)

## 🧪 Testing

### API Testing
```bash
# Test health endpoint
curl http://localhost:8080/healthz

# Test verification endpoint
curl -H "Authorization: Bearer test-key" \
     -F "text=The Earth is round" \
     -F "mode=fast" \
     -F "language=en" \
     http://localhost:8080/v1/verify
```

### PWA Testing
1. Open http://localhost:3000
2. Test share functionality
3. Verify offline support
4. Check service worker

## 🔒 Security
- **API Keys**: Bearer token authentication
- **Service Accounts**: IAM-based permissions
- **Data Encryption**: All data encrypted at rest and in transit
- **PII Protection**: User data anonymized
- **Retention Policies**: Automatic data deletion

## 📊 Monitoring
- **Cloud Logging**: Application logs
- **Cloud Monitoring**: Metrics and alerting
- **BigQuery**: Analytics and reporting
- **Uptime Checks**: Service availability

## 🛠️ Development

### Project Structure
```
TruthLens/
├── app/                    # React PWA
│   ├── src/App.js          # Main React component
│   ├── src/App.css          # Styles
│   ├── public/index.html    # HTML template
│   ├── manifest.json        # PWA manifest
│   └── sw.js               # Service worker
├── api/                     # Python FastAPI
│   ├── main.py             # Main API application
│   ├── simple_main.py      # Simple development server
│   ├── requirements.txt    # Dependencies
│   └── Dockerfile          # Container config
├── infra/                   # Infrastructure
│   ├── terraform/          # Terraform configs
│   ├── cloudbuild.yaml     # CI/CD config
│   └── api-gateway.yaml    # API Gateway spec
└── scripts/                # Deployment scripts
    ├── deploy.sh           # Production deployment
    ├── setup-dev.sh        # Development setup
    └── start-dev.sh        # Start dev servers
```

### Adding Features
1. **API**: Add endpoints in `api/main.py`
2. **PWA**: Add components in `app/src/`
3. **Infrastructure**: Update Terraform configs
4. **Monitoring**: Add metrics and alerts

## 🤝 Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License
MIT License - see LICENSE file for details

## 🆘 Support
- **Email**: support@truthlens.app
- **Documentation**: https://docs.truthlens.app
- **Issues**: https://github.com/channi23/OrangeLens/issues
- **Status**: https://status.truthlens.app

## 🗺️ Roadmap
- [ ] Mobile app (iOS/Android)
- [ ] Browser extension
- [ ] Telegram bot
- [ ] WhatsApp integration
- [ ] Advanced analytics
- [ ] Custom fact-check sources
- [ ] API rate limiting
- [ ] Multi-tenant support

---

**TruthLens** - Making fact verification accessible, transparent, and reliable. 🔍✨