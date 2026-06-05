# GCP Resource Catalog: sre-next-prod
Auto-generated on **2026-06-05 11:09:18 UTC** by Project Benjamin SRE Discovery Engine.

## Executive SRE Audit Summary
🚨 **VULNERABILITY WARNING**: Found **1** exposed/vulnerable resources out of **3** analyzed assets. Action required!

## Discovered Resource Catalog
| Type | Name | Location | Status | Audit Warning |
| --- | --- | --- | --- | --- |
| ☸️ GKE Cluster | `online-boutique-prod` | `us-central1` | `RUNNING` | **⚠️ EXPOSED: Public GKE control plane endpoint access enabled** |
| 🪣 GCS Bucket | `test-riccardo-demo-sre` | `EU` | `ACTIVE` | ✅ SAFE |
| 🌐 VPC Network | `online-boutique-prod-vpc` | `global` | `ACTIVE` | ✅ SAFE |

## Detailed Resource Metadata
### `online-boutique-prod` (gke_cluster)
- **Location**: `us-central1`
- **Status**: `RUNNING`
- **Audited Vulnerable**: `True`
- **Audit Warning**: **⚠️ EXPOSED: Public GKE control plane endpoint access enabled**
- **Metadata Details**:
  ```json
{
      "endpoint": "34.121.227.243",
      "private_cluster": false
  }
  ```
### `test-riccardo-demo-sre` (gcs_bucket)
- **Location**: `EU`
- **Status**: `ACTIVE`
- **Audited Vulnerable**: `False`
- **Metadata Details**:
  ```json
{
      "public_access_prevention": "enforced",
      "storage_class": "STANDARD",
      "uniform_bucket_level_access": true
  }
  ```
### `online-boutique-prod-vpc` (vpc_network)
- **Location**: `global`
- **Status**: `ACTIVE`
- **Audited Vulnerable**: `False`
- **Metadata Details**:
  ```json
{
      "auto_create_subnetworks": false,
      "subnetworks": [
          "online-boutique-prod-subnet"
      ],
      "routing_mode": "REGIONAL"
  }
  ```