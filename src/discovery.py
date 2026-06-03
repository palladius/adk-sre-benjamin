import os
import json
import subprocess
from datetime import datetime, timezone
from src.incident import get_discover_dir

def discover_project_resources(project_id: str) -> str:
    """Discovers GCP resources, audits them for vulnerabilities, 
    persists results to discover/gcp-project/<project_id>.json, 
    and compiles a Markdown index at discover/gcp-project/<project_id>.md.
    """
    mock_tooling = os.getenv("MOCK_TOOLING", "false").lower() == "true"
    resources = []
    
    # We will generate mock resources list so we have it handy for mock mode or live mode fallback
    if project_id == "sre-next":
        mock_resources = [
            # Compute Engine VMs
            {
                "name": "frontend-vm",
                "type": "gce_vm",
                "location": "us-central1-a",
                "status": "RUNNING",
                "vulnerable": True,
                "warning": "⚠️ EXPOSED: Bound to public IP 34.135.120.45",
                "console_url": f"https://console.cloud.google.com/compute/instancesDetail/zones/us-central1-a/instances/frontend-vm?project={project_id}",
                "is_mock": True,
                "metadata": {
                    "internal_ip": "10.128.0.5",
                    "external_ip": "34.135.120.45"
                }
            },
            {
                "name": "checkout-vm",
                "type": "gce_vm",
                "location": "us-central1-b",
                "status": "RUNNING",
                "vulnerable": False,
                "warning": None,
                "console_url": f"https://console.cloud.google.com/compute/instancesDetail/zones/us-central1-b/instances/checkout-vm?project={project_id}",
                "is_mock": True,
                "metadata": {
                    "internal_ip": "10.128.0.6",
                    "external_ip": None
                }
            },
            # Cloud Run Services
            {
                "name": "email-service",
                "type": "cloud_run",
                "location": "us-central1",
                "status": "READY",
                "vulnerable": True,
                "warning": "⚠️ EXPOSED: Unauthenticated public access (allUsers invoker)",
                "console_url": f"https://console.cloud.google.com/run/detail/us-central1/email-service/metrics?project={project_id}",
                "is_mock": True,
                "metadata": {
                    "url": "https://email-service-xq-uc.a.run.app",
                    "all_users_invoker": True
                }
            },
            {
                "name": "payment-service",
                "type": "cloud_run",
                "location": "us-central1",
                "status": "READY",
                "vulnerable": False,
                "warning": None,
                "console_url": f"https://console.cloud.google.com/run/detail/us-central1/payment-service/metrics?project={project_id}",
                "is_mock": True,
                "metadata": {
                    "url": "https://payment-service-xq-uc.a.run.app",
                    "all_users_invoker": False
                }
            },
            # GKE Clusters
            {
                "name": "online-boutique",
                "type": "gke_cluster",
                "location": "us-central1",
                "status": "RUNNING",
                "vulnerable": True,
                "warning": "⚠️ EXPOSED: Public GKE control plane endpoint access enabled",
                "console_url": f"https://console.cloud.google.com/kubernetes/clusters/details/us-central1/online-boutique/overview?project={project_id}",
                "is_mock": True,
                "metadata": {
                    "endpoint": "35.224.12.80",
                    "private_cluster": False
                }
            },
            # Cloud SQL Database Instances
            {
                "name": "boutique-db",
                "type": "cloud_sql",
                "location": "us-central1",
                "status": "RUNNING",
                "vulnerable": True,
                "warning": "⚠️ EXPOSED: Public IP enabled with no authorized networks restrictions",
                "console_url": f"https://console.cloud.google.com/sql/instances/boutique-db/overview?project={project_id}",
                "is_mock": True,
                "metadata": {
                    "public_ip_enabled": True,
                    "authorized_networks": []
                }
            },
            # GCS Buckets
            {
                "name": "sre-next-assets-bucket",
                "type": "gcs_bucket",
                "location": "US-CENTRAL1",
                "status": "ACTIVE",
                "vulnerable": False,
                "warning": None,
                "console_url": f"https://console.cloud.google.com/storage/browser/sre-next-assets-bucket?project={project_id}",
                "is_mock": True,
                "metadata": {
                    "public_access_prevention": "enforced",
                    "storage_class": "STANDARD",
                    "uniform_bucket_level_access": True
                }
            },
            {
                "name": "public-user-uploads-bucket",
                "type": "gcs_bucket",
                "location": "US-CENTRAL1",
                "status": "ACTIVE",
                "vulnerable": True,
                "warning": "⚠️ EXPOSED: Uniform bucket public access prevention is not enforced",
                "console_url": f"https://console.cloud.google.com/storage/browser/public-user-uploads-bucket?project={project_id}",
                "is_mock": True,
                "metadata": {
                    "public_access_prevention": "inherited",
                    "storage_class": "STANDARD",
                    "uniform_bucket_level_access": False
                }
            },
            # VPC Networks
            {
                "name": "online-boutique-vpc",
                "type": "vpc_network",
                "location": "global",
                "status": "ACTIVE",
                "vulnerable": False,
                "warning": None,
                "console_url": f"https://console.cloud.google.com/networking/networks/details/online-boutique-vpc?project={project_id}",
                "is_mock": True,
                "metadata": {
                    "auto_create_subnetworks": False,
                    "subnetworks": ["online-boutique-subnet"],
                    "routing_mode": "REGIONAL"
                }
            },
            {
                "name": "default",
                "type": "vpc_network",
                "location": "global",
                "status": "ACTIVE",
                "vulnerable": True,
                "warning": "⚠️ EXPOSED: Default network contains auto-subnets and standard wide ingress firewall rules",
                "console_url": f"https://console.cloud.google.com/networking/networks/details/default?project={project_id}",
                "is_mock": True,
                "metadata": {
                    "auto_create_subnetworks": True,
                    "subnetworks": ["default-subnet-us-central1", "default-subnet-us-east1"],
                    "routing_mode": "REGIONAL"
                }
            }
        ]
    else:
        mock_resources = [
            # Compute Engine VMs
            {
                "name": "web-frontend-vm",
                "type": "gce_vm",
                "location": "us-central1-a",
                "status": "RUNNING",
                "vulnerable": True,
                "warning": "⚠️ EXPOSED: Bound to public IP 34.122.90.10",
                "console_url": f"https://console.cloud.google.com/compute/instancesDetail/zones/us-central1-a/instances/web-frontend-vm?project={project_id}",
                "is_mock": True,
                "metadata": {
                    "internal_ip": "10.128.0.2",
                    "external_ip": "34.122.90.10"
                }
            },
            {
                "name": "internal-db-vm",
                "type": "gce_vm",
                "location": "us-central1-a",
                "status": "RUNNING",
                "vulnerable": False,
                "warning": None,
                "console_url": f"https://console.cloud.google.com/compute/instancesDetail/zones/us-central1-a/instances/internal-db-vm?project={project_id}",
                "is_mock": True,
                "metadata": {
                    "internal_ip": "10.128.0.3",
                    "external_ip": None
                }
            },
            # Cloud Run Services
            {
                "name": "public-api-service",
                "type": "cloud_run",
                "location": "us-central1",
                "status": "READY",
                "vulnerable": True,
                "warning": "⚠️ EXPOSED: Unauthenticated public access (allUsers invoker)",
                "console_url": f"https://console.cloud.google.com/run/detail/us-central1/public-api-service/metrics?project={project_id}",
                "is_mock": True,
                "metadata": {
                    "url": "https://public-api-service-xq-uc.a.run.app",
                    "all_users_invoker": True
                }
            },
            {
                "name": "secure-backend-service",
                "type": "cloud_run",
                "location": "us-central1",
                "status": "READY",
                "vulnerable": False,
                "warning": None,
                "console_url": f"https://console.cloud.google.com/run/detail/us-central1/secure-backend-service/metrics?project={project_id}",
                "is_mock": True,
                "metadata": {
                    "url": "https://secure-backend-service-xq-uc.a.run.app",
                    "all_users_invoker": False
                }
            },
            # GKE Clusters
            {
                "name": "gke-public-cluster",
                "type": "gke_cluster",
                "location": "us-central1",
                "status": "RUNNING",
                "vulnerable": True,
                "warning": "⚠️ EXPOSED: Public GKE control plane endpoint access enabled",
                "console_url": f"https://console.cloud.google.com/kubernetes/clusters/details/us-central1/gke-public-cluster/overview?project={project_id}",
                "is_mock": True,
                "metadata": {
                    "endpoint": "35.224.12.80",
                    "private_cluster": False
                }
            },
            {
                "name": "gke-private-cluster",
                "type": "gke_cluster",
                "location": "us-central1",
                "status": "RUNNING",
                "vulnerable": False,
                "warning": None,
                "console_url": f"https://console.cloud.google.com/kubernetes/clusters/details/us-central1/gke-private-cluster/overview?project={project_id}",
                "is_mock": True,
                "metadata": {
                    "endpoint": "10.128.16.2",
                    "private_cluster": True
                }
            },
            # Cloud SQL Database Instances
            {
                "name": "customer-db-sql",
                "type": "cloud_sql",
                "location": "us-central1",
                "status": "RUNNING",
                "vulnerable": True,
                "warning": "⚠️ EXPOSED: Public IP enabled with no authorized networks restrictions",
                "console_url": f"https://console.cloud.google.com/sql/instances/customer-db-sql/overview?project={project_id}",
                "is_mock": True,
                "metadata": {
                    "public_ip_enabled": True,
                    "authorized_networks": []
                }
            },
            {
                "name": "secure-vault-sql",
                "type": "cloud_sql",
                "location": "us-central1",
                "status": "RUNNING",
                "vulnerable": False,
                "warning": None,
                "console_url": f"https://console.cloud.google.com/sql/instances/secure-vault-sql/overview?project={project_id}",
                "is_mock": True,
                "metadata": {
                    "public_ip_enabled": False,
                    "authorized_networks": []
                }
            },
            # GCS Buckets
            {
                "name": "generic-backup-bucket",
                "type": "gcs_bucket",
                "location": "US",
                "status": "ACTIVE",
                "vulnerable": False,
                "warning": None,
                "console_url": f"https://console.cloud.google.com/storage/browser/generic-backup-bucket?project={project_id}",
                "is_mock": True,
                "metadata": {
                    "public_access_prevention": "enforced",
                    "storage_class": "NEARLINE",
                    "uniform_bucket_level_access": True
                }
            },
            {
                "name": "exposed-logs-bucket",
                "type": "gcs_bucket",
                "location": "US",
                "status": "ACTIVE",
                "vulnerable": True,
                "warning": "⚠️ EXPOSED: Uniform bucket public access prevention is not enforced",
                "console_url": f"https://console.cloud.google.com/storage/browser/exposed-logs-bucket?project={project_id}",
                "is_mock": True,
                "metadata": {
                    "public_access_prevention": "inherited",
                    "storage_class": "STANDARD",
                    "uniform_bucket_level_access": False
                }
            },
            # VPC Networks
            {
                "name": "corporate-vpc-network",
                "type": "vpc_network",
                "location": "global",
                "status": "ACTIVE",
                "vulnerable": False,
                "warning": None,
                "console_url": f"https://console.cloud.google.com/networking/networks/details/corporate-vpc-network?project={project_id}",
                "is_mock": True,
                "metadata": {
                    "auto_create_subnetworks": False,
                    "subnetworks": ["corp-subnet-1"],
                    "routing_mode": "GLOBAL"
                }
            }
        ]

    use_live = (not mock_tooling) or (project_id == "sre-next")

    # Temporarily override service account impersonation for other projects during live discovery
    original_sdk_impersonate = os.environ.get("CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT")
    if use_live and project_id != "sre-next":
        os.environ["CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT"] = ""

    if not use_live:
        resources = mock_resources
    else:
        # Live gcloud subprocess commands inheriting active SA context securely
        # 1. Discover GCE VMs
        try:
            cmd = ["gcloud", "compute", "instances", "list", f"--project={project_id}", "--format=json"]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            vms_data = json.loads(res.stdout)
            for vm in vms_data:
                name = vm.get("name")
                if not name:
                    continue
                # Skip 'boring' helper VMs (GKE system node pools, Dataproc cluster nodes)
                if name.startswith("gke-") or "dataproc" in name.lower():
                    continue
                status = vm.get("status")
                zone = vm.get("zone", "").split("/")[-1]
                
                external_ip = None
                internal_ip = None
                vulnerable = False
                warning = None
                
                for interface in vm.get("networkInterfaces", []):
                    internal_ip = interface.get("networkIP")
                    for access_config in interface.get("accessConfigs", []):
                        if access_config.get("natIP"):
                            external_ip = access_config.get("natIP")
                            vulnerable = True
                            warning = f"⚠️ EXPOSED: Bound to public IP {external_ip}"
                            
                resources.append({
                    "name": name,
                    "type": "gce_vm",
                    "location": zone,
                    "status": status,
                    "vulnerable": vulnerable,
                    "warning": warning,
                    "console_url": f"https://console.cloud.google.com/compute/instancesDetail/zones/{zone}/instances/{name}?project={project_id}",
                    "is_mock": False,
                    "metadata": {
                        "internal_ip": internal_ip,
                        "external_ip": external_ip
                    }
                })
        except Exception as e:
            print(f"Failed to crawl GCE VMs: {e}")
            
        # 2. Discover Cloud Run Services
        try:
            cmd = ["gcloud", "run", "services", "list", f"--project={project_id}", "--format=json"]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            run_data = json.loads(res.stdout)
            for service in run_data:
                name = service.get("metadata", {}).get("name")
                region = service.get("metadata", {}).get("labels", {}).get("cloud.googleapis.com/location", "unknown")
                status = "READY"
                url = service.get("status", {}).get("url")
                
                vulnerable = False
                warning = None
                all_users_invoker = False
                try:
                    iam_cmd = ["gcloud", "run", "services", "get-iam-policy", name, f"--project={project_id}", f"--region={region}", "--format=json"]
                    iam_res = subprocess.run(iam_cmd, capture_output=True, text=True, check=True)
                    iam_data = json.loads(iam_res.stdout)
                    for binding in iam_data.get("bindings", []):
                        if binding.get("role") == "roles/run.invoker":
                            if "allUsers" in binding.get("members", []):
                                vulnerable = True
                                all_users_invoker = True
                                warning = "⚠️ EXPOSED: Unauthenticated public access (allUsers invoker)"
                except Exception as iam_err:
                    print(f"Failed to fetch IAM policy for service {name}: {iam_err}")
                
                resources.append({
                    "name": name,
                    "type": "cloud_run",
                    "location": region,
                    "status": status,
                    "vulnerable": vulnerable,
                    "warning": warning,
                    "console_url": f"https://console.cloud.google.com/run/detail/{region}/{name}/metrics?project={project_id}",
                    "is_mock": False,
                    "metadata": {
                        "url": url,
                        "all_users_invoker": all_users_invoker
                    }
                })
        except Exception as e:
            print(f"Failed to crawl Cloud Run Services: {e}")
            
        # 3. Discover GKE Clusters
        try:
            cmd = ["gcloud", "container", "clusters", "list", f"--project={project_id}", "--format=json"]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            gke_data = json.loads(res.stdout)
            for cluster in gke_data:
                name = cluster.get("name")
                location = cluster.get("location")
                status = cluster.get("status")
                endpoint = cluster.get("endpoint")
                
                vulnerable = True
                warning = "⚠️ EXPOSED: Public GKE control plane endpoint access enabled"
                private_cluster = False
                
                private_config = cluster.get("privateClusterConfig")
                if private_config:
                    if private_config.get("enablePrivateEndpoint") == True:
                        vulnerable = False
                        warning = None
                        private_cluster = True
                
                resources.append({
                    "name": name,
                    "type": "gke_cluster",
                    "location": location,
                    "status": status,
                    "vulnerable": vulnerable,
                    "warning": warning,
                    "console_url": f"https://console.cloud.google.com/kubernetes/clusters/details/{location}/{name}/overview?project={project_id}",
                    "is_mock": False,
                    "metadata": {
                        "endpoint": endpoint,
                        "private_cluster": private_cluster
                    }
                })
        except Exception as e:
            print(f"Failed to crawl GKE Clusters: {e}")
            
        # 4. Discover Cloud SQL Instances
        try:
            cmd = ["gcloud", "sql", "instances", "list", f"--project={project_id}", "--format=json"]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            sql_data = json.loads(res.stdout)
            for instance in sql_data:
                name = instance.get("name")
                region = instance.get("region")
                status = instance.get("state")
                
                vulnerable = False
                warning = None
                public_ip_enabled = False
                authorized_networks = []
                
                settings = instance.get("settings", {})
                ip_config = settings.get("ipConfiguration", {})
                if ip_config:
                    public_ip_enabled = ip_config.get("ipv4Enabled", False)
                    authorized_networks = ip_config.get("authorizedNetworks", [])
                    if public_ip_enabled:
                        if not authorized_networks:
                            vulnerable = True
                            warning = "⚠️ EXPOSED: Public IP enabled with no authorized networks restrictions"
                            
                resources.append({
                    "name": name,
                    "type": "cloud_sql",
                    "location": region,
                    "status": status,
                    "vulnerable": vulnerable,
                    "warning": warning,
                    "console_url": f"https://console.cloud.google.com/sql/instances/{name}/overview?project={project_id}",
                    "is_mock": False,
                    "metadata": {
                        "public_ip_enabled": public_ip_enabled,
                        "authorized_networks": [net.get("value") for net in authorized_networks] if authorized_networks else []
                    }
                })
        except Exception as e:
            print(f"Failed to crawl Cloud SQL Instances: {e}")
            
        # 5. Discover GCS Buckets
        try:
            cmd = ["gcloud", "storage", "buckets", "list", f"--project={project_id}", "--format=json"]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            buckets_data = json.loads(res.stdout)
            for bucket in buckets_data:
                name = bucket.get("name")
                loc = bucket.get("location", "us-central1")
                pap = bucket.get("public_access_prevention", "inherited")
                
                vulnerable = pap != "enforced"
                warning = "⚠️ EXPOSED: Uniform bucket public access prevention is not enforced" if vulnerable else None
                
                resources.append({
                    "name": name,
                    "type": "gcs_bucket",
                    "location": loc,
                    "status": "ACTIVE",
                    "vulnerable": vulnerable,
                    "warning": warning,
                    "console_url": f"https://console.cloud.google.com/storage/browser/{name}?project={project_id}",
                    "is_mock": False,
                    "metadata": {
                        "public_access_prevention": pap,
                        "storage_class": bucket.get("default_storage_class", "STANDARD"),
                        "uniform_bucket_level_access": bucket.get("uniform_bucket_level_access", True)
                    }
                })
        except Exception as e:
            print(f"Failed to crawl GCS Buckets: {e}")
            
        # 6. Discover VPC Networks
        try:
            cmd = ["gcloud", "compute", "networks", "list", f"--project={project_id}", "--format=json"]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            networks_data = json.loads(res.stdout)
            for net in networks_data:
                name = net.get("name")
                auto_subnets = net.get("autoCreateSubnetworks", False)
                
                vulnerable = name == "default" or auto_subnets
                warning = "⚠️ EXPOSED: Default network contains auto-subnets and standard wide ingress firewall rules" if vulnerable else None
                
                subnets = [s.split("/")[-1] for s in net.get("subnetworks", [])]
                
                resources.append({
                    "name": name,
                    "type": "vpc_network",
                    "location": "global",
                    "status": "ACTIVE",
                    "vulnerable": vulnerable,
                    "warning": warning,
                    "console_url": f"https://console.cloud.google.com/networking/networks/details/{name}?project={project_id}",
                    "is_mock": False,
                    "metadata": {
                        "auto_create_subnetworks": auto_subnets,
                        "subnetworks": subnets,
                        "routing_mode": net.get("routingConfig", {}).get("routingMode", "REGIONAL")
                    }
                })
        except Exception as e:
            print(f"Failed to crawl VPC Networks: {e}")

        # Fallback to mock data if live discovery returned nothing (e.g. gcloud errors, no permission, no assets)
        if not resources:
            print(f"Live discovery returned 0 resources for project {project_id} (e.g. not logged in, no project, or no assets). Falling back to mock data.")
            resources = mock_resources

    # Restore service account impersonation setting if it was overridden
    if use_live and project_id != "sre-next":
        if original_sdk_impersonate is not None:
            os.environ["CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT"] = original_sdk_impersonate
        else:
            os.environ.pop("CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT", None)

    # Build the deterministic directory paths and save JSON cache and Markdown Wiki
    cache_dir = os.path.join(get_discover_dir(), "gcp-project", project_id)
    os.makedirs(cache_dir, exist_ok=True)
    
    json_path = os.path.join(cache_dir, "discover.json")
        
    md_path = os.path.join(cache_dir, "wiki.md")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Generate beautiful index page with bold red warning flags
    md_lines = []
    md_lines.append(f"# GCP Resource Catalog: {project_id}")
    md_lines.append(f"Auto-generated on **{timestamp}** by Project Benjamin SRE Discovery Engine.\n")
    md_lines.append("## Executive SRE Audit Summary")
    
    total_resources = len(resources)
    vulnerable_resources = sum(1 for r in resources if r["vulnerable"])
    
    if vulnerable_resources > 0:
        md_lines.append(f"🚨 **VULNERABILITY WARNING**: Found **{vulnerable_resources}** exposed/vulnerable resources out of **{total_resources}** analyzed assets. Action required!\n")
    else:
        md_lines.append(f"✅ All **{total_resources}** analyzed GCP assets are compliant with default security boundaries.\n")
        
    md_lines.append("## Discovered Resource Catalog")
    md_lines.append("| Type | Name | Location | Status | Audit Warning |")
    md_lines.append("| --- | --- | --- | --- | --- |")
    
    type_icons = {
        "gce_vm": "🖥️ Compute VM",
        "cloud_run": "🏃 Cloud Run",
        "gke_cluster": "☸️ GKE Cluster",
        "cloud_sql": "💾 Cloud SQL",
        "gcs_bucket": "🪣 GCS Bucket",
        "vpc_network": "🌐 VPC Network"
    }
    
    for r in resources:
        icon_type = type_icons.get(r["type"], r["type"])
        warning_str = f"**{r['warning']}**" if r["vulnerable"] else "✅ SAFE"
        md_lines.append(f"| {icon_type} | `{r['name']}` | `{r['location']}` | `{r['status']}` | {warning_str} |")
        
    md_lines.append("\n## Detailed Resource Metadata")
    for r in resources:
        md_lines.append(f"### `{r['name']}` ({r['type']})")
        md_lines.append(f"- **Location**: `{r['location']}`")
        md_lines.append(f"- **Status**: `{r['status']}`")
        md_lines.append(f"- **Audited Vulnerable**: `{r['vulnerable']}`")
        if r["warning"]:
            md_lines.append(f"- **Audit Warning**: **{r['warning']}**")
        md_lines.append("- **Metadata Details**:")
        md_lines.append("  ```json")
        md_lines.append(json.dumps(r["metadata"], indent=4).replace("\n", "\n  "))
        md_lines.append("  ```")
        
    # Standard SRE Runbooks & Remediation Templates
    md_lines.append("\n## Standard SRE Runbooks & Remediation Templates\n")
    md_lines.append("### 1. GKE Control Plane Public Endpoint Remediation Runbook")
    md_lines.append("If a GKE cluster is flagged as **⚠️ EXPOSED (Public GKE control plane endpoint access enabled)**, follow these steps to secure the API server:")
    md_lines.append("- **Action A: Enable Master Authorized Networks (Recommended)**")
    md_lines.append("  Restrict access to the Kubernetes control plane to specific trusted source IPs or corporate CIDR ranges:")
    md_lines.append("  ```bash")
    md_lines.append("  gcloud container clusters update <CLUSTER_NAME> \\")
    md_lines.append("      --zone=<ZONE_OR_REGION> \\")
    md_lines.append("      --enable-master-authorized-networks \\")
    md_lines.append("      --master-authorized-networks=<TRUSTED_CIDR_1>,<TRUSTED_CIDR_2>")
    md_lines.append("  ```")
    md_lines.append("- **Action B: Convert to Private Endpoint Only**")
    md_lines.append("  Disable public control plane access entirely, forcing all traffic to transit a private endpoint inside your VPC:")
    md_lines.append("  ```bash")
    md_lines.append("  gcloud container clusters update <CLUSTER_NAME> \\")
    md_lines.append("      --zone=<ZONE_OR_REGION> \\")
    md_lines.append("      --enable-private-nodes \\")
    md_lines.append("      --disable-public-endpoint")
    md_lines.append("  ```\n")

    md_lines.append("### 2. GCS Public Bucket Disclosure Runbook")
    md_lines.append("If a storage bucket is flagged as **⚠️ EXPOSED (Uniform bucket public access prevention is not enforced)**, secure bucket IAM permissions immediately:")
    md_lines.append("- **Action A: Enforce Public Access Prevention (PAP)**")
    md_lines.append("  Force the bucket to inherit or enforce public access block limits to prevent object exposure:")
    md_lines.append("  ```bash")
    md_lines.append("  gcloud storage buckets update gs://<BUCKET_NAME> \\")
    md_lines.append("      --public-access-prevention")
    md_lines.append("  ```")
    md_lines.append("- **Action B: Enforce Uniform Bucket-Level Access (UBLA)**")
    md_lines.append("  Disable legacy fine-grained ACLs and manage access strictly via IAM policies:")
    md_lines.append("  ```bash")
    md_lines.append("  gcloud storage buckets update gs://<BUCKET_NAME> \\")
    md_lines.append("      --uniform-bucket-level-access")
    md_lines.append("  ```")
    md_lines.append("- **Action C: Remove Anonymous Public Reader Bindings**")
    md_lines.append("  Remove public read permissions from allObjects/allUsers:")
    md_lines.append("  ```bash")
    md_lines.append("  gcloud storage buckets remove-iam-policy-binding gs://<BUCKET_NAME> \\")
    md_lines.append("      --member=allUsers \\")
    md_lines.append("      --role=roles/storage.objectViewer")
    md_lines.append("  ```\n")

    md_lines.append("### 3. Auto-Mode VPC Network & Wide Ingress Security Runbook")
    md_lines.append("If a network is flagged as **⚠️ EXPOSED (Default network / Auto-mode network)**, audit and secure wide ingress exposure:")
    md_lines.append("- **Action A: Switch VPC to Custom Subnet Mode (Non-Disruptive)**")
    md_lines.append("  Transition your VPC network out of auto-mode to prevent GCP from creating subnets in every region by default:")
    md_lines.append("  ```bash")
    md_lines.append("  gcloud compute networks update <NETWORK_NAME> \\")
    md_lines.append("      --switch-to-custom-subnet-mode")
    md_lines.append("  ```")
    md_lines.append("- **Action B: Audit & Delete Wide Ingress Firewall Rules**")
    md_lines.append("  Identify wide ingress permissions (e.g., 0.0.0.0/0 on sensitive ports like 22/3389/3306):")
    md_lines.append("  ```bash")
    md_lines.append("  gcloud compute firewall-rules list \\")
    md_lines.append("      --filter=\"network:<NETWORK_NAME> AND direction:INGRESS AND sourceRanges:0.0.0.0/0\"")
    md_lines.append("  ```")
    md_lines.append("  Delete default permissive rules that expose internal assets:")
    md_lines.append("  ```bash")
    md_lines.append("  gcloud compute firewall-rules delete <FIREWALL_RULE_NAME>")
    md_lines.append("  ```")

    from src.storage import get_discovery_storage
    get_discovery_storage().save_discovery(project_id, resources, "\n".join(md_lines))
        
    return json_path
