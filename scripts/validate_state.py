#!/usr/bin/env python3
"""Validate state.yaml structure and consistency

Used by CI/CD to ensure state.yaml is valid.
"""
import yaml
import sys
from pathlib import Path
from datetime import datetime

def validate_state():
    """Validate state.yaml"""
    errors = []
    
    state_file = Path(__file__).parent.parent / "state.yaml"
    
    if not state_file.exists():
        print("Error: state.yaml not found")
        return False
    
    try:
        state = yaml.safe_load(state_file.read_text())
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML: {e}")
        return False
    
    # Check required keys
    required_keys = ["version", "last_updated", "containers", "ports", "services"]
    for key in required_keys:
        if key not in state:
            errors.append(f"Missing required key: {key}")
    
    # Validate version format
    if "version" in state:
        parts = state["version"].split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            errors.append(f"Invalid version format: {state['version']} (expected X.Y.Z)")
    
    # Validate last_updated is ISO 8601
    if "last_updated" in state:
        try:
            datetime.fromisoformat(state["last_updated"].replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"Invalid last_updated format: {state['last_updated']} (expected ISO 8601)")
    
    # Validate containers have required fields
    if "containers" in state:
        for name, container in state["containers"].items():
            if "port" not in container:
                errors.append(f"Container {name} missing 'port' field")
            if "status" not in container:
                errors.append(f"Container {name} missing 'status' field")
    
    # Validate ports are integers
    if "ports" in state:
        for port in state["ports"].keys():
            if not isinstance(port, int):
                errors.append(f"Port key must be integer: {port}")
    
    # Print results
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("state.yaml validation passed ✓")
        return True

if __name__ == "__main__":
    success = validate_state()
    sys.exit(0 if success else 1)
