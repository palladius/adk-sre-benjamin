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

# Kill any process listening on port 8080 and restart the web server (FE and BE)
restart-services:
    @echo "🔄 Restarting Project Benjamin web services..."
    @pid=$(lsof -t -i :8080 2>/dev/null) || true; \
    if [ -n "$pid" ]; then \
        echo "💀 Killing existing process $pid on port 8080..."; \
        kill -9 $pid || true; \
        sleep 1; \
    fi
    @PYTHONPATH=. uv run python3 src/server.py

# Deploy SRE dashboard locally via Docker building, pushing, and Cloud Run deploy
deploy:
    @bash bin/deploy-to-cloudrun.sh


# Build the SRE dashboard Docker container locally
docker-build:
    @echo "📦 Building SRE Agent docker image..."
    docker build \
        -t us-central1-docker.pkg.dev/$(gcloud config get-value project 2>/dev/null || echo "sre-next")/sre-agent-repo/sre-agent:latest \
        -t us-central1-docker.pkg.dev/$(gcloud config get-value project 2>/dev/null || echo "sre-next")/sre-agent-repo/sre-agent:v$(cat VERSION | tr -d '\r\n') .

# Push SRE dashboard Docker container to Artifact Registry
docker-push:
    @echo "🚀 Pushing SRE Agent docker image to Artifact Registry..."
    docker push us-central1-docker.pkg.dev/$(gcloud config get-value project 2>/dev/null || echo "sre-next")/sre-agent-repo/sre-agent:latest
    docker push us-central1-docker.pkg.dev/$(gcloud config get-value project 2>/dev/null || echo "sre-next")/sre-agent-repo/sre-agent:v$(cat VERSION | tr -d '\r\n')


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
conductor-status:
	~/git/ricclife-with-gemini-pvt/work/articles/20260605-worktree-multiagent-dev-flow/subtasks/20260616-adk-sre-benjamin/conductor-worktree-hitl/scripts/conductor-inspector . --open --short
conductor-status-all:
	~/git/ricclife-with-gemini-pvt/work/articles/20260605-worktree-multiagent-dev-flow/subtasks/20260616-adk-sre-benjamin/conductor-worktree-hitl/scripts/conductor-inspector . --all --short

poll-ghi-questions:
	python3 ~/git/ricclife-with-gemini-pvt/work/articles/20260605-worktree-multiagent-dev-flow/subtasks/20260616-adk-sre-benjamin/conductor-worktree-hitl/scripts/poll_ghi_questions.py


