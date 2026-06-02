# Project Benjamin SRE Agentic Framework - Justfile

default:
    @just --list

# Run the complete E2E SRE incident simulation
simulate:
    @uv run python3 run_simulation.py

# Run all automated unit and integration tests inside a resource-limited cage (max 4GB RAM)
test:
    @nice -n 19 systemd-run --user --scope -p MemoryMax=4G -p CPUQuota=80% uv run pytest

# Relaunch the SRE dashboard web server on port 8080
web:
    @PYTHONPATH=. uv run python3 src/server.py

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

