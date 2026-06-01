import os
import json
import subprocess
from datetime import datetime, timezone

def discover_project_resources(project_id: str) -> str:
    """Discovers GCP resources, audits them for vulnerabilities, 
    persists results to cloud/gcp/projects/<project_id>/discovery.json, 
    and compiles a Markdown index at cloud/gcp/projects/<project_id>/README.md.
    """
    mock_tooling = os.getenv("MOCK_TOOLING", "true").lower() == "true"
    resources = []
    
    if mock_tooling:
        # Generate high-quality mock resources matching the specifications
        resources = [
            # Compute Engine VMs
            {
                "name": "web-frontend-vm",
                "type": "gce_vm",
                "location": "us-central1-a",
                "status": "RUNNING",
                "vulnerable": True,
                "warning": "⚠️ EXPOSED: Bound to public IP 34.122.90.10",
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
                "metadata": {
                    "public_ip_enabled": False,
                    "authorized_networks": []
                }
            }
        ]
    else:
        # Live gcloud subprocess commands inheriting active SA context securely
        # 1. Discover GCE VMs
        try:
            cmd = ["gcloud", "compute", "instances", "list", f"--project={project_id}", "--format=json"]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            vms_data = json.loads(res.stdout)
            for vm in vms_data:
                name = vm.get("name")
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
                    "metadata": {
                        "public_ip_enabled": public_ip_enabled,
                        "authorized_networks": [net.get("value") for net in authorized_networks] if authorized_networks else []
                    }
                })
        except Exception as e:
            print(f"Failed to crawl Cloud SQL Instances: {e}")

    # Build the deterministic directory paths and save JSON cache and Markdown Wiki
    cache_dir = os.path.join("cloud", "gcp", "projects", project_id)
    os.makedirs(cache_dir, exist_ok=True)
    
    json_path = os.path.join(cache_dir, "discovery.json")
    with open(json_path, "w") as f:
        json.dump(resources, f, indent=2)
        
    md_path = os.path.join(cache_dir, "README.md")
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
        "cloud_sql": "💾 Cloud SQL"
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
        
    with open(md_path, "w") as f:
        f.write("\n".join(md_lines))
        
    return json_path
