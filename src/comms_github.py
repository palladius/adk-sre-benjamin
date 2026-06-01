import os
import json
import urllib.request
from datetime import datetime, timezone

class GitHubTicketingEngine:
    def __init__(self, issue_file_path: str = None):
        self.token = os.getenv("GITHUB_TOKEN")
        self.repo = os.getenv("GITHUB_REPO") # Format: "owner/repo"
        self.issue_file_path = issue_file_path
        
    def _get_issue_path(self, incident_id: str) -> str:
        if self.issue_file_path:
            return self.issue_file_path
        return os.path.join("investigations", incident_id, "artifacts", "github_issue.json")
        
    def create_incident_issue(self, incident_id: str, trigger_event: str, project_id: str) -> str:
        """Creates a real or mock GitHub issue tracking ticket for the SRE incident."""
        title = f"🚨 ACTIVE: {incident_id} - {trigger_event}"
        body = f"An SRE incident has been declared active for project: `{project_id}`.\nTrigger event: `{trigger_event}`\n\nIncident timeline comments will be posted below automatically."
        
        # 1. Real GitHub API Dispatch
        if self.token and self.repo and not self.issue_file_path:
            try:
                url = f"https://api.github.com/repos/{self.repo}/issues"
                headers = {
                    "Authorization": f"token {self.token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "Project-Benjamin-SRE"
                }
                data = json.dumps({"title": title, "body": body}).encode("utf-8")
                req = urllib.request.Request(url, data=data, headers=headers, method="POST")
                
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 201:
                        res_data = json.loads(response.read().decode("utf-8"))
                        return str(res_data.get("number", "issue_1"))
            except Exception as e:
                print(f"[GitHub Comms Error] Failed to create live issue: {e}")
                
        # 2. Fallback Mock Mode
        mock_file = self._get_issue_path(incident_id)
        try:
            os.makedirs(os.path.dirname(mock_file), exist_ok=True)
            mock_payload = {
                "incident_id": incident_id,
                "issue_id": "issue_1",
                "title": title,
                "body": body,
                "status": "open",
                "comments": [],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            with open(mock_file, "w") as f:
                json.dump(mock_payload, f, indent=2)
            return "issue_1"
        except Exception as e:
            print(f"[GitHub Comms Error] Failed to create mock issue: {e}")
            return "issue_1"
            
    def add_issue_comment(self, issue_id: str, author: str, message: str, incident_id: str = None) -> bool:
        """Appends a progress log comment to the issue ticket."""
        body = f"**[{author}]** {message}"
        
        # 1. Real GitHub API Comment
        if self.token and self.repo and not self.issue_file_path and issue_id != "issue_1":
            try:
                url = f"https://api.github.com/repos/{self.repo}/issues/{issue_id}/comments"
                headers = {
                    "Authorization": f"token {self.token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "Project-Benjamin-SRE"
                }
                data = json.dumps({"body": body}).encode("utf-8")
                req = urllib.request.Request(url, data=data, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 201:
                        return True
            except Exception as e:
                print(f"[GitHub Comms Error] Failed to add live comment: {e}")
                
        # 2. Fallback Mock Mode
        mock_file = self._get_issue_path(incident_id or "INC-UNKNOWN")
        if os.path.exists(mock_file):
            try:
                with open(mock_file, "r") as f:
                    data = json.load(f)
                    
                data["comments"].append({
                    "author": author,
                    "body": message,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                with open(mock_file, "w") as f:
                    json.dump(data, f, indent=2)
                return True
            except Exception as e:
                print(f"[GitHub Comms Error] Failed to add mock comment: {e}")
        return False
        
    def close_incident_issue(self, issue_id: str, summary: str, incident_id: str = None) -> bool:
        """Closes the tracking ticket upon successful incident resolution."""
        closing_comment = f"Incident Resolved: {summary}"
        
        # 1. Real GitHub API Issue Close
        if self.token and self.repo and not self.issue_file_path and issue_id != "issue_1":
            try:
                # Add final comment first
                self.add_issue_comment(issue_id, "System", closing_comment, incident_id)
                
                url = f"https://api.github.com/repos/{self.repo}/issues/{issue_id}"
                headers = {
                    "Authorization": f"token {self.token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "Project-Benjamin-SRE"
                }
                data = json.dumps({"state": "closed"}).encode("utf-8")
                req = urllib.request.Request(url, data=data, headers=headers, method="PATCH")
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        return True
            except Exception as e:
                print(f"[GitHub Comms Error] Failed to close live issue: {e}")
                
        # 2. Fallback Mock Mode
        mock_file = self._get_issue_path(incident_id or "INC-UNKNOWN")
        if os.path.exists(mock_file):
            try:
                with open(mock_file, "r") as f:
                    data = json.load(f)
                    
                data["status"] = "closed"
                data["comments"].append({
                    "author": "System",
                    "body": f"Incident Resolved: {summary}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                with open(mock_file, "w") as f:
                    json.dump(data, f, indent=2)
                return True
            except Exception as e:
                print(f"[GitHub Comms Error] Failed to close mock issue: {e}")
        return False
