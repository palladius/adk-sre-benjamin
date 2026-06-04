variable "project_id" {
  type        = string
  description = "The GCP Project ID where resources will be deployed."
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "The GCP Region to deploy the Cloud Run service."
}

variable "image" {
  type        = string
  description = "The container image URL to deploy to Cloud Run."
}

variable "web_username" {
  type        = string
  default     = ""
  description = "The optional username for L7 Basic Authentication."
}

variable "web_password" {
  type        = string
  default     = ""
  sensitive   = true
  description = "The optional password for L7 Basic Authentication."
}

variable "gemini_api_key" {
  type        = string
  default     = ""
  sensitive   = true
  description = "The Gemini API Key to enable agent reasoning loops."
}

variable "default_gemini_model" {
  type        = string
  default     = "gemini-3.1-flash-lite"
  description = "The default Gemini model identifier for the agents."
}

variable "gcloud_identity" {
  type        = string
  default     = ""
  description = "The authorized Google user email for Identity-Aware Proxy (IAP) L7 check."
}

