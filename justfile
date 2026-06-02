# Project Benjamin SRE Agentic Framework - Justfile

default:
    @just --list

# Run the complete E2E SRE incident simulation
simulate:
    @uv run python3 run_simulation.py

# Run all automated unit and integration tests
test:
    @uv run pytest

# Relaunch the SRE dashboard web server on port 8080
web:
    @PYTHONPATH=. uv run python3 src/server.py

# Run test suite with code coverage reports
coverage:
    @uv run pytest --cov=src

# Install dependencies into virtual environment
install:
    @uv pip install -r requirements.txt

# Clean temporary files, pytest caches, and cached project discoveries
clean:
    @rm -rf .pytest_cache .coverage htmlcov src/__pycache__ tests/__pycache__ src/agents/__pycache__
    @rm -rf discover/gcp-project/*.json discover/gcp-project/*.md
    @rm -rf cloud
