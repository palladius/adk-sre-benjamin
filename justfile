# Project Benjamin SRE Agentic Framework - Justfile

default:
    @just --list

# Run the complete E2E SRE incident simulation
simulate:
    @.venv/bin/python3 run_simulation.py

# Run all automated unit and integration tests
test:
    @.venv/bin/pytest

# Run test suite with code coverage reports
coverage:
    @.venv/bin/pytest --cov=src

# Install dependencies into virtual environment
install:
    @.venv/bin/pip install -r requirements.txt
