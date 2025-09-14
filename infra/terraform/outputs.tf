# Terraform outputs for TruthLens

output "project_id" {
  description = "GCP Project ID"
  value       = var.project_id
}

output "region" {
  description = "GCP Region"
  value       = var.region
}

output "cloud_run_url" {
  description = "Cloud Run service URL"
  value       = google_cloud_run_service.truthlens_api.status[0].url
}

output "api_gateway_url" {
  description = "API Gateway URL"
  value       = google_api_gateway_gateway.truthlens_gateway.default_hostname
}

output "storage_bucket" {
  description = "Cloud Storage bucket name"
  value       = google_storage_bucket.evidence.name
}

output "bigquery_dataset" {
  description = "BigQuery dataset ID"
  value       = google_bigquery_dataset.logs.dataset_id
}

output "bigquery_table" {
  description = "BigQuery table ID"
  value       = google_bigquery_table.verification_requests.table_id
}

output "service_account_email" {
  description = "Service account email"
  value       = google_service_account.truthlens_api.email
}

output "secret_names" {
  description = "Secret Manager secret names"
  value = {
    api_key           = google_secret_manager_secret.api_key.secret_id
    fact_check_api_key = google_secret_manager_secret.fact_check_api_key.secret_id
  }
}
