import os
import json
import shutil
import pytest
from unittest.mock import patch, MagicMock
from src.discovery import discover_project_resources
from src.cli import run_cli
from src.incident import get_discover_dir

def test_discover_mock_resources():
    project_id = "sre-next-dev"
    cache_dir = os.path.join(get_discover_dir(), "gcp-project", project_id)
    json_path = os.path.join(cache_dir, "discover.json")
    md_path = os.path.join(cache_dir, "wiki.md")
    
    # Ensure clean state
    if os.path.exists(json_path):
        os.remove(json_path)
    if os.path.exists(md_path):
        os.remove(md_path)
        
    try:
        # Enable Mock mode
        with patch.dict(os.environ, {"MOCK_TOOLING": "true"}):
            ret_json_path = discover_project_resources(project_id)
            
            assert ret_json_path == json_path
            assert os.path.exists(json_path)
            assert os.path.exists(md_path)
            
            with open(json_path, "r") as f:
                resources = json.load(f)
                
            assert len(resources) > 0
            
            # GCE VM Audit Check
            vm_vulnerable = next(r for r in resources if r["name"] == "web-frontend-vm")
            vm_safe = next(r for r in resources if r["name"] == "internal-db-vm")
            assert vm_vulnerable["vulnerable"] is True
            assert vm_safe["vulnerable"] is False
            
            # Cloud Run Audit Check
            run_vulnerable = next(r for r in resources if r["name"] == "public-api-service")
            run_safe = next(r for r in resources if r["name"] == "secure-backend-service")
            assert run_vulnerable["vulnerable"] is True
            assert run_safe["vulnerable"] is False
            
            # GKE Audit Check
            gke_vulnerable = next(r for r in resources if r["name"] == "gke-public-cluster")
            gke_safe = next(r for r in resources if r["name"] == "gke-private-cluster")
            assert gke_vulnerable["vulnerable"] is True
            assert gke_safe["vulnerable"] is False
            
            # Cloud SQL Audit Check
            sql_vulnerable = next(r for r in resources if r["name"] == "customer-db-sql")
            sql_safe = next(r for r in resources if r["name"] == "secure-vault-sql")
            assert sql_vulnerable["vulnerable"] is True
            assert sql_safe["vulnerable"] is False
            
            # Verify md_path contents
            with open(md_path, "r") as f:
                md_content = f.read()
                
            assert f"# GCP Resource Catalog: {project_id}" in md_content
            assert "⚠️ EXPOSED" in md_content
            assert "✅ SAFE" in md_content
    finally:
        if os.path.exists(json_path):
            os.remove(json_path)
        if os.path.exists(md_path):
            os.remove(md_path)

def test_discover_live_resources_mocked_subprocess():
    project_id = "live-project-abc"
    cache_dir = os.path.join(get_discover_dir(), "gcp-project", project_id)
    json_path = os.path.join(cache_dir, "discover.json")
    md_path = os.path.join(cache_dir, "wiki.md")
    
    # Ensure clean state
    if os.path.exists(json_path):
        os.remove(json_path)
    if os.path.exists(md_path):
        os.remove(md_path)
        
    try:
        # Mock subprocess outputs to replicate exact live response parsing
        mock_vm_out = json.dumps([
            {
                "name": "live-vm",
                "status": "RUNNING",
                "zone": "projects/foo/zones/us-east1-b",
                "networkInterfaces": [{
                    "networkIP": "10.0.0.4",
                    "accessConfigs": [{"natIP": "35.190.20.1"}]
                }]
            },
            {
                "name": "gke-online-boutique-prod-main-pool-12345-abcd",
                "status": "RUNNING",
                "zone": "projects/foo/zones/us-east1-b",
                "networkInterfaces": [{
                    "networkIP": "10.0.0.10",
                    "accessConfigs": []
                }]
            },
            {
                "name": "my-dataproc-w-0",
                "status": "RUNNING",
                "zone": "projects/foo/zones/us-east1-b",
                "networkInterfaces": [{
                    "networkIP": "10.0.0.11",
                    "accessConfigs": []
                }]
            }
        ])
        mock_run_out = json.dumps([{
            "metadata": {"name": "live-run-service", "labels": {"cloud.googleapis.com/location": "us-east1"}},
            "status": {"url": "https://live-run-service.a.run.app"}
        }])
        mock_run_iam_out = json.dumps({
            "bindings": [{"role": "roles/run.invoker", "members": ["allUsers"]}]
        })
        mock_gke_out = json.dumps([{
            "name": "live-gke",
            "location": "us-east1",
            "status": "RUNNING",
            "endpoint": "35.190.40.1",
            "privateClusterConfig": {"enablePrivateEndpoint": False}
        }])
        mock_sql_out = json.dumps([{
            "name": "live-sql",
            "region": "us-east1",
            "state": "RUNNING",
            "settings": {
                "ipConfiguration": {"ipv4Enabled": True, "authorizedNetworks": []}
            }
        }])
        mock_gcs_out = json.dumps([{
            "name": "live-bucket",
            "location": "us-east1",
            "public_access_prevention": "inherited",
            "default_storage_class": "STANDARD",
            "uniform_bucket_level_access": True
        }])
        mock_network_out = json.dumps([{
            "name": "default",
            "autoCreateSubnetworks": True,
            "subnetworks": ["live-subnet-1"]
        }])
        
        def mock_subprocess_run(cmd, *args, **kwargs):
            mock_res = MagicMock()
            mock_res.returncode = 0
            if "compute" in cmd and "instances" in cmd:
                mock_res.stdout = mock_vm_out
            elif "compute" in cmd and "networks" in cmd:
                mock_res.stdout = mock_network_out
            elif "run" in cmd and "get-iam-policy" in cmd:
                mock_res.stdout = mock_run_iam_out
            elif "run" in cmd:
                mock_res.stdout = mock_run_out
            elif "container" in cmd:
                mock_res.stdout = mock_gke_out
            elif "sql" in cmd:
                mock_res.stdout = mock_sql_out
            elif "storage" in cmd:
                mock_res.stdout = mock_gcs_out
            return mock_res
            
        with patch.dict(os.environ, {"MOCK_TOOLING": "false"}), \
             patch("subprocess.run", side_effect=mock_subprocess_run):
             
            ret_json_path = discover_project_resources(project_id)
            assert ret_json_path == json_path
            assert os.path.exists(json_path)
            assert os.path.exists(md_path)
            
            with open(json_path, "r") as f:
                resources = json.load(f)
                
            assert len(resources) == 6  # VM crawler filtered out GKE system and Dataproc worker node VMs
            for r in resources:
                assert r["vulnerable"] is True  # All mocked resources were set up vulnerable
                if r["type"] == "gce_vm":
                    assert not r["name"].startswith("gke-")
                    assert "dataproc" not in r["name"]
    finally:
        if os.path.exists(json_path):
            os.remove(json_path)
        if os.path.exists(md_path):
            os.remove(md_path)

def test_cli_discover_subcommand():
    project_id = "cli-test-project"
    cache_dir = os.path.join(get_discover_dir(), "gcp-project", project_id)
    json_path = os.path.join(cache_dir, "discover.json")
    md_path = os.path.join(cache_dir, "wiki.md")
    
    # Ensure clean state
    if os.path.exists(json_path):
        os.remove(json_path)
    if os.path.exists(md_path):
        os.remove(md_path)
        
    try:
        with patch.dict(os.environ, {"MOCK_TOOLING": "true"}):
            exit_code = run_cli(["discover", "--project-id", project_id])
            assert exit_code == 0
            assert os.path.exists(json_path)
            assert os.path.exists(md_path)
    finally:
        if os.path.exists(json_path):
            os.remove(json_path)
        if os.path.exists(md_path):
            os.remove(md_path)

def test_discover_live_failure_raises_in_development():
    """Verify that in development mode with MOCK_TOOLING=false, empty/failing live discovery
    raises RuntimeError instead of silently falling back to mock data."""
    project_id = "non-existent-project-xyz"
    cache_dir = os.path.join(get_discover_dir(), "gcp-project", project_id)
    json_path = os.path.join(cache_dir, "discover.json")
    md_path = os.path.join(cache_dir, "wiki.md")
    
    if os.path.exists(json_path):
        os.remove(json_path)
    if os.path.exists(md_path):
        os.remove(md_path)

    try:
        def failing_subprocess_run(*args, **kwargs):
            raise subprocess.CalledProcessError(returncode=1, cmd=args[0], output="Error: project not found or lack permissions")

        with patch.dict(os.environ, {"MOCK_TOOLING": "false", "SRE_ENV": "development"}), \
             patch("subprocess.run", side_effect=failing_subprocess_run):
            with pytest.raises(RuntimeError) as exc_info:
                discover_project_resources(project_id)
            assert "Silent fallback to mock data is disabled in development mode" in str(exc_info.value)
            assert project_id in str(exc_info.value)
            # Ensure mock data was NOT written to disk
            assert not os.path.exists(json_path)
    finally:
        if os.path.exists(json_path):
            os.remove(json_path)
        if os.path.exists(md_path):
            os.remove(md_path)

def test_discover_mock_resources_sre_next():
    """Verify that MOCK_TOOLING=true properly uses mock resources for sre-next."""
    project_id = "sre-next"
    cache_dir = os.path.join(get_discover_dir(), "gcp-project", project_id)
    json_path = os.path.join(cache_dir, "discover.json")
    md_path = os.path.join(cache_dir, "wiki.md")
    
    if os.path.exists(json_path):
        os.remove(json_path)
    if os.path.exists(md_path):
        os.remove(md_path)

    try:
        with patch.dict(os.environ, {"MOCK_TOOLING": "true"}):
            ret_json_path = discover_project_resources(project_id)
            assert ret_json_path == json_path
            assert os.path.exists(json_path)
            with open(json_path, "r") as f:
                resources = json.load(f)
            assert len(resources) > 0
            assert all(r.get("is_mock") is True for r in resources)
    finally:
        if os.path.exists(json_path):
            os.remove(json_path)
        if os.path.exists(md_path):
            os.remove(md_path)

def test_discover_mock_fallback_allowed_in_test_env():
    """Verify that in test environment (SRE_ENV=test), fallback to mock data still functions."""
    project_id = "test-project-fallback"
    cache_dir = os.path.join(get_discover_dir(), "gcp-project", project_id)
    json_path = os.path.join(cache_dir, "discover.json")
    md_path = os.path.join(cache_dir, "wiki.md")
    
    if os.path.exists(json_path):
        os.remove(json_path)
    if os.path.exists(md_path):
        os.remove(md_path)

    try:
        def failing_subprocess_run(*args, **kwargs):
            raise subprocess.CalledProcessError(returncode=1, cmd=args[0], output="Error")

        with patch.dict(os.environ, {"MOCK_TOOLING": "false", "SRE_ENV": "test"}), \
             patch("subprocess.run", side_effect=failing_subprocess_run):
            ret_json_path = discover_project_resources(project_id)
            assert ret_json_path == json_path
            assert os.path.exists(json_path)
            with open(json_path, "r") as f:
                resources = json.load(f)
            assert len(resources) > 0
            assert any(r.get("is_mock") is True for r in resources)
    finally:
        if os.path.exists(json_path):
            os.remove(json_path)
        if os.path.exists(md_path):
            os.remove(md_path)
