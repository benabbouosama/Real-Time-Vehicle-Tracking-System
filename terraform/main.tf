terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "5.27.0"
    }
  }
}

provider "google" {
  credentials = file(var.credentials)
  project     = var.project
  region      = var.region
}

resource "google_storage_bucket" "auto-expire" {
  name          = var.bucket
  location      = var.location
  force_destroy = true

  lifecycle_rule {
    condition {
      age = 1  # Objects older than 1 day
    }
    action {
      type = "AbortIncompleteMultipartUpload"  # Abort incomplete multipart uploads
    }
  }
}

resource "google_bigquery_dataset" "my_dataset" {
  dataset_id = var.stg_bq_dataset
  location   = var.location  # Dataset location is the same as bucket location
}
