variable "project" {
  description = "Your GCP Project ID"
}

variable "credentials" {
  description = "Path to your GCP service account credentials JSON file"
  default     = "../keys/keyfile.json"
}

variable "region" {
  description = "Your project region"
  default     = "us-central1"
}

variable "stg_bq_dataset" {
  description = "BigQuery dataset ID"
  default     = "my_dataset"
}

variable "location" {
  description = "Storage location for GCS bucket and BigQuery dataset"
  default     = "US"
}

variable "bucket" {
  description = "Name of your GCS bucket. Must be globally unique across GCP"
}
