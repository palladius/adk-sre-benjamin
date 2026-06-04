# Project Benjamin SRE Agentic Framework - Justfile

default:
    @just --list

# Verify local installation, dependencies, and configuration
check:
    @uv run python3 bin/check_env.py

# Run a live test query against GCP Cloud Logging
test-logging:
    @SRE_MODE=LIVE PYTHONPATH=. uv run python3 -c "from src.diagnostics import query_logs; print(query_logs('sre-next', 'severity>=WARNING'))"

# Run a live test query against GCP Cloud Monitoring metrics
test-metrics:
    @SRE_MODE=LIVE PYTHONPATH=. uv run python3 -c "from src.diagnostics import query_metrics; print(query_metrics('sre-next', 'cpu'))"

# Run the complete E2E SRE incident simulation
simulate:
    @uv run python3 run_simulation.py

# Run all automated unit and integration tests inside a resource-limited cage (max 4GB RAM)
test:
    @nice -n 19 systemd-run --user --scope -p MemoryMax=4G -p CPUQuota=80% uv run pytest

# Relaunch the SRE dashboard web server on port 8080
web:
    @PYTHONPATH=. uv run python3 src/server.py

# Deploy the SRE dashboard to Google Cloud Run using gcloud source build
deploy:
    @echo "🚀 Containerizing and deploying SRE Dashboard to Cloud Run..."
    gcloud beta run deploy sre-agent-service \
        --source . \
        --port 8080 \
        --no-allow-unauthenticated \
        --iap \
        --set-env-vars "WEB_USERNAME=${WEB_USERNAME},WEB_PASSWORD=${WEB_PASSWORD},GEMINI_API_KEY=${GEMINI_API_KEY},DEFAULT_GEMINI_MODEL=${DEFAULT_GEMINI_MODEL},GCLOUD_IDENTITY=${GCLOUD_IDENTITY}" \
        --region us-central1

# Initialize Terraform configuration
tf-init:
    cd terraform && terraform init

# Plan Terraform infrastructure deployment
tf-plan:
    cd terraform && terraform plan -var="project_id=$(gcloud config get-value project)" -var="image=us-central1-docker.pkg.dev/$(gcloud config get-value project)/cloud-run-source-deploy/sre-agent-service:latest" -var="gcloud_identity=${GCLOUD_IDENTITY}"

# Apply Terraform infrastructure deployment
tf-apply:
    cd terraform && terraform apply -auto-approve -var="project_id=$(gcloud config get-value project)" -var="image=us-central1-docker.pkg.dev/$(gcloud config get-value project)/cloud-run-source-deploy/sre-agent-service:latest" -var="gcloud_identity=${GCLOUD_IDENTITY}"



# Run test suite with code coverage reports inside a resource-limited cage (max 4GB RAM)
coverage:
    @nice -n 19 systemd-run --user --scope -p MemoryMax=4G -p CPUQuota=80% uv run pytest --cov=src

# Install dependencies into virtual environment and configure GCP profile
install:
    @uv venv
    @uv pip install -r requirements.txt
    @just setup

# Configure local gcloud profile 'sre-benjamin-dflt-project' with SRE credentials
setup:
    @python3 bin/gcloud_setup.py

# Clean temporary files, pytest caches, and cached project discoveries
clean:
    @rm -rf .pytest_cache .coverage htmlcov src/__pycache__ tests/__pycache__ src/agents/__pycache__
    @rm -rf discover/gcp-project/*.json discover/gcp-project/*.md
    @rm -rf cloud


telegram-send-test-message:
  PYTHONPATH=. uv run python3 src/cli.py telegram send "Hello Operator! Testing the new CLI telegram send command from *$(hostname)*! 🏰🚀"

# Setup just for Riccardo
ricc-setup:
  git-privatize sync
