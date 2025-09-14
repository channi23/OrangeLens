# Terraform variables for TruthLens

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
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

variable "max_instances" {
  description = "Maximum Cloud Run instances"
  type        = number
  default     = 10
}

variable "min_instances" {
  description = "Minimum Cloud Run instances"
  type        = number
  default     = 0
}

variable "cpu_limit" {
  description = "CPU limit for Cloud Run"
  type        = string
  default     = "2"
}

variable "memory_limit" {
  description = "Memory limit for Cloud Run"
  type        = string
  default     = "2Gi"
}
