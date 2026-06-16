import os
import sys
from typing import Dict
from google.cloud import aiplatform
from vertexai.preview import reasoning_engines

# Add local path for import checking
sys.path.append(os.getcwd())

# 1. Define the Reasoning Engine packaging wrapper class
class SreBenjaminAgent:
    def __init__(self, config: Dict[str, str] = None):
        if config:
            for k, v in config.items():
                os.environ[k] = v

    def query(self, prompt: str) -> str:
        """Executes the SRE Benjamin incident simulation or resumes it."""
        import os
        import sys
        import json
        
        # Ensure imports work cleanly on remote runtime
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.append(current_dir)
            
        try:
            from run_simulation import run_simulation, resume_simulation
            
            # Parse JSON prompts if available
            stripped_prompt = prompt.strip()
            if stripped_prompt.startswith("{") and stripped_prompt.endswith("}"):
                try:
                    params = json.loads(stripped_prompt)
                    action = params.get("action", "run_simulation")
                    if action == "run_simulation":
                        payload = params.get("payload", {})
                        inc_id, folder = run_simulation(payload=payload)
                        return json.dumps({
                            "incident_id": inc_id,
                            "folder_path": folder,
                            "status": "AWAITING_APPROVAL"
                        })
                    elif action == "resume_simulation":
                        incident_id = params.get("incident_id")
                        approved = params.get("approved", True)
                        inc_id, folder = resume_simulation(incident_id=incident_id, approved=approved)
                        return json.dumps({
                            "incident_id": inc_id,
                            "folder_path": folder,
                            "status": "RESOLVED" if approved else "ABORTED"
                        })
                except Exception:
                    pass
            
            # Parse simple text commands
            if "resume" in prompt.lower():
                parts = prompt.split()
                incident_id = parts[1] if len(parts) > 1 else "unknown"
                approved = parts[2].lower() != "false" if len(parts) > 2 else True
                inc_id, folder = resume_simulation(incident_id=incident_id, approved=approved)
                return f"Resumed incident {inc_id}. Chronicles saved in {folder}."
            else:
                payload = {
                    "event_type": "frontend_latency_slo_violated",
                    "project_id": os.getenv("GOOGLE_CLOUD_PROJECT", "")
                }
                inc_id, folder = run_simulation(payload=payload)
                return f"Started incident {inc_id} simulation. Chronicles saved in {folder}."
        except Exception as e:
            return f"Error executing SRE Benjamin: {str(e)}"

def deploy():
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    staging_bucket = f"gs://agent-staging-bucket-{project_id}"
    
    print(f"🚀 Deploying SRE Benjamin to Vertex AI Reasoning Engine...")
    print(f"   Project ID: {project_id}")
    print(f"   Region:     {location}")
    print(f"   Bucket:     {staging_bucket}")
    
    aiplatform.init(project=project_id, location=location, staging_bucket=staging_bucket)
    
    env_vars = {
        "GOOGLE_CLOUD_PROJECT": project_id,
        "DEFAULT_GEMINI_MODEL": "gemini-3.1-flash-lite",
        "STAGING_BUCKET": staging_bucket
    }
    
    agent_instance = SreBenjaminAgent(config=env_vars)
    
    remote_agent = reasoning_engines.ReasoningEngine.create(
        agent_instance,
        requirements=[
            "google-cloud-aiplatform[agent_engines]>=1.133.0",
            "google-genai>=1.57.0",
            "python-dotenv>=1.0.0",
            "jinja2>=3.1.0",
            "pyyaml>=6.0.0",
            "opentelemetry-api>=1.37.0",
            "opentelemetry-sdk>=1.37.0",
            "opentelemetry-exporter-gcp-trace>=1.6.0",
            "opentelemetry-instrumentation-logging>=0.58b0",
            "structlog>=25.5.0"
        ],
        extra_packages=[
            "./src",
            "./run_simulation.py"
        ],
        display_name="sre-benjamin-agent",
        description="SRE Incident Command System reasoning agent",
    )
    
    print(f"✅ Deployment Complete!")
    print(f"   Resource Name: {remote_agent.resource_name}")
    
    AGENT_ID_FILE = "latest_agent.txt"
    with open(AGENT_ID_FILE, "w") as f:
        f.write(remote_agent.resource_name)
    print(f"Saved resource name to: {AGENT_ID_FILE}")

if __name__ == "__main__":
    deploy()
