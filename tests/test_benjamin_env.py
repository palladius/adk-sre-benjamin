import os
import pytest
from src.incident import (
    resolve_benjamin_env,
    get_investigations_dir,
    get_discover_dir,
    validate_incident_id,
)
import src.db as db


def test_resolve_benjamin_env_precedence(monkeypatch):
    # 1. Highest priority: BENJAMIN_ENV
    monkeypatch.setenv("BENJAMIN_ENV", "prod")
    monkeypatch.setenv("SRE_ENV", "dev")
    monkeypatch.setenv("RAILS_ENV", "test")
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    assert resolve_benjamin_env() == "production"
    assert get_investigations_dir() == "investigations/prod"
    assert get_discover_dir() == "discovery/prod"

    # 2. Second priority: SRE_ENV
    monkeypatch.delenv("BENJAMIN_ENV", raising=False)
    monkeypatch.setenv("SRE_ENV", "production")
    monkeypatch.setenv("RAILS_ENV", "dev")
    assert resolve_benjamin_env() == "production"

    # 3. Third priority: PYTEST_CURRENT_TEST when BENJAMIN_ENV and SRE_ENV are unset
    monkeypatch.delenv("SRE_ENV", raising=False)
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "tests/test_benjamin_env.py::test")
    monkeypatch.setenv("RAILS_ENV", "production")
    assert resolve_benjamin_env() == "test"

    # 4. Fourth priority: RAILS_ENV
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setenv("RAILS_ENV", "production")
    assert resolve_benjamin_env() == "production"

    # 5. Fallback default: development
    monkeypatch.delenv("RAILS_ENV", raising=False)
    assert resolve_benjamin_env() == "development"
    assert get_investigations_dir() == "investigations/dev"
    assert get_discover_dir() == "discovery/dev"


def test_resolve_benjamin_env_aliases(monkeypatch):
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    # Test aliases
    for val in ("test", "testing", "TEST"):
        monkeypatch.setenv("BENJAMIN_ENV", val)
        assert resolve_benjamin_env() == "test"
        assert get_investigations_dir() == "investigations/test"
        assert get_discover_dir() == "discovery/test"

    # Dev aliases
    for val in ("dev", "development", "local", "Development"):
        monkeypatch.setenv("BENJAMIN_ENV", val)
        assert resolve_benjamin_env() == "development"
        assert get_investigations_dir() == "investigations/dev"
        assert get_discover_dir() == "discovery/dev"

    # Prod aliases
    for val in ("prod", "production", "PROD"):
        monkeypatch.setenv("BENJAMIN_ENV", val)
        assert resolve_benjamin_env() == "production"
        assert get_investigations_dir() == "investigations/prod"
        assert get_discover_dir() == "discovery/prod"


def test_resolve_benjamin_env_rejects_unknown_values(monkeypatch):
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    for bad_env in ("staging", "prodution", "qa", "invalid-env"):
        monkeypatch.setenv("BENJAMIN_ENV", bad_env)
        with pytest.raises(ValueError, match="Invalid environment"):
            resolve_benjamin_env()


def test_db_active_state_row_id_scoped_by_benjamin_env(monkeypatch):
    monkeypatch.setenv("BENJAMIN_ENV", "production")
    assert db._resolve_active_state_row_id() == 1

    monkeypatch.setenv("BENJAMIN_ENV", "development")
    assert db._resolve_active_state_row_id() == 2

    monkeypatch.setenv("BENJAMIN_ENV", "test")
    assert db._resolve_active_state_row_id() == 3


def test_validate_incident_id_rejects_traversal_and_reserved_names():
    assert validate_incident_id("INC-20260601-244e") == "INC-20260601-244e"
    for bad_id in (
        "",
        "None",
        "../../escaped",
        "../secret",
        "INC/123",
        "INC\\123",
        "active_state.json",
        "state.md",
        "chat.json",
        "something.json",
        ".hidden",
    ):
        with pytest.raises(ValueError):
            validate_incident_id(bad_id)
