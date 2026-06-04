terraform {
  required_version = ">= 1.3.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Create SRE Runner Service Account
resource "google_service_account" "sre_runner" {
  account_id   = "sre-benjamin-runner"
  display_name = "Project Benjamin SRE Cloud Run Runner"
}

# 2. Grant IAM Roles to the Runner Service Account
resource "google_project_iam_member" "trace_agent" {
  project = var.project_id
  role    = "roles/cloudtrace.agent"
  member  = "serviceAccount:${google_service_account.sre_runner.email}"
}

resource "google_project_iam_member" "logging_viewer" {
  project = var.project_id
  role    = "roles/logging.viewer"
  member  = "serviceAccount:${google_service_account.sre_runner.email}"
}

resource "google_project_iam_member" "monitoring_viewer" {
  project = var.project_id
  role    = "roles/monitoring.viewer"
  member  = "serviceAccount:${google_service_account.sre_runner.email}"
}

resource "google_project_iam_member" "viewer" {
  project = var.project_id
  role    = "roles/viewer"
  member  = "serviceAccount:${google_service_account.sre_runner.email}"
}

data "google_project" "project" {
  project_id = var.project_id
}

# 3. Create Google Cloud Run V2 Service
resource "google_cloud_run_v2_service" "sre_dashboard" {
  name        = "sre-agent-service"
  location    = var.region
  ingress     = "INGRESS_TRAFFIC_ALL"
  iap_enabled = true

  template {
    service_account = google_service_account.sre_runner.email

    containers {
      image = var.image

      resources {
        limits = {
          cpu    = "1"
          memory = "1024Mi"
        }
      }

      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      env {
        name  = "WEB_USERNAME"
        value = var.web_username
      }

      env {
        name  = "WEB_PASSWORD"
        value = var.web_password
      }

      env {
        name  = "GEMINI_API_KEY"
        value = var.gemini_api_key
      }

      env {
        name  = "DEFAULT_GEMINI_MODEL"
        value = var.default_gemini_model
      }

      env {
        name  = "GCLOUD_IDENTITY"
        value = var.gcloud_identity
      }
    }
  }

  lifecycle {
    ignore_changes = []
  }
}

# 4. Grant Cloud Run Invoker permission to the IAP service agent
resource "google_cloud_run_v2_service_iam_member" "iap_invoker" {
  project  = google_cloud_run_v2_service.sre_dashboard.project
  location = google_cloud_run_v2_service.sre_dashboard.location
  name     = google_cloud_run_v2_service.sre_dashboard.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-iap.iam.gserviceaccount.com"
}

