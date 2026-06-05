# Create Gemini API key via Terraform
resource "google_apikeys_key" "gemini_key" {
  name         = "gemini-api-key"
  display_name = "Gemini API Key for SRE Benjamin"
  project      = var.project_id

  restrictions {
    api_targets {
      service = "generativelanguage.googleapis.com"
      methods = ["*"]
    }
  }
}

# Create Secret in Secret Manager
resource "google_secret_manager_secret" "gemini_api_key_secret" {
  secret_id = "gemini-api-key"
  project   = var.project_id
  replication {
    auto {}
  }
}

# Add Version to Secret containing the API Key string
resource "google_secret_manager_secret_version" "gemini_api_key_version" {
  secret      = google_secret_manager_secret.gemini_api_key_secret.id
  secret_data = google_apikeys_key.gemini_key.key_string
}

# Grant the Cloud Run service account permission to read secrets in the project
resource "google_project_iam_member" "sre_agent_secret_accessor_project" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.sre_runner.email}"
}

# Grant the SRE Investigator service account permission to read secrets in the project
resource "google_project_iam_member" "sre_agent_secret_accessor_investigator" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:safe-sre-investigator@${var.project_id}.iam.gserviceaccount.com"
}

# Grant the developer user permission to read secrets in the project
resource "google_project_iam_member" "sre_agent_secret_accessor_user" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "user:ricc@gcp.altostrat.com"
}
