import os
from unittest.mock import patch, MagicMock
import pytest
from src.gcs_sync import (
    get_gcs_bucket_name,
    is_gcs_enabled,
    get_sync_status,
    set_sync_status,
    GcsSyncManager
)

def test_get_gcs_bucket_name():
    with patch.dict(os.environ, {"GCS_BUCKET": "my-custom-bucket"}):
        assert get_gcs_bucket_name() == "my-custom-bucket"

    with patch.dict(os.environ, {"GCS_BUCKET": "'my-custom-bucket'"}):
        assert get_gcs_bucket_name() == "my-custom-bucket"

    with patch.dict(os.environ, {}, clear=True):
        with patch.dict(os.environ, {"GCP_PROJECT_ID": "sre-next-dev"}):
            assert get_gcs_bucket_name() == "sre-next-dev-sre-benjamin-discovery"

    with patch.dict(os.environ, {}, clear=True):
        with patch.dict(os.environ, {"PROJECT_ID": "my-project-456"}):
            assert get_gcs_bucket_name() == "my-project-456-sre-benjamin-discovery"

def test_is_gcs_enabled():
    with patch.dict(os.environ, {"MOCK_TOOLING": "true"}):
        assert not is_gcs_enabled()

    with patch.dict(os.environ, {"MOCK_TOOLING": "false", "GCS_BUCKET": "my-bucket"}):
        assert is_gcs_enabled()

def test_sync_status():
    set_sync_status("SYNCING")
    with patch.dict(os.environ, {"MOCK_TOOLING": "false", "GCS_BUCKET": "my-bucket"}):
        assert get_sync_status() == "SYNCING"

    with patch.dict(os.environ, {"MOCK_TOOLING": "true"}):
        assert get_sync_status() == "OFFLINE"

@patch("subprocess.run")
def test_gcs_sync_manager_commands(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="gs://my-bucket/")
    
    # Check bucket exists
    assert GcsSyncManager.check_bucket_exists("my-bucket")
    assert mock_run.call_args[0][0] == ["gsutil", "ls", "-b", "gs://my-bucket"]

    # Check GCS has files
    mock_run.return_value = MagicMock(returncode=0, stdout="gs://my-bucket/gcp-project/discover.json")
    assert GcsSyncManager.check_gcs_has_files("my-bucket")
    assert mock_run.call_args[0][0] == ["gsutil", "ls", "gs://my-bucket/gcp-project/"]

    # Create bucket
    mock_run.return_value = MagicMock(returncode=0)
    with patch.dict(os.environ, {"GCP_PROJECT_ID": "sre-next-dev"}):
        assert GcsSyncManager.create_bucket("my-bucket")
        assert mock_run.call_args[0][0] == ["gsutil", "mb", "-p", "sre-next-dev", "gs://my-bucket"]
