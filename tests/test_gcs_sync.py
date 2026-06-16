import os
import subprocess
from unittest.mock import patch, MagicMock
import pytest
from src.gcs_sync import (
    get_gcs_bucket_name,
    get_gcs_folder_path,
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

def test_gcs_yaml_configuration():
    mock_config = {
        "production": {
            "gcs_enabled": True,
            "gcs_bucket": "custom-production-bucket",
            "gcs_folder": "production-discovery-folder"
        },
        "development": {
            "gcs_enabled": True,
            "gcs_bucket": "custom-dev-bucket"
        },
        "test": {
            "gcs_enabled": False
        }
    }
    
    with patch("src.gcs_sync._load_gcs_config", return_value=mock_config):
        # Test production configs (friendly name prod should map to production)
        with patch.dict(os.environ, {"SRE_ENV": "prod", "GCP_PROJECT_ID": "project-123"}):
            assert is_gcs_enabled()
            assert get_gcs_bucket_name() == "custom-production-bucket"
            assert get_gcs_folder_path() == "production-discovery-folder/"
            
        # Test development configs (friendly name dev should map to development)
        with patch.dict(os.environ, {"SRE_ENV": "dev", "GCP_PROJECT_ID": "project-123"}):
            assert is_gcs_enabled()
            assert get_gcs_bucket_name() == "custom-dev-bucket"
            assert get_gcs_folder_path() == "discovery/development/"  # Default fallback
            
        # Test test configs (should always be false and fallback)
        with patch.dict(os.environ, {"SRE_ENV": "testing", "GCP_PROJECT_ID": "project-123"}):
            assert not is_gcs_enabled()
            assert get_gcs_folder_path() == "discovery/test/"

def test_is_gcs_enabled():
    with patch.dict(os.environ, {"MOCK_TOOLING": "true"}):
        assert not is_gcs_enabled()

    with patch.dict(os.environ, {"MOCK_TOOLING": "false", "GCS_BUCKET": "my-bucket", "SRE_ENV": "production"}):
        assert is_gcs_enabled()

def test_sync_status():
    set_sync_status("SYNCING")
    with patch.dict(os.environ, {"MOCK_TOOLING": "false", "GCS_BUCKET": "my-bucket", "SRE_ENV": "production"}):
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
    mock_run.return_value = MagicMock(returncode=0, stdout="gs://my-bucket/discovery/test/discover.json")
    with patch.dict(os.environ, {"SRE_ENV": "test"}):
        assert GcsSyncManager.check_gcs_has_files("my-bucket")
        assert mock_run.call_args[0][0] == ["gsutil", "ls", "gs://my-bucket/discovery/test/"]

    # Create bucket
    mock_run.return_value = MagicMock(returncode=0)
    with patch.dict(os.environ, {"GCP_PROJECT_ID": "sre-next-dev"}):
        assert GcsSyncManager.create_bucket("my-bucket")
        assert mock_run.call_args[0][0] == ["gsutil", "mb", "-p", "sre-next-dev", "gs://my-bucket"]

def test_gcs_sync_manager_live():
    # Only run this test if SRE_MODE is explicitly set to LIVE (acceptance testing)
    if os.getenv("SRE_MODE") != "LIVE":
        pytest.skip("Skipping GCS acceptance testing because SRE_MODE is not LIVE")

    # We will test the actual GcsSyncManager syncing with the real GCS bucket.
    # We will use a unique folder name in the bucket to prevent collusions with production state.
    import uuid
    test_run_id = f"acceptance-test-{uuid.uuid4().hex[:8]}"
    
    with patch.dict(os.environ, {
        "MOCK_TOOLING": "false",
        "SRE_ENV": "production",  # Enable GCS
        "GCS_BUCKET": "sre-next-sre-benjamin-discovery",
    }):
        # Setup a temporary local discovery file
        from src.incident import get_discover_dir
        local_dir = get_discover_dir()
        os.makedirs(local_dir, exist_ok=True)
        
        test_file_path = os.path.join(local_dir, "acceptance_test.json")
        with open(test_file_path, "w") as f:
            f.write('{"status": "testing", "test_id": "' + test_run_id + '"}')
            
        try:
            # Synchronize to GCS
            # We patch the folder path to be unique to this test run
            with patch("src.gcs_sync.get_gcs_folder_path", return_value=f"discovery/acceptance-tests/{test_run_id}/"):
                # 1. Test pushing to GCS
                push_success = GcsSyncManager.do_sync_to_gcs()
                assert push_success, "Failed to push acceptance test file to GCS"
                
                # 2. Verify files are on GCS
                assert GcsSyncManager.check_gcs_has_files("sre-next-sre-benjamin-discovery"), "GCS does not report files on the test path"
                
                # 3. Modify local file, then pull back from GCS and verify it gets restored
                with open(test_file_path, "w") as f:
                    f.write('{"status": "overwritten"}')
                
                pull_success = GcsSyncManager.do_sync_from_gcs()
                assert pull_success, "Failed to pull acceptance test file from GCS"
                
                with open(test_file_path, "r") as f:
                    content = f.read()
                assert test_run_id in content, f"Expected test_run_id {test_run_id} in content, got: {content}"
                
        finally:
            # Clean up local file
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
            # Clean up GCS path by deleting the files using gsutil
            gcs_folder_path = f"gs://sre-next-sre-benjamin-discovery/discovery/acceptance-tests/{test_run_id}/"
            subprocess.run(["gsutil", "rm", "-r", gcs_folder_path], capture_output=True)
