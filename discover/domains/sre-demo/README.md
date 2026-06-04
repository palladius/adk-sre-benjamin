# SRE Demo Domain Documentation

Welcome to the **SRE Demo Domain** workspace. This domain functions as a sandbox and demonstration environment for testing and staging SRE processes, vulnerability auditing, automated playbooks, and on-call drills within the Project Benjamin framework.

---

## 🔍 Domain Overview & Introduction
The SRE Demo Domain serves as the primary testing ground for our automated SRE agent, diagnostics simulator, and vulnerability scanners. By staging resources under a dedicated domain, we can safely simulate service failures, perform structural network mapping, test logging capabilities, and run incident response drill exercises without impacting live production services.

---

## ⚙️ GCP Target Project Details: `sre-next`
The SRE Demo Domain primarily targets and analyzes the resource profile of the Google Cloud Project **`sre-next`**.

### Current Audit Findings Summary
An executive SRE audit of the `sre-next` project revealed that **12 out of 16 analyzed assets** are currently flagged with configuration vulnerabilities or public exposure. 

### Target Resource Catalog
| Resource Name | Resource Type | Location | Status | SRE Audit Warning / Status |
| --- | --- | --- | --- | --- |
| `lab-setup` | Compute VM | `us-central1-a` | `RUNNING` | **⚠️ EXPOSED**: Bound to public IP `35.232.121.228` |
| `sre-agent-service` | Cloud Run | `us-central1` | `READY` | **✅ SAFE**: Not publicly accessible without authorization |
| `online-boutique` | GKE Cluster | `us-central1` | `RUNNING` | **⚠️ EXPOSED**: Public GKE control plane endpoint access enabled (`34.9.73.164`) |
| `online-boutique-standard` | GKE Cluster | `us-central1` | `RUNNING` | **⚠️ EXPOSED**: Public GKE control plane endpoint access enabled (`136.119.135.4`) |
| `sre-postgres` | Cloud SQL | `us-central1` | `RUNNABLE` | **✅ SAFE**: Private IP only, public IP disabled |
| `agent-staging-bucket-sre-next` | GCS Bucket | `US-CENTRAL1` | `ACTIVE` | **⚠️ EXPOSED**: Uniform bucket public access prevention is not enforced |
| `sre-agent-investigations-sre-next` | GCS Bucket | `US-CENTRAL1` | `ACTIVE` | **⚠️ EXPOSED**: Uniform bucket public access prevention is not enforced |

---

## 📖 SRE Playbook Guidelines
These playbooks document the recommended procedures for investigating and mitigating the primary exposures discovered in the `sre-next` target project.

### Playbook 1: exposed VM Instance Public IP
**Alert Condition**: Compute VM `lab-setup` is bound to an ephemeral or static external IP.
1. **Audit/Verification**:
   ```bash
   gcloud compute instances describe lab-setup --zone us-central1-a \
     --format="value(networkInterfaces[0].accessConfigs[0].natIP)"
   ```
2. **Mitigation**:
   * Determine if external traffic is necessary. If not, remove the access configuration:
     ```bash
     gcloud compute instances delete-access-config lab-setup --zone us-central1-a \
       --access-config-name="external-nat"
     ```
   * Set up an Identity-Aware Proxy (IAP) tunnel for secure administrative SSH access.

### Playbook 2: Public GKE Control Plane Endpoint
**Alert Condition**: GKE control plane allows public access.
1. **Audit/Verification**:
   ```bash
   gcloud container clusters describe online-boutique --zone us-central1 \
     --format="value(privateClusterConfig.enablePrivateEndpoint)"
   ```
2. **Mitigation**:
   * Restrict access by enabling authorized networks:
     ```bash
     gcloud container clusters update online-boutique --zone us-central1 \
       --enable-master-authorized-networks \
       --master-authorized-networks 10.0.0.0/8
     ```
   * Transition the cluster to a private endpoint setup if direct public access is no longer required.

### Playbook 3: GCS Public Access Prevention (PAP) Inherited
**Alert Condition**: Uniform bucket public access prevention is not enforced on critical staging or audit buckets.
1. **Audit/Verification**:
   ```bash
   gcloud storage buckets describe gs://agent-staging-bucket-sre-next \
     --format="value(iamConfiguration.publicAccessPrevention)"
   ```
2. **Mitigation**:
   * Force the bucket's Public Access Prevention setting to `enforced`:
     ```bash
     gcloud storage buckets update gs://agent-staging-bucket-sre-next \
       --public-access-prevention
     ```

---

## 🚨 On-Call Instructions
In the event of an automated audit alert or suspected compromise:

### Escalation Path
1. **Primary On-Call SRE**: `sre-oncall@example.com`
2. **Secondary Escalation**: Lead Architect
3. **Security Incident Contact**: `security-alerts@example.com`

### Incident Investigation Checklist
- [ ] Retrieve logs for the affected resource using the `query_logs` tool or Cloud Logging.
- [ ] Determine if the vulnerability was actively exploited (e.g., unauthorized network access, unfamiliar SSH connections).
- [ ] Apply the corresponding Playbook mitigation steps.
- [ ] Trigger a manual discovery audit run to verify that the resource status transitions to `✅ SAFE`.
