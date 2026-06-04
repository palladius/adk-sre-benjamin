#!/usr/bin/env python3
import os
import sys

def check_env():
    print("=====================================================")
    print("🛡️ PROJECT BENJAMIN: SRE CONFIG & ENVIRONMENT CHECK")
    print("=====================================================")
    
    errors = 0
    warnings = 0

    # 1. Check Python Dependencies
    print("[1] Checking python dependencies...")
    required_modules = {
        "dotenv": "python-dotenv",
        "jinja2": "jinja2",
        "yaml": "pyyaml",
        "pytest": "pytest"
    }
    for module, pkg in required_modules.items():
        try:
            __import__(module)
            print(f"  ✅ {pkg} is installed.")
        except ImportError:
            print(f"  ❌ {pkg} is NOT installed!")
            errors += 1

    # 2. Check .env existence
    print("\n[2] Checking .env configuration...")
    if not os.path.exists(".env"):
        print("  ❌ .env file does not exist! Please create one based on .env.dist.")
        errors += 1
        return errors, warnings
    else:
        print("  ✅ .env file exists.")

    # 3. Load .env manually to avoid import dependency issues
    env_vars = {}
    try:
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    parts = line.split("=", 1)
                    key = parts[0].strip()
                    val = parts[1].strip().strip("'\"")
                    env_vars[key] = val
    except Exception as e:
        print(f"  ❌ Failed to parse .env file: {e}")
        errors += 1
        return errors, warnings

    # 4. Validate Environment Variables
    required_keys = ["MOCK_TOOLING", "DEFAULT_GEMINI_MODEL"]
    for key in required_keys:
        if key not in env_vars:
            print(f"  ❌ Required variable {key} is missing in .env.")
            errors += 1
        else:
            print(f"  ✅ {key} is set to: '{env_vars[key]}'")

    # 5. Check Telegram Integration
    print("\n[3] Checking Telegram configurations...")
    tg_bot = env_vars.get("TELEGRAM_BOT_TOKEN")
    tg_chat = env_vars.get("TELEGRAM_CHAT_ID")
    
    if not tg_bot or tg_bot == "ENTER_BOT_TOKEN_HERE" or tg_bot == "your_telegram_bot_token_here":
        print("  ⚠️ TELEGRAM_BOT_TOKEN is not configured or uses placeholder.")
        warnings += 1
    else:
        print(f"  ✅ TELEGRAM_BOT_TOKEN is set ({tg_bot[:6]}...{tg_bot[-4:] if len(tg_bot) > 10 else ''})")

    if not tg_chat or tg_chat == "ENTER_CHAT_ID_HERE" or tg_chat == "your_telegram_chat_id_here":
        print("  ⚠️ TELEGRAM_CHAT_ID is not configured or uses placeholder.")
        warnings += 1
    else:
        print(f"  ✅ TELEGRAM_CHAT_ID is set ({tg_chat})")

    # 6. Check GCP Impersonation
    print("\n[4] Checking active GCP credentials...")
    import subprocess
    try:
        # Check active gcloud config
        active_config = subprocess.check_output(
            ["gcloud", "config", "configurations", "list", "--filter=IS_ACTIVE=true", "--format=value(NAME)"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        print(f"  ✅ Active gcloud configuration: '{active_config}'")
        
        # Check impersonate service account
        impersonate_sa = subprocess.check_output(
            ["gcloud", "config", "get-value", "auth/impersonate_service_account"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        if impersonate_sa:
            print(f"  ✅ Impersonated Service Account: '{impersonate_sa}'")
        else:
            print("  ⚠️ No impersonated service account active in current config.")
            warnings += 1
    except Exception:
        print("  ⚠️ Could not query active gcloud profile. (Is gcloud CLI installed?)")
        warnings += 1

    # 7. Check local Web server (FE & BE) activity
    print("\n[5] Checking local Web server (FE & BE) activity...")
    import socket
    import urllib.request
    import urllib.error
    
    port = int(env_vars.get("PORT", 8080))
    url = f"http://localhost:{port}"
    web_error = False
    
    # Try opening socket first
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.0)
    try:
        s.connect(("127.0.0.1", port))
        s.close()
        print(f"  ✅ Port {port} is open and listening.")
        
        # Try fetching frontend route
        try:
            req = urllib.request.Request(url + "/projects/sre-next")
            with urllib.request.urlopen(req, timeout=2.0) as response:
                if response.status == 200:
                    print("  ✅ Frontend (FE) page loaded successfully (200 OK).")
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                print(f"  ✅ Backend (BE) is alive, but requested authentication (HTTP {e.code}).")
            else:
                print(f"  ❌ Backend (BE) returned HTTP error: {e.code} - {e.reason}")
                web_error = True
        except Exception as e:
            print(f"  ❌ Failed to communicate with local web server: {e}")
            web_error = True
            
        # Try fetching API config using credentials from .env if present
        try:
            username = env_vars.get("WEB_USERNAME")
            password = env_vars.get("WEB_PASSWORD")
            req_api = urllib.request.Request(url + "/api/config")
            if username and password:
                import base64
                auth_str = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")
                req_api.add_header("Authorization", f"Basic {auth_str}")
            with urllib.request.urlopen(req_api, timeout=2.0) as resp_api:
                if resp_api.status == 200:
                    import json
                    data = json.loads(resp_api.read().decode("utf-8"))
                    print(f"  ✅ Backend API (/api/config) responsive. Project ID: '{data.get('project_id')}', Version: '{data.get('version')}'")
        except Exception as e:
            # Don't fail the check on API auth issues, just warn
            print(f"  ⚠️ Could not query config API (possibly auth-restricted): {e}")
            
    except (socket.timeout, ConnectionRefusedError):
        print(f"  ❌ Port {port} is NOT listening! The SRE Dashboard server is inactive.")
        print(f"  👉 COMMAND TO RUN: Start the backend server by running 'just web' in another terminal.")
        web_error = True

    print("\n=====================================================")
    if errors > 0 or web_error:
        print(f"❌ CHECK FAILED: {errors} error(s), {warnings} warning(s) found.")
        if web_error and errors == 0:
            print("Configuration is OK, but the server is not currently running.")
            print("👉 Run: 'just web' to start the server.")
        else:
            print("Please correct the errors before running the server.")
        sys.exit(1)
    elif warnings > 0:
        print(f"⚠️ CHECK PASSED WITH WARNINGS: {warnings} warning(s) found.")
        print("Server should run, but some optional integrations might not work.")
        sys.exit(0)
    else:
        print("🎉 ALL CHECKS PASSED: Your environment and server are fully active!")
        sys.exit(0)

if __name__ == "__main__":
    check_env()
