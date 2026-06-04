# GCP Resource Catalog: sre-next
Auto-generated on **2026-06-04 15:42:57 UTC** by Project Benjamin SRE Discovery Engine.

## Executive SRE Audit Summary
🚨 **VULNERABILITY WARNING**: Found **12** exposed/vulnerable resources out of **16** analyzed assets. Action required!

## Discovered Resource Catalog
| Type | Name | Location | Status | Audit Warning |
| --- | --- | --- | --- | --- |
| 🖥️ Compute VM | `lab-setup` | `us-central1-a` | `RUNNING` | **⚠️ EXPOSED: Bound to public IP 35.232.121.228** |
| 🏃 Cloud Run | `sre-agent-service` | `us-central1` | `READY` | ✅ SAFE |
| ☸️ GKE Cluster | `online-boutique` | `us-central1` | `RUNNING` | **⚠️ EXPOSED: Public GKE control plane endpoint access enabled** |
| ☸️ GKE Cluster | `online-boutique-standard` | `us-central1` | `RUNNING` | **⚠️ EXPOSED: Public GKE control plane endpoint access enabled** |
| 💾 Cloud SQL | `sre-postgres` | `us-central1` | `RUNNABLE` | ✅ SAFE |
| 🪣 GCS Bucket | `agent-staging-bucket-sre-next` | `US-CENTRAL1` | `ACTIVE` | **⚠️ EXPOSED: Uniform bucket public access prevention is not enforced** |
| 🪣 GCS Bucket | `gcf-v2-sources-353539023891-us-central1` | `US-CENTRAL1` | `ACTIVE` | **⚠️ EXPOSED: Uniform bucket public access prevention is not enforced** |
| 🪣 GCS Bucket | `gcf-v2-uploads-353539023891.us-central1.cloudfunctions.appspot.com` | `US-CENTRAL1` | `ACTIVE` | **⚠️ EXPOSED: Uniform bucket public access prevention is not enforced** |
| 🪣 GCS Bucket | `my-test-project-123-mediagen-files` | `US-CENTRAL1` | `ACTIVE` | **⚠️ EXPOSED: Uniform bucket public access prevention is not enforced** |
| 🪣 GCS Bucket | `sre-agent-investigations-sre-next` | `US-CENTRAL1` | `ACTIVE` | **⚠️ EXPOSED: Uniform bucket public access prevention is not enforced** |
| 🪣 GCS Bucket | `sre-agent-staging-sre-next` | `US-CENTRAL1` | `ACTIVE` | **⚠️ EXPOSED: Uniform bucket public access prevention is not enforced** |
| 🪣 GCS Bucket | `sre-next-mediagen-files` | `US-CENTRAL1` | `ACTIVE` | **⚠️ EXPOSED: Uniform bucket public access prevention is not enforced** |
| 🪣 GCS Bucket | `sre-next-static-assets-bucket` | `US-CENTRAL1` | `ACTIVE` | **⚠️ EXPOSED: Uniform bucket public access prevention is not enforced** |
| 🪣 GCS Bucket | `sre-next_cloudbuild` | `US` | `ACTIVE` | **⚠️ EXPOSED: Uniform bucket public access prevention is not enforced** |
| 🌐 VPC Network | `online-boutique-standard-vpc` | `global` | `ACTIVE` | ✅ SAFE |
| 🌐 VPC Network | `online-boutique-vpc` | `global` | `ACTIVE` | ✅ SAFE |

## Detailed Resource Metadata
### `lab-setup` (gce_vm)
- **Location**: `us-central1-a`
- **Status**: `RUNNING`
- **Audited Vulnerable**: `True`
- **Audit Warning**: **⚠️ EXPOSED: Bound to public IP 35.232.121.228**
- **Metadata Details**:
  ```json
{
      "internal_ip": "10.0.0.9",
      "external_ip": "35.232.121.228"
  }
  ```
### `sre-agent-service` (cloud_run)
- **Location**: `us-central1`
- **Status**: `READY`
- **Audited Vulnerable**: `False`
- **Metadata Details**:
  ```json
{
      "url": "https://sre-agent-service-ha5bfv5noa-uc.a.run.app",
      "all_users_invoker": false
  }
  ```
### `online-boutique` (gke_cluster)
- **Location**: `us-central1`
- **Status**: `RUNNING`
- **Audited Vulnerable**: `True`
- **Audit Warning**: **⚠️ EXPOSED: Public GKE control plane endpoint access enabled**
- **Metadata Details**:
  ```json
{
      "endpoint": "34.9.73.164",
      "private_cluster": false
  }
  ```
### `online-boutique-standard` (gke_cluster)
- **Location**: `us-central1`
- **Status**: `RUNNING`
- **Audited Vulnerable**: `True`
- **Audit Warning**: **⚠️ EXPOSED: Public GKE control plane endpoint access enabled**
- **Metadata Details**:
  ```json
{
      "endpoint": "136.119.135.4",
      "private_cluster": false
  }
  ```
### `sre-postgres` (cloud_sql)
- **Location**: `us-central1`
- **Status**: `RUNNABLE`
- **Audited Vulnerable**: `False`
- **Metadata Details**:
  ```json
{
      "public_ip_enabled": false,
      "authorized_networks": []
  }
  ```
### `agent-staging-bucket-sre-next` (gcs_bucket)
- **Location**: `US-CENTRAL1`
- **Status**: `ACTIVE`
- **Audited Vulnerable**: `True`
- **Audit Warning**: **⚠️ EXPOSED: Uniform bucket public access prevention is not enforced**
- **Metadata Details**:
  ```json
{
      "public_access_prevention": "inherited",
      "storage_class": "STANDARD",
      "uniform_bucket_level_access": true
  }
  ```
### `gcf-v2-sources-353539023891-us-central1` (gcs_bucket)
- **Location**: `US-CENTRAL1`
- **Status**: `ACTIVE`
- **Audited Vulnerable**: `True`
- **Audit Warning**: **⚠️ EXPOSED: Uniform bucket public access prevention is not enforced**
- **Metadata Details**:
  ```json
{
      "public_access_prevention": "inherited",
      "storage_class": "STANDARD",
      "uniform_bucket_level_access": true
  }
  ```
### `gcf-v2-uploads-353539023891.us-central1.cloudfunctions.appspot.com` (gcs_bucket)
- **Location**: `US-CENTRAL1`
- **Status**: `ACTIVE`
- **Audited Vulnerable**: `True`
- **Audit Warning**: **⚠️ EXPOSED: Uniform bucket public access prevention is not enforced**
- **Metadata Details**:
  ```json
{
      "public_access_prevention": "inherited",
      "storage_class": "STANDARD",
      "uniform_bucket_level_access": true
  }
  ```
### `my-test-project-123-mediagen-files` (gcs_bucket)
- **Location**: `US-CENTRAL1`
- **Status**: `ACTIVE`
- **Audited Vulnerable**: `True`
- **Audit Warning**: **⚠️ EXPOSED: Uniform bucket public access prevention is not enforced**
- **Metadata Details**:
  ```json
{
      "public_access_prevention": "inherited",
      "storage_class": "STANDARD",
      "uniform_bucket_level_access": true
  }
  ```
### `sre-agent-investigations-sre-next` (gcs_bucket)
- **Location**: `US-CENTRAL1`
- **Status**: `ACTIVE`
- **Audited Vulnerable**: `True`
- **Audit Warning**: **⚠️ EXPOSED: Uniform bucket public access prevention is not enforced**
- **Metadata Details**:
  ```json
{
      "public_access_prevention": "inherited",
      "storage_class": "STANDARD",
      "uniform_bucket_level_access": true
  }
  ```
### `sre-agent-staging-sre-next` (gcs_bucket)
- **Location**: `US-CENTRAL1`
- **Status**: `ACTIVE`
- **Audited Vulnerable**: `True`
- **Audit Warning**: **⚠️ EXPOSED: Uniform bucket public access prevention is not enforced**
- **Metadata Details**:
  ```json
{
      "public_access_prevention": "inherited",
      "storage_class": "STANDARD",
      "uniform_bucket_level_access": true
  }
  ```
### `sre-next-mediagen-files` (gcs_bucket)
- **Location**: `US-CENTRAL1`
- **Status**: `ACTIVE`
- **Audited Vulnerable**: `True`
- **Audit Warning**: **⚠️ EXPOSED: Uniform bucket public access prevention is not enforced**
- **Metadata Details**:
  ```json
{
      "public_access_prevention": "inherited",
      "storage_class": "STANDARD",
      "uniform_bucket_level_access": true
  }
  ```
### `sre-next-static-assets-bucket` (gcs_bucket)
- **Location**: `US-CENTRAL1`
- **Status**: `ACTIVE`
- **Audited Vulnerable**: `True`
- **Audit Warning**: **⚠️ EXPOSED: Uniform bucket public access prevention is not enforced**
- **Metadata Details**:
  ```json
{
      "public_access_prevention": "inherited",
      "storage_class": "REGIONAL",
      "uniform_bucket_level_access": true
  }
  ```
### `sre-next_cloudbuild` (gcs_bucket)
- **Location**: `US`
- **Status**: `ACTIVE`
- **Audited Vulnerable**: `True`
- **Audit Warning**: **⚠️ EXPOSED: Uniform bucket public access prevention is not enforced**
- **Metadata Details**:
  ```json
{
      "public_access_prevention": "inherited",
      "storage_class": "STANDARD",
      "uniform_bucket_level_access": true
  }
  ```
### `online-boutique-standard-vpc` (vpc_network)
- **Location**: `global`
- **Status**: `ACTIVE`
- **Audited Vulnerable**: `False`
- **Metadata Details**:
  ```json
{
      "auto_create_subnetworks": false,
      "subnetworks": [
          "online-boutique-standard-subnet"
      ],
      "routing_mode": "REGIONAL"
  }
  ```
### `online-boutique-vpc` (vpc_network)
- **Location**: `global`
- **Status**: `ACTIVE`
- **Audited Vulnerable**: `False`
- **Metadata Details**:
  ```json
{
      "auto_create_subnetworks": false,
      "subnetworks": [
          "online-boutique-subnet"
      ],
      "routing_mode": "REGIONAL"
  }
  ```