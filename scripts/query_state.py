#!/usr/bin/env python3
"""Query infrastructure state from state.yaml

Usage:
    python query_state.py db                  # Get database config
    python query_state.py ports               # List all ports
    python query_state.py port 5433          # Check specific port
    python query_state.py credentials <container>  # Get credentials
    python query_state.py service <repo>     # Get service info
    python query_state.py conflicts          # List known conflicts
"""
import yaml
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any

def load_state() -> Dict[str, Any]:
    """Load state.yaml from repository root"""
    state_file = Path(__file__).parent.parent / "state.yaml"
    if not state_file.exists():
        print(f"Error: state.yaml not found at {state_file}", file=sys.stderr)
        sys.exit(1)
    return yaml.safe_load(state_file.read_text())

def get_db_config(db_name: str = "timescaledb_quotes") -> Optional[Dict[str, Any]]:
    """Get database configuration"""
    state = load_state()
    return state["containers"].get(db_name)

def get_all_ports() -> Dict[int, str]:
    """Get all port assignments"""
    state = load_state()
    return state["ports"]

def get_port_info(port: int) -> Optional[str]:
    """Get info for specific port"""
    state = load_state()
    return state["ports"].get(port)

def get_credentials(container: str) -> Optional[Dict[str, str]]:
    """Get credentials for container"""
    state = load_state()
    container_info = state["containers"].get(container)
    return container_info.get("credentials") if container_info else None

def get_service_info(repo: str) -> Optional[Dict[str, Any]]:
    """Get service status info"""
    state = load_state()
    return state["services"].get(repo)

def get_conflicts() -> list:
    """Get known conflicts"""
    state = load_state()
    return state.get("known_conflicts", [])

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    try:
        if cmd == "db":
            db_name = sys.argv[2] if len(sys.argv) > 2 else "timescaledb_quotes"
            result = get_db_config(db_name)
            
        elif cmd == "ports":
            result = get_all_ports()
            
        elif cmd == "port":
            if len(sys.argv) < 3:
                print("Error: port number required", file=sys.stderr)
                sys.exit(1)
            port = int(sys.argv[2])
            result = {port: get_port_info(port)}
            
        elif cmd == "credentials":
            if len(sys.argv) < 3:
                print("Error: container name required", file=sys.stderr)
                sys.exit(1)
            container = sys.argv[2]
            result = get_credentials(container)
            
        elif cmd == "service":
            if len(sys.argv) < 3:
                print("Error: service name required", file=sys.stderr)
                sys.exit(1)
            service = sys.argv[2]
            result = get_service_info(service)
            
        elif cmd == "conflicts":
            result = get_conflicts()
            
        else:
            print(f"Error: Unknown command '{cmd}'", file=sys.stderr)
            print(__doc__)
            sys.exit(1)
        
        if result is None:
            print(f"Not found", file=sys.stderr)
            sys.exit(1)
            
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
