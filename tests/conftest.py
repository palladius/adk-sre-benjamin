import os
import pytest

@pytest.fixture(autouse=True)
def clean_auth_env():
    # Store original values
    orig_user = os.environ.get("WEB_USERNAME")
    orig_pwd = os.environ.get("WEB_PASSWORD")
    orig_identity = os.environ.get("GCLOUD_IDENTITY")
    
    # Remove from env for the test run
    os.environ.pop("WEB_USERNAME", None)
    os.environ.pop("WEB_PASSWORD", None)
    os.environ.pop("GCLOUD_IDENTITY", None)
    
    yield
    
    # Restore original values
    if orig_user is not None:
        os.environ["WEB_USERNAME"] = orig_user
    else:
        os.environ.pop("WEB_USERNAME", None)
        
    if orig_pwd is not None:
        os.environ["WEB_PASSWORD"] = orig_pwd
    else:
        os.environ.pop("WEB_PASSWORD", None)
        
    if orig_identity is not None:
        os.environ["GCLOUD_IDENTITY"] = orig_identity
    else:
        os.environ.pop("GCLOUD_IDENTITY", None)
