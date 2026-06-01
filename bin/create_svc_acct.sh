#!/bin/bash
# Reusable SRE script to create the Safe Investigator Service Account and save key

set -e

# Default variables
PROJECT_ID=${1:-$(grep -Po "^PROJECT_ID='?\K[^']+" .env 2>/dev/null || echo "sre-demo-fake-id-123")}
SA_NAME="safe-sre-investigator"
EMAIL_NAME="palladiusbonton"
KEY_FILE="private/${EMAIL_NAME}.json"

echo "====================================================="
echo "🛡️ SRE SAFE INVESTIGATOR SERVICE ACCOUNT SETUP"
echo "====================================================="
echo " Target GCP Project : ${PROJECT_ID}"
echo " Service Account Name: ${SA_NAME}"
echo " Key File Output     : ${KEY_FILE}"
echo "====================================================="

# 1. Create the private directory
mkdir -p private

# 2. Check if service account already exists
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
if gcloud iam service-accounts describe "${SA_EMAIL}" --project="${PROJECT_ID}" &>/dev/null; then
    echo "[-] Service account ${SA_EMAIL} already exists."
else
    echo "[+] Creating service account ${SA_NAME}..."
    gcloud iam service-accounts create "${SA_NAME}" \
        --display-name="SRE Safe Investigator Service Account" \
        --project="${PROJECT_ID}"
fi

# 3. Bind safe roles (Viewer, Logging Viewer, Monitoring Viewer) to the service account
echo "[+] Binding safe Read-Only roles to service account..."
RO_ROLES=("roles/viewer" "roles/logging.viewer" "roles/monitoring.viewer")
for role in "${RO_ROLES[@]}"; do
    echo "    - Binding ${role}..."
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="${role}" \
        --no-user-output-enabled &>/dev/null || echo "    [!] Warning: Could not bind ${role}."
done

# 4. Generate and download the JSON credentials key file
echo "[+] Generating JSON credentials key file..."
gcloud iam service-accounts keys create "${KEY_FILE}" \
    --iam-account="${SA_EMAIL}" \
    --project="${PROJECT_ID}"

echo "====================================================="
echo "🎉 Setup complete! Key file stored in: ${KEY_FILE}"
echo "====================================================="
