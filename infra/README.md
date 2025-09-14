# TruthLens Infrastructure Documentation

## Overview
TruthLens infrastructure is built on Google Cloud Platform using modern cloud-native services for scalability, cost-efficiency, and reliability.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PWA Frontend  │    │  API Gateway    │    │   Cloud Run     │
│   (Firebase)    │◄──►│   (Google)      │◄──►│   (Backend)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────┐              │
                       │  Vertex AI      │◄─────────────┤
                       │  Gemini         │              │
                       └─────────────────┘              │
                                                        │
                       ┌─────────────────┐              │
                       │  Fact Check     │◄─────────────┤
                       │  API            │              │
                       └─────────────────┘              │
                                                        │
┌─────────────────┐    ┌─────────────────┐              │
│   BigQuery      │    │  Cloud Storage  │◄─────────────┘
│   (Logs)        │    │  (Evidence)     │
└─────────────────┘    └─────────────────┘
```

## Services Used

### Compute
- **Cloud Run**: Serverless container platform for API
- **API Gateway**: Managed API gateway for routing and security

### AI & ML
- **Vertex AI**: Gemini 1.5-flash for fact verification
- **Google Fact Check API**: External fact-checking database

### Storage
- **Cloud Storage**: Evidence storage with lifecycle policies
- **BigQuery**: Structured logging and analytics

### Security
- **Secret Manager**: API keys and sensitive configuration
- **IAM**: Service account permissions

### Monitoring
- **Cloud Logging**: Application logs
- **Cloud Monitoring**: Metrics and alerting
- **Uptime Checks**: Service availability monitoring

## Infrastructure as Code

### Terraform
All infrastructure is defined in Terraform for reproducibility:

```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

### Cloud Build
Automated CI/CD pipeline for deployments:

```bash
gcloud builds submit --config infra/cloudbuild.yaml
```

## Configuration

### Environment Variables
- `GOOGLE_CLOUD_PROJECT`: GCP Project ID
- `GOOGLE_CLOUD_LOCATION`: GCP Region
- `STORAGE_BUCKET`: Cloud Storage bucket name
- `BIGQUERY_DATASET`: BigQuery dataset ID
- `BIGQUERY_TABLE`: BigQuery table ID

### Secrets
- `truthlens-api-key`: API authentication key
- `fact-check-api-key`: Google Fact Check API key

## Deployment

### Prerequisites
1. GCP Project with billing enabled
2. gcloud CLI installed and authenticated
3. Required APIs enabled

### Quick Deploy
```bash
./scripts/deploy.sh
```

### Manual Deploy
```bash
# 1. Enable APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com

# 2. Deploy infrastructure
cd infra/terraform
terraform apply

# 3. Deploy API
cd ../../api
gcloud builds submit --tag gcr.io/PROJECT_ID/truthlens-api
gcloud run deploy truthlens-api --image gcr.io/PROJECT_ID/truthlens-api

# 4. Deploy PWA
cd ../app
npm run build
firebase deploy
```

## Monitoring

### Dashboards
- **Request Rate**: Requests per second
- **P95 Latency**: 95th percentile response time
- **Error Rate**: Error percentage
- **Cost Metrics**: Cost per 1K queries
- **Verdict Distribution**: Distribution of verification results

### Alerts
- **High Latency**: P95 > 3 seconds
- **High Error Rate**: Error rate > 2%
- **Service Down**: Uptime check failures

### Logs
- **Request Logs**: All API requests logged to BigQuery
- **Error Logs**: Application errors in Cloud Logging
- **Audit Logs**: Security and access logs

## Cost Optimization

### Auto-scaling
- **Min Instances**: 0 (scale to zero)
- **Max Instances**: 10
- **Concurrency**: 100 requests per instance

### Lifecycle Policies
- **Images**: Deleted after 14 days
- **Logs**: Deleted after 30 days
- **Responses**: Deleted after 30 days

### Cost Controls
- **Fast Mode**: AI-only verification (~$0.001/request)
- **Deep Mode**: AI + Fact Check (~$0.005/request)
- **Image Processing**: Additional $0.002/image

## Security

### Authentication
- **API Keys**: Bearer token authentication
- **Service Accounts**: IAM-based permissions
- **CORS**: Configured for specific origins

### Data Protection
- **Encryption**: All data encrypted at rest and in transit
- **PII**: User data anonymized with hashing
- **Retention**: Automatic data deletion policies

### Network Security
- **HTTPS**: All traffic encrypted
- **API Gateway**: Managed security layer
- **VPC**: Private network configuration (optional)

## Backup & Recovery

### Data Backup
- **BigQuery**: Automatic backups
- **Cloud Storage**: Versioning enabled
- **Secrets**: Replicated across regions

### Disaster Recovery
- **Multi-region**: Deploy to multiple regions
- **Cross-region**: Data replication
- **RTO**: 5 minutes (Cloud Run cold start)
- **RPO**: 1 hour (BigQuery replication)

## Scaling

### Horizontal Scaling
- **Auto-scaling**: Based on request volume
- **Load Balancing**: API Gateway handles distribution
- **Regional Deployment**: Deploy to multiple regions

### Vertical Scaling
- **CPU**: Up to 2 vCPUs per instance
- **Memory**: Up to 2GB per instance
- **Concurrency**: Up to 100 requests per instance

## Maintenance

### Updates
- **API**: Rolling updates via Cloud Run
- **Infrastructure**: Terraform apply
- **Monitoring**: Automatic updates

### Monitoring
- **Health Checks**: Automated uptime monitoring
- **Performance**: Latency and throughput metrics
- **Cost**: Daily cost reports

## Troubleshooting

### Common Issues
1. **API Timeout**: Increase Cloud Run timeout
2. **High Latency**: Check Vertex AI quotas
3. **Authentication**: Verify API keys in Secret Manager
4. **Storage**: Check bucket permissions

### Debug Commands
```bash
# Check Cloud Run logs
gcloud logs read --service=truthlens-api

# Check API Gateway status
gcloud api-gateway gateways describe truthlens-gateway

# Check BigQuery data
bq query "SELECT * FROM truthlens_logs.verification_requests LIMIT 10"
```

## Support
- **Documentation**: https://docs.truthlens.app/infrastructure
- **Issues**: https://github.com/truthlens/infrastructure/issues
- **Email**: infrastructure@truthlens.app
