#!/usr/bin/env python3
"""
Project Benjamin SRE GCP Config Setup Helper
Creates/configures a local gcloud configuration profile 'sre-benjamin-dflt-project' 
using values loaded dynamically from the environment or .env file.
"""

import os
import sys
import json
import shutil
import subprocess

def load_env_vars() -> dict:
    """Loads environment variables manually from .env file to bypass external dependencies."""
    env = {}
    # Load system environment first
    for k, v in os.environ.items():
        env[k] = v
        
    # Override with local .env file
    if os.path.exists(".env"):
        try:
            with open(".env", "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        parts = line.split("=", 1)
                        key = parts[0].strip()
                        val = parts[1].strip().strip("'\"")
                        env[key] = val
        except Exception as e:
            print(f"⚠️ Warning: Failed to parse .env file: {e}")
            
    return env

def main():
    print("=====================================================")
    print("🛡️ PROJECT BENJAMIN: SRE GCP GCLOUD CONFIG SETUP")
    print("=====================================================")

    # 1. Verify gcloud is installed
    if not shutil.which("gcloud"):
        print("❌ Error: 'gcloud' CLI tool is not installed on this system.")
        print("👉 Please download and install the Google Cloud SDK: https://cloud.google.com/sdk")
        sys.exit(1)

    # 2. Load and validate SRE configuration keys
    env = load_env_vars()
    
    gcp_project_id = env.get("GCP_PROJECT_ID") or env.get("PROJECT_ID")
    gcp_service_account = env.get("GCP_SERVICE_ACCOUNT") or env.get("GOOGLE_IMPERSONATE_SERVICE_ACCOUNT")

    # Clean default template placeholders
    if gcp_project_id:
        gcp_project_id = gcp_project_id.strip("'\"")
    if gcp_service_account:
        gcp_service_account = gcp_service_account.strip("'\"")

    is_project_placeholder = not gcp_project_id or "ENTER" in gcp_project_id
    is_sa_placeholder = not gcp_service_account or "ENTER" in gcp_service_account

    if is_project_placeholder or is_sa_placeholder:
        print("❌ Error: Missing or default GCP configurations in '.env' file!")
        print("👉 Please populate these two variables inside your '.env' with your authentic settings:")
        print("   1. GCP_PROJECT_ID='<your-project-id>'")
        print("   2. GCP_SERVICE_ACCOUNT='<your-service-account-email>'")
        sys.exit(1)

    # 3. Check for active gcloud authentication
    try:
        res = subprocess.run(
            ["gcloud", "auth", "list", "--format=json"], 
            capture_output=True, 
            text=True
        )
        if res.returncode == 0:
            auths = json.loads(res.stdout)
            has_active = any(a.get("status") == "ACTIVE" for a in auths)
            if not has_active:
                print("⚠️ Warning: No active gcloud authenticated account found!")
                print("👉 Please authenticate with Google first by running in your terminal:")
                print("   $ gcloud auth login")
                print("   $ gcloud auth application-default login")
                print("-----------------------------------------------------")
        else:
            print("⚠️ Warning: Could not verify gcloud authentication state.")
    except Exception as e:
        print(f"⚠️ Warning: Check auth check error: {e}")

    # 4. Create or activate 'sre-benjamin-dflt-project' configuration profile
    try:
        res_list = subprocess.run(
            ["gcloud", "config", "configurations", "list", "--format=json"], 
            capture_output=True, 
            text=True,
            check=True
        )
        configs = json.loads(res_list.stdout)
        config_names = [c.get("name") for c in configs]
        
        profile_name = "sre-benjamin-dflt-project"
        
        if profile_name in config_names:
            print(f"[+] Activating existing configuration profile '{profile_name}'...")
            subprocess.run(
                ["gcloud", "config", "configurations", "activate", profile_name], 
                check=True
            )
        else:
            print(f"[+] Creating a new local configuration profile '{profile_name}'...")
            subprocess.run(
                ["gcloud", "config", "configurations", "create", profile_name], 
                check=True
            )
            
        # 5. Bind project and service account impersonation coordinates
        print(f"[+] Setting default GCP Project ID: {gcp_project_id}")
        subprocess.run(
            ["gcloud", "config", "set", "project", gcp_project_id], 
            check=True
        )
        
        print(f"[+] Setting service account impersonation identity: {gcp_service_account}")
        subprocess.run(
            ["gcloud", "config", "set", "auth/impersonate_service_account", gcp_service_account], 
            check=True
        )
        
        print("=====================================================")
        print("🎉 SUCCESS: 'sre-benjamin-dflt-project' IS READY!")
        print("=====================================================")
        print(f" Active Project    : {gcp_project_id}")
        print(f" Impersonated SA   : {gcp_service_account}")
        print("=====================================================")
        
    except subprocess.CalledProcessError as err:
        print(f"❌ Failure executing gcloud configuration commands: {err}")
        sys.exit(1)
    except Exception as err:
        print(f"❌ An unexpected error occurred: {err}")
        sys.exit(1)

if __name__ == "__main__":
    main()
