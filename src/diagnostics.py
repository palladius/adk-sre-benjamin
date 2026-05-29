import os

def _get_execution_mode() -> str:
    """Reads execution mode from environment variables, defaulting to MOCK."""
    return os.getenv("SRE_MODE", "MOCK").upper()

def query_logs(project_id: str, query: str) -> str:
    """Queries SRE log streams, dynamically switching between mock and live modes."""
    mode = _get_execution_mode()
    
    if mode == "LIVE":
        raise NotImplementedError("Live GCP logging connectors not configured in this version.")
        
    # Standard super-fast mock SRE log output
    return f"""[2026-05-29T12:00:05Z] INFO starting query processing in db_instance
[2026-05-29T12:00:12Z] WARNING database connection limit pool saturated
[2026-05-29T12:00:30Z] ERROR lock contention detected on table 'users': transaction aborted
[2026-05-29T12:00:45Z] ERROR database timeout executing SELECT * FROM users WHERE status = 'active'
[2026-05-29T12:01:00Z] WARNING read performance degraded due to disk IO saturation
"""

def query_metrics(project_id: str, metric_name: str) -> list[float]:
    """Queries site monitoring metrics, dynamically switching between mock and live modes."""
    mode = _get_execution_mode()
    
    if mode == "LIVE":
        raise NotImplementedError("Live GCP Cloud Monitoring connectors not configured in this version.")
        
    # Standard super-fast mock latency/resource measurements
    if "latency" in metric_name.lower():
        return [85.0, 92.0, 115.0, 240.0, 480.0, 480.0, 480.0]
        
    if "cpu" in metric_name.lower():
        return [32.5, 35.0, 48.0, 72.0, 95.0, 95.0, 95.0]
        
    return [1.0, 1.0, 1.0, 1.0, 1.0]
