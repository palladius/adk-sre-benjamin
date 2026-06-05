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

# Create GCS Bucket for investigations
resource "google_storage_bucket" "investigations_bucket" {
  project                     = var.project_id
  name                        = "sre-agent-investigations-${var.project_id}"
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true
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
        name  = "MOCK_TOOLING"
        value = "false"
      }

      env {
        name  = "SRE_MODE"
        value = "LIVE"
      }

      env {
        name  = "DEPLOY_VERSION"
        value = "1.2.5"
      }

      env {
        name  = "DEFAULT_GEMINI_MODEL"
        value = var.default_gemini_model
      }

      env {
        name  = "GCLOUD_IDENTITY"
        value = var.gcloud_identity
      }

      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gemini_api_key_secret.secret_id
            version = "latest"
          }
        }
      }

      volume_mounts {
        name       = "investigations-volume"
        mount_path = "/workspace/investigations"
      }
    }

    volumes {
      name = "investigations-volume"
      gcs {
        bucket    = google_storage_bucket.investigations_bucket.name
        read_only = false
      }
    }
  }

  depends_on = [
    google_storage_bucket.investigations_bucket,
    google_secret_manager_secret_version.gemini_api_key_version,
    google_project_iam_member.sre_agent_secret_accessor_project,
    google_project_iam_member.sre_agent_secret_accessor_investigator,
    google_project_iam_member.sre_agent_secret_accessor_user
  ]

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

