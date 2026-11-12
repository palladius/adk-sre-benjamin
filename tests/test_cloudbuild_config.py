"""Static sanity checks for cloudbuild.yaml (offline; no GCP access needed)."""
from pathlib import Path

import yaml

CLOUDBUILD = Path(__file__).resolve().parent.parent / "cloudbuild.yaml"


def _load():
    return yaml.safe_load(CLOUDBUILD.read_text())


def test_cloudbuild_has_named_steps():
    config = _load()
    steps = config.get("steps")
    assert steps, "cloudbuild.yaml must define at least one step"
    assert all(step.get("name") for step in steps)


def test_cloudbuild_dual_tags_latest_and_version():
    text = CLOUDBUILD.read_text()
    assert ":latest" in text
    assert ":v$$VERSION" in text
