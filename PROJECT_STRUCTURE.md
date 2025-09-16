# TruthLens Project Structure

This document outlines the complete project structure for TruthLens, an AI-powered fact verification PWA.

## 📁 Directory Structure

```
TruthLens/
├── README.md                           # Main project documentation
├── TruthLens_Optimized_Prototype.docx  # Original project specification
│
├── app/                                # Progressive Web App (React)
│   ├── README.md                      # PWA documentation
│   ├── package.json                   # Node.js dependencies
│   ├── manifest.json                  # PWA manifest
│   ├── public/
│   │   ├── index.html                 # HTML template
│   │   └── sw.js                      # Service worker
│   └── src/
│       ├── App.js                     # Main React component
│       └── App.css                    # Styles
│
├── api/                                # Backend API (Python FastAPI)
│   ├── README.md                      # API documentation
│   ├── main.py                        # Main API application
│   ├── simple_main.py                 # Simple development server
│   ├── requirements.txt               # Python dependencies
│   ├── Dockerfile                     # Container configuration
│   └── config.env.example             # Environment configuration template
│
├── infra/                              # Infrastructure configurations
│   ├── README.md                      # Infrastructure documentation
│   ├── cloudbuild.yaml                # Cloud Build CI/CD configuration
│   ├── api-gateway.yaml               # API Gateway OpenAPI specification
│   ├── monitoring.tf                  # Monitoring and alerting configuration
│   └── terraform/                      # Terraform infrastructure as code
│       ├── main.tf                     # Main Terraform configuration
│       ├── variables.tf               # Terraform variables
│       └── outputs.tf                  # Terraform outputs
│
└── scripts/                            # Deployment and development scripts
    ├── deploy.sh                       # Production deployment script
    └── setup-dev.sh                   # Development environment setup
```

## 🎯 Component Overview

### Frontend (PWA)
- **Technology**: React with PWA capabilities
- **Features**: Share target, offline support, responsive design
- **Deployment**: Firebase Hosting or any static hosting
- **Key Files**:
  - `manifest.json`: PWA configuration
  - `public/sw.js`: Service worker for offline support
  - `src/App.js`: Main application component

### Backend (API)
- **Technology**: Python FastAPI on Cloud Run
- **Features**: AI integration, fact checking, logging
- **Deployment**: Google Cloud Run
- **Key Files**:
  - `main.py`: Complete API with AI integration
  - `simple_main.py`: Development server
  - `requirements.txt`: Python dependencies

### Infrastructure
- **Technology**: Terraform + Google Cloud
- **Services**: Cloud Run, API Gateway, BigQuery, Cloud Storage
- **Deployment**: Terraform apply + Cloud Build
- **Key Files**:
  - `terraform/main.tf`: Infrastructure definition
  - `cloudbuild.yaml`: CI/CD pipeline
  - `api-gateway.yaml`: API Gateway specification

## 🔧 Configuration Files

### Environment Variables
- **API**: `api/config.env.example` → `api/.env`
- **PWA**: `app/.env` (created by setup script)

### Secrets
- **API Key**: Stored in Google Secret Manager
- **Fact Check API Key**: Stored in Google Secret Manager

### Deployment
- **Terraform**: Infrastructure as code
- **Cloud Build**: Automated CI/CD
- **Scripts**: Manual deployment automation

## 🚀 Getting Started

### 1. Development Setup
```bash
./scripts/setup-dev.sh
```

### 2. Start Development
```bash
./scripts/start-dev.sh
```

### 3. Deploy to Production
```bash
./scripts/deploy.sh
```

## 📊 Key Features Implemented

### ✅ Completed Features
1. **PWA Structure**: Complete React PWA with manifest and service worker
2. **API Backend**: FastAPI with AI integration and fact checking
3. **Infrastructure**: Terraform configs for all GCP services
4. **CI/CD**: Cloud Build pipeline for automated deployment
5. **Monitoring**: Cloud Monitoring dashboards and alerts
6. **Security**: API Gateway, Secret Manager, IAM permissions
7. **Data Layer**: BigQuery logging and Cloud Storage evidence
8. **Documentation**: Comprehensive documentation for all components

### 🔄 Ready for Implementation
- Vertex AI Gemini integration (code ready, needs API keys)
- Google Fact Check API integration (code ready, needs API keys)
- Multi-language support (English, Hindi, Tamil)
- Share target functionality
- Offline support with service worker
- Real-time metrics and cost tracking

## 🎯 Next Steps

1. **Configure API Keys**: Set up Vertex AI and Fact Check API keys
2. **Deploy Infrastructure**: Run Terraform to create GCP resources
3. **Deploy API**: Use Cloud Build to deploy the backend
4. **Deploy PWA**: Build and deploy the frontend
5. **Test Integration**: Verify end-to-end functionality
6. **Configure Monitoring**: Set up alerts and dashboards

## 📈 Scalability Considerations

- **Auto-scaling**: Cloud Run scales from 0 to 10 instances
- **Cost Optimization**: Lifecycle policies for data retention
- **Performance**: P95 latency < 3 seconds target
- **Reliability**: Multi-region deployment capability
- **Security**: Comprehensive IAM and encryption

This structure provides a complete, production-ready foundation for the TruthLens fact verification platform.
