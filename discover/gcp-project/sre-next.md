# GCP Resource Catalog: sre-next
Auto-generated on **2026-06-02 06:21:13 UTC** by Project Benjamin SRE Discovery Engine.

## Executive SRE Audit Summary
🚨 **VULNERABILITY WARNING**: Found **10** exposed/vulnerable resources out of **12** analyzed assets. Action required!

## Discovered Resource Catalog
| Type | Name | Location | Status | Audit Warning |
| --- | --- | --- | --- | --- |
| 🖥️ Compute VM | `gke-online-boutique-standar-main-pool-3db4c871-sj94` | `us-central1-a` | `RUNNING` | **⚠️ EXPOSED: Bound to public IP 34.57.66.211** |
| 🖥️ Compute VM | `gke-online-boutique-standar-main-pool-8d1a34a4-hznq` | `us-central1-c` | `RUNNING` | **⚠️ EXPOSED: Bound to public IP 136.113.42.55** |
| 🖥️ Compute VM | `gke-online-boutique-standar-main-pool-5f5faafb-zx3d` | `us-central1-f` | `RUNNING` | **⚠️ EXPOSED: Bound to public IP 35.238.28.179** |
| ☸️ GKE Cluster | `online-boutique` | `us-central1` | `RUNNING` | **⚠️ EXPOSED: Public GKE control plane endpoint access enabled** |
| ☸️ GKE Cluster | `online-boutique-standard` | `us-central1` | `RUNNING` | **⚠️ EXPOSED: Public GKE control plane endpoint access enabled** |
| 🪣 GCS Bucket | `gcf-v2-sources-353539023891-us-central1` | `US-CENTRAL1` | `ACTIVE` | **⚠️ EXPOSED: Uniform bucket public access prevention is not enforced** |
| 🪣 GCS Bucket | `gcf-v2-uploads-353539023891.us-central1.cloudfunctions.appspot.com` | `US-CENTRAL1` | `ACTIVE` | **⚠️ EXPOSED: Uniform bucket public access prevention is not enforced** |
| 🪣 GCS Bucket | `my-test-project-123-mediagen-files` | `US-CENTRAL1` | `ACTIVE` | **⚠️ EXPOSED: Uniform bucket public access prevention is not enforced** |
| 🪣 GCS Bucket | `sre-agent-staging-sre-next` | `US-CENTRAL1` | `ACTIVE` | **⚠️ EXPOSED: Uniform bucket public access prevention is not enforced** |
| 🪣 GCS Bucket | `sre-next-mediagen-files` | `US-CENTRAL1` | `ACTIVE` | **⚠️ EXPOSED: Uniform bucket public access prevention is not enforced** |
| 🌐 VPC Network | `online-boutique-standard-vpc` | `global` | `ACTIVE` | ✅ SAFE |
| 🌐 VPC Network | `online-boutique-vpc` | `global` | `ACTIVE` | ✅ SAFE |

## Detailed Resource Metadata
### `gke-online-boutique-standar-main-pool-3db4c871-sj94` (gce_vm)
- **Location**: `us-central1-a`
- **Status**: `RUNNING`
- **Audited Vulnerable**: `True`
- **Audit Warning**: **⚠️ EXPOSED: Bound to public IP 34.57.66.211**
- **Metadata Details**:
  ```json
{
      "internal_ip": "10.0.0.26",
      "external_ip": "34.57.66.211"
  }
  ```
### `gke-online-boutique-standar-main-pool-8d1a34a4-hznq` (gce_vm)
- **Location**: `us-central1-c`
- **Status**: `RUNNING`
- **Audited Vulnerable**: `True`
- **Audit Warning**: **⚠️ EXPOSED: Bound to public IP 136.113.42.55**
- **Metadata Details**:
  ```json
{
      "internal_ip": "10.0.0.27",
      "external_ip": "136.113.42.55"
  }
  ```
### `gke-online-boutique-standar-main-pool-5f5faafb-zx3d` (gce_vm)
- **Location**: `us-central1-f`
- **Status**: `RUNNING`
- **Audited Vulnerable**: `True`
- **Audit Warning**: **⚠️ EXPOSED: Bound to public IP 35.238.28.179**
- **Metadata Details**:
  ```json
{
      "internal_ip": "10.0.0.25",
      "external_ip": "35.238.28.179"
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