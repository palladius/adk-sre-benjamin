import os
import subprocess

def find_repo_root(start_dir: str) -> str:
    """Finds the root directory containing the .git folder by searching upwards."""
    current = os.path.abspath(start_dir)
    while True:
        if os.path.exists(os.path.join(current, ".git")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            # Return original if we hit the file system root without finding .git
            return os.path.abspath(start_dir)
        current = parent

def commit_scribe_changes(incident_folder: str, message: str) -> str:
    """Automates Git versioning for Scribe's incident timeline and state files.
    
    Stages state.md and timeline.md, commits them, and returns the resulting commit hash.
    """
    state_path = os.path.abspath(os.path.join(incident_folder, "state.md"))
    timeline_path = os.path.abspath(os.path.join(incident_folder, "timeline.md"))
    
    # Dynamically find the git repository root
    repo_dir = find_repo_root(incident_folder)
    
    # Stage Scribe chronicles
    subprocess.run(["git", "add", state_path, timeline_path], cwd=repo_dir, capture_output=True)
    
    # Execute Git Commit
    res = subprocess.run(["git", "commit", "-m", message], cwd=repo_dir, capture_output=True, text=True)
    
    # Query resulting commit hash
    hash_res = subprocess.run(["git", "log", "-1", "--format=%H"], cwd=repo_dir, capture_output=True, text=True)
    return hash_res.stdout.strip()

def add_git_note(incident_folder: str, commit_hash: str, note_content: str) -> None:
    """Attaches an SRE verification audit report or checklist to a Scribe checkpoint commit via Git Notes."""
    repo_dir = find_repo_root(incident_folder)
    subprocess.run(["git", "notes", "add", "-f", "-m", note_content, commit_hash], cwd=repo_dir, capture_output=True)

