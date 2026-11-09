import os
import pytest
from src.incident import resolve_benjamin_env, get_investigations_dir, get_discover_dir

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

    # 3. Third priority: RAILS_ENV
    monkeypatch.delenv("SRE_ENV", raising=False)
    monkeypatch.setenv("RAILS_ENV", "production")
    assert resolve_benjamin_env() == "production"

    # 4. Fallback default: development
    monkeypatch.delenv("RAILS_ENV", raising=False)
    assert resolve_benjamin_env() == "development"
    assert get_investigations_dir() == "investigations/dev"
    assert get_discover_dir() == "discovery/dev"

def test_resolve_benjamin_env_aliases(monkeypatch):
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    
    # Test aliases
    for val in ("test", "testing"):
        monkeypatch.setenv("BENJAMIN_ENV", val)
        assert resolve_benjamin_env() == "test"
        assert get_investigations_dir() == "investigations/test"
        assert get_discover_dir() == "discovery/test"

    # Dev aliases
    for val in ("dev", "development", "local"):
        monkeypatch.setenv("BENJAMIN_ENV", val)
        assert resolve_benjamin_env() == "development"
        assert get_investigations_dir() == "investigations/dev"
        assert get_discover_dir() == "discovery/dev"
