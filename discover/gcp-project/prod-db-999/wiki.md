# GCP Resource Catalog: prod-db-999
Auto-generated on **2026-06-02 06:20:53 UTC** by Project Benjamin SRE Discovery Engine.

## Executive SRE Audit Summary
🚨 **VULNERABILITY WARNING**: Found **5** exposed/vulnerable resources out of **11** analyzed assets. Action required!

## Discovered Resource Catalog
| Type | Name | Location | Status | Audit Warning |
| --- | --- | --- | --- | --- |
| 🖥️ Compute VM | `web-frontend-vm` | `us-central1-a` | `RUNNING` | **⚠️ EXPOSED: Bound to public IP 34.122.90.10** |
| 🖥️ Compute VM | `internal-db-vm` | `us-central1-a` | `RUNNING` | ✅ SAFE |
| 🏃 Cloud Run | `public-api-service` | `us-central1` | `READY` | **⚠️ EXPOSED: Unauthenticated public access (allUsers invoker)** |
| 🏃 Cloud Run | `secure-backend-service` | `us-central1` | `READY` | ✅ SAFE |
| ☸️ GKE Cluster | `gke-public-cluster` | `us-central1` | `RUNNING` | **⚠️ EXPOSED: Public GKE control plane endpoint access enabled** |
| ☸️ GKE Cluster | `gke-private-cluster` | `us-central1` | `RUNNING` | ✅ SAFE |
| 💾 Cloud SQL | `customer-db-sql` | `us-central1` | `RUNNING` | **⚠️ EXPOSED: Public IP enabled with no authorized networks restrictions** |
| 💾 Cloud SQL | `secure-vault-sql` | `us-central1` | `RUNNING` | ✅ SAFE |
| 🪣 GCS Bucket | `generic-backup-bucket` | `US` | `ACTIVE` | ✅ SAFE |
| 🪣 GCS Bucket | `exposed-logs-bucket` | `US` | `ACTIVE` | **⚠️ EXPOSED: Uniform bucket public access prevention is not enforced** |
| 🌐 VPC Network | `corporate-vpc-network` | `global` | `ACTIVE` | ✅ SAFE |

## Detailed Resource Metadata
### `web-frontend-vm` (gce_vm)
- **Location**: `us-central1-a`
- **Status**: `RUNNING`
- **Audited Vulnerable**: `True`
- **Audit Warning**: **⚠️ EXPOSED: Bound to public IP 34.122.90.10**
- **Metadata Details**:
  ```json
{
      "internal_ip": "10.128.0.2",
      "external_ip": "34.122.90.10"
  }
  ```
### `internal-db-vm` (gce_vm)
- **Location**: `us-central1-a`
- **Status**: `RUNNING`
- **Audited Vulnerable**: `False`
- **Metadata Details**:
  ```json
{
      "internal_ip": "10.128.0.3",
      "external_ip": null
  }
  ```
### `public-api-service` (cloud_run)
- **Location**: `us-central1`
- **Status**: `READY`
- **Audited Vulnerable**: `True`
- **Audit Warning**: **⚠️ EXPOSED: Unauthenticated public access (allUsers invoker)**
- **Metadata Details**:
  ```json
{
      "url": "https://public-api-service-xq-uc.a.run.app",
      "all_users_invoker": true
  }
  ```
### `secure-backend-service` (cloud_run)
- **Location**: `us-central1`
- **Status**: `READY`
- **Audited Vulnerable**: `False`
- **Metadata Details**:
  ```json
{
      "url": "https://secure-backend-service-xq-uc.a.run.app",
      "all_users_invoker": false
  }
  ```
### `gke-public-cluster` (gke_cluster)
- **Location**: `us-central1`
- **Status**: `RUNNING`
- **Audited Vulnerable**: `True`
- **Audit Warning**: **⚠️ EXPOSED: Public GKE control plane endpoint access enabled**
- **Metadata Details**:
  ```json
{
      "endpoint": "35.224.12.80",
      "private_cluster": false
  }
  ```
### `gke-private-cluster` (gke_cluster)
- **Location**: `us-central1`
- **Status**: `RUNNING`
- **Audited Vulnerable**: `False`
- **Metadata Details**:
  ```json
{
      "endpoint": "10.128.16.2",
      "private_cluster": true
  }
  ```
### `customer-db-sql` (cloud_sql)
- **Location**: `us-central1`
- **Status**: `RUNNING`
- **Audited Vulnerable**: `True`
- **Audit Warning**: **⚠️ EXPOSED: Public IP enabled with no authorized networks restrictions**
- **Metadata Details**:
  ```json
{
      "public_ip_enabled": true,
      "authorized_networks": []
  }
  ```
### `secure-vault-sql` (cloud_sql)
- **Location**: `us-central1`
- **Status**: `RUNNING`
- **Audited Vulnerable**: `False`
- **Metadata Details**:
  ```json
{
      "public_ip_enabled": false,
      "authorized_networks": []
  }
  ```
### `generic-backup-bucket` (gcs_bucket)
- **Location**: `US`
- **Status**: `ACTIVE`
- **Audited Vulnerable**: `False`
- **Metadata Details**:
  ```json
{
      "public_access_prevention": "enforced",
      "storage_class": "NEARLINE",
      "uniform_bucket_level_access": true
  }
  ```
### `exposed-logs-bucket` (gcs_bucket)
- **Location**: `US`
- **Status**: `ACTIVE`
- **Audited Vulnerable**: `True`
- **Audit Warning**: **⚠️ EXPOSED: Uniform bucket public access prevention is not enforced**
- **Metadata Details**:
  ```json
{
      "public_access_prevention": "inherited",
      "storage_class": "STANDARD",
      "uniform_bucket_level_access": false
  }
  ```
### `corporate-vpc-network` (vpc_network)
- **Location**: `global`
- **Status**: `ACTIVE`
- **Audited Vulnerable**: `False`
- **Metadata Details**:
  ```json
{
      "auto_create_subnetworks": false,
      "subnetworks": [
          "corp-subnet-1"
      ],
      "routing_mode": "GLOBAL"
  }
  ```