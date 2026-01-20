#!/usr/bin/env python3
"""Update infrastructure state after service run

Usage:
    python update_state.py <repo> <commit> [issue1,issue2,...]
    
Example:
    python update_state.py opa-quotes-streamer abc1234 OPA-291,OPA-293
"""
import yaml
import sys
from datetime import datetime, timezone
from pathlib import Path
import subprocess
from typing import List, Optional

def load_state() -> dict:
    state_file = Path(__file__).parent.parent / "state.yaml"
    return yaml.safe_load(state_file.read_text())

def save_state(state: dict):
    state_file = Path(__file__).parent.parent / "state.yaml"
    state_file.write_text(yaml.dump(state, sort_keys=False, allow_unicode=True))

def update_service(repo: str, commit: str, issues: Optional[List[str]] = None):
    """Update service state"""
    state = load_state()
    
    # Update service info
    if "services" not in state:
        state["services"] = {}
    
    state["services"][repo] = {
        "last_run": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "last_commit": commit,
        "status": "operational",
        "issues_completed": issues or []
    }
    
    # Update global last_updated
    state["last_updated"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    state["updated_by"] = repo
    
    save_state(state)
    print(f"Updated state for {repo} @ {commit}")
    
    # Git commit & push
    try:
        subprocess.run(["git", "add", "state.yaml"], check=True, cwd=Path(__file__).parent.parent)
        subprocess.run(
            ["git", "commit", "-m", f"Update state: {repo} @ {commit}"],
            check=True,
            cwd=Path(__file__).parent.parent
        )
        subprocess.run(["git", "push", "origin", "main"], check=True, cwd=Path(__file__).parent.parent)
        print("State pushed to GitHub")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Git operations failed: {e}", file=sys.stderr)
        print("State updated locally but not pushed")

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    
    repo = sys.argv[1]
    commit = sys.argv[2]
    issues = sys.argv[3].split(",") if len(sys.argv) > 3 else None
    
    update_service(repo, commit, issues)

if __name__ == "__main__":
    main()
