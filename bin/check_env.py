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

    print("\n=====================================================")
    if errors > 0:
        print(f"❌ CHECK FAILED: {errors} error(s), {warnings} warning(s) found.")
        print("Please correct the errors before running the server.")
        sys.exit(1)
    elif warnings > 0:
        print(f"⚠️ CHECK PASSED WITH WARNINGS: {warnings} warning(s) found.")
        print("Server should run, but some optional integrations might not work.")
        sys.exit(0)
    else:
        print("🎉 ALL CHECKS PASSED: Your environment is fully configured!")
        sys.exit(0)

if __name__ == "__main__":
    check_env()
