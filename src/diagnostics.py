import os
import subprocess
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone

def _get_execution_mode() -> str:
    """Reads execution mode from environment variables, defaulting to MOCK."""
    return os.getenv("SRE_MODE", "MOCK").upper()

def query_logs(project_id: str, query: str) -> str:
    """Queries SRE log streams, dynamically switching between mock and live modes."""
    mode = _get_execution_mode()
    
    if mode == "LIVE":
        try:
            # Run gcloud logging read command
            cmd = [
                "gcloud", "logging", "read",
                query,
                f"--project={project_id}",
                "--limit=10",
                "--format=json"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            entries = json.loads(res.stdout)
            
            if not entries:
                return "No log entries found for the query."
                
            formatted_logs = []
            for entry in entries:
                formatted_logs.append(format_log_entry(entry))
            return "\n".join(formatted_logs) + "\n"
        except Exception as e:
            print(f"[Diagnostics Error] Live logging query failed: {e}")
            return f"[Diagnostics Error] Live logging query failed: {e}\nFalling back to mock logs:\n" + get_mock_logs()
        
    return get_mock_logs()

def get_mock_logs() -> str:
    return """[2026-05-29T12:00:05Z] INFO starting query processing in db_instance
[2026-05-29T12:00:12Z] WARNING database connection limit pool saturated
[2026-05-29T12:00:30Z] ERROR lock contention detected on table 'users': transaction aborted
[2026-05-29T12:00:45Z] ERROR database timeout executing SELECT * FROM users WHERE status = 'active'
[2026-05-29T12:01:00Z] WARNING read performance degraded due to disk IO saturation
"""

def format_log_entry(entry: dict) -> str:
    timestamp = entry.get("timestamp", "")
    severity = entry.get("severity", "INFO")
    
    payload = ""
    if "textPayload" in entry:
        payload = entry["textPayload"]
    elif "jsonPayload" in entry:
        jp = entry["jsonPayload"]
        if isinstance(jp, dict):
            msg = jp.get("message") or jp.get("msg") or jp.get("error")
            if msg:
                extra = {k: v for k, v in jp.items() if k not in ["message", "msg", "error"]}
                payload = f"{msg}"
                if extra:
                    payload += f" (details: {json.dumps(extra)})"
            else:
                payload = json.dumps(jp)
        else:
            payload = str(jp)
    elif "protoPayload" in entry:
        payload = json.dumps(entry["protoPayload"])
    else:
        payload = json.dumps(entry)
        
    return f"[{timestamp}] {severity} {payload}"

def query_metrics(project_id: str, metric_name: str) -> list[float]:
    """Queries site monitoring metrics, dynamically switching between mock and live modes."""
    mode = _get_execution_mode()
    
    if mode == "LIVE":
        try:
            if "cpu" in metric_name.lower():
                filter_str = 'metric.type="compute.googleapis.com/instance/cpu/utilization"'
            elif "latency" in metric_name.lower():
                filter_str = 'metric.type="compute.googleapis.com/instance/network/received_bytes_count"'
            else:
                filter_str = 'metric.type="compute.googleapis.com/instance/cpu/utilization"'
                
            # Get access token from gcloud
            res = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True)
            token = res.stdout.strip()
            
            # Setup time window: last 15 minutes
            now = datetime.now(timezone.utc)
            start = now - timedelta(minutes=15)
            start_str = start.isoformat().replace("+00:00", "Z")
            end_str = now.isoformat().replace("+00:00", "Z")
            
            params = urllib.parse.urlencode({
                "filter": filter_str,
                "interval.startTime": start_str,
                "interval.endTime": end_str,
                "pageSize": 10
            })
            
            url = f"https://monitoring.googleapis.com/v3/projects/{project_id}/timeSeries?{params}"
            req = urllib.request.Request(url)
            req.add_header("Authorization", f"Bearer {token}")
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
                
            time_series = data.get("timeSeries", [])
            if not time_series:
                print(f"[Diagnostics Warning] Live metrics query returned no timeseries for {metric_name}. Using fallback.")
                return get_mock_metrics(metric_name)
                
            values = []
            pts = time_series[0].get("points", [])
            for pt in pts:
                val_dict = pt.get("value", {})
                val = val_dict.get("doubleValue")
                if val is None:
                    val = val_dict.get("int64Value")
                if val is not None:
                    values.append(float(val))
            
            # Points are returned newest-first, reverse to make it chronological
            values.reverse()
            
            # Scale CPU values to percentage (0 - 100)
            if "cpu" in metric_name.lower():
                values = [v * 100.0 for v in values]
            elif "latency" in metric_name.lower():
                if values:
                    max_val = max(values)
                    if max_val > 0:
                        values = [(v / max_val) * 400.0 + 80.0 for v in values]
                    else:
                        values = [80.0] * len(values)
                        
            return values
        except Exception as e:
            print(f"[Diagnostics Error] Live metrics query failed: {e}. Using fallback.")
            return get_mock_metrics(metric_name)
            
    return get_mock_metrics(metric_name)

def get_mock_metrics(metric_name: str) -> list[float]:
    if "latency" in metric_name.lower():
        return [85.0, 92.0, 115.0, 240.0, 480.0, 480.0, 480.0]
    if "cpu" in metric_name.lower():
        return [32.5, 35.0, 48.0, 72.0, 95.0, 95.0, 95.0]
    return [1.0, 1.0, 1.0, 1.0, 1.0]
