# Terraform configuration for TruthLens infrastructure

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "bucket_name" {
  description = "Cloud Storage bucket name"
  type        = string
  default     = "truthlens-evidence"
}

variable "dataset_id" {
  description = "BigQuery dataset ID"
  type        = string
  default     = "truthlens_logs"
}

variable "table_id" {
  description = "BigQuery table ID"
  type        = string
  default     = "verification_requests"
}

# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "containerregistry.googleapis.com",
    "bigquery.googleapis.com",
    "storage.googleapis.com",
    "secretmanager.googleapis.com",
    "aiplatform.googleapis.com",
    "apigateway.googleapis.com",
    "servicecontrol.googleapis.com",
    "servicemanagement.googleapis.com"
  ])

  service = each.value
  disable_on_destroy = false
}

# Service Account for Cloud Run
resource "google_service_account" "truthlens_api" {
  account_id   = "truthlens-api"
  display_name = "TruthLens API Service Account"
  description  = "Service account for TruthLens API"
}

# IAM bindings for the service account
resource "google_project_iam_member" "truthlens_api_permissions" {
  for_each = toset([
    "roles/aiplatform.user",
    "roles/storage.objectAdmin",
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/secretmanager.secretAccessor"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.truthlens_api.email}"
}

# Cloud Storage bucket for evidence
resource "google_storage_bucket" "evidence" {
  name          = var.bucket_name
  location      = "US"
  force_destroy = true

  lifecycle_rule {
    condition {
      age = 14
    }
    action {
      type = "Delete"
    }
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 3600
  }
}

# BigQuery dataset
resource "google_bigquery_dataset" "logs" {
  dataset_id  = var.dataset_id
  location    = "US"
  description = "TruthLens verification logs"

  default_table_expiration_ms = 30 * 24 * 60 * 60 * 1000  # 30 days
}

# BigQuery table
resource "google_bigquery_table" "verification_requests" {
  dataset_id = google_bigquery_dataset.logs.dataset_id
  table_id   = var.table_id

  time_partitioning {
    type = "DAY"
    field = "timestamp"
  }

  schema = jsonencode([
    {
      name = "request_id"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "timestamp"
      type = "TIMESTAMP"
      mode = "REQUIRED"
    },
    {
      name = "text"
      type = "STRING"
      mode = "NULLABLE"
    },
    {
      name = "mode"
      type = "STRING"
      mode = "NULLABLE"
    },
    {
      name = "language"
      type = "STRING"
      mode = "NULLABLE"
    },
    {
      name = "verdict"
      type = "STRING"
      mode = "NULLABLE"
    },
    {
      name = "confidence"
      type = "FLOAT"
      mode = "NULLABLE"
    },
    {
      name = "latency_ms"
      type = "FLOAT"
      mode = "NULLABLE"
    },
    {
      name = "cost_usd"
      type = "FLOAT"
      mode = "NULLABLE"
    },
    {
      name = "user_hash"
      type = "STRING"
      mode = "NULLABLE"
    }
  ])
}

# Secret Manager secrets
resource "google_secret_manager_secret" "api_key" {
  secret_id = "truthlens-api-key"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "fact_check_api_key" {
  secret_id = "fact-check-api-key"

  replication {
    auto {}
  }
}

# Cloud Run service
resource "google_cloud_run_service" "truthlens_api" {
  name     = "truthlens-api"
  location = var.region

  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "10"
        "autoscaling.knative.dev/minScale"  = "0"
        "run.googleapis.com/cpu-throttling" = "false"
      }
    }

    spec {
      container_concurrency = 100
      timeout_seconds      = 300

      containers {
        image = "gcr.io/${var.project_id}/truthlens-api:latest"

        ports {
          container_port = 8080
        }

        resources {
          limits = {
            cpu    = "2"
            memory = "2Gi"
          }
        }

        env {
          name  = "GOOGLE_CLOUD_PROJECT"
          value = var.project_id
        }

        env {
          name  = "GOOGLE_CLOUD_LOCATION"
          value = var.region
        }

        env {
          name  = "STORAGE_BUCKET"
          value = var.bucket_name
        }

        env {
          name  = "BIGQUERY_DATASET"
          value = var.dataset_id
        }

        env {
          name  = "BIGQUERY_TABLE"
          value = var.table_id
        }
      }

      service_account_name = google_service_account.truthlens_api.email
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.apis]
}

# Allow unauthenticated access to Cloud Run
resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_service.truthlens_api.name
  location = google_cloud_run_service.truthlens_api.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# API Gateway
resource "google_api_gateway_api" "truthlens_api" {
  provider = google-beta
  api_id   = "truthlens-api"
}

resource "google_api_gateway_api_config" "truthlens_config" {
  provider      = google-beta
  api           = google_api_gateway_api.truthlens_api.api_id
  api_config_id = "truthlens-config"

  openapi_documents {
    document {
      path     = "api-gateway.yaml"
      contents = filebase64("${path.module}/api-gateway.yaml")
    }
  }

  gateway_config {
    backend_config {
      google_service_account = google_service_account.truthlens_api.email
    }
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "google_api_gateway_gateway" "truthlens_gateway" {
  provider   = google-beta
  api_config = google_api_gateway_api_config.truthlens_config.id
  gateway_id = "truthlens-gateway"
  location   = var.region
}

# Outputs
output "cloud_run_url" {
  value = google_cloud_run_service.truthlens_api.status[0].url
}

output "api_gateway_url" {
  value = google_api_gateway_gateway.truthlens_gateway.default_hostname
}

output "storage_bucket" {
  value = google_storage_bucket.evidence.name
}

output "bigquery_dataset" {
  value = google_bigquery_dataset.logs.dataset_id
}

output "service_account_email" {
  value = google_service_account.truthlens_api.email
}
