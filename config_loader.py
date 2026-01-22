"""Configuration loader for OPA_Machine ecosystem.

Provides centralized configuration management from state.yaml,
preventing hardcoded defaults that can cause issues like OPA-324.

Usage:
    from config_loader import get_db_config
    
    config = get_db_config("capacity")
    # Returns: {"host": "localhost", "port": 5434, "user": "opa_user", ...}
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional


def load_infrastructure_config() -> Dict[str, Any]:
    """Load state.yaml from opa-infrastructure-state repository.
    
    Returns:
        dict: Full infrastructure state configuration
        
    Raises:
        FileNotFoundError: If state.yaml doesn't exist
        yaml.YAMLError: If state.yaml is malformed
    """
    state_path = Path(__file__).parent / "state.yaml"
    
    if not state_path.exists():
        raise FileNotFoundError(
            f"state.yaml not found at {state_path}. "
            "Make sure opa-infrastructure-state is cloned."
        )
    
    try:
        with open(state_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Failed to parse state.yaml: {e}")


def get_db_config(module: str) -> Dict[str, Any]:
    """Get database configuration for a specific module.
    
    Args:
        module: Module name (quotes, capacity, prediction, intention, monitoring)
        
    Returns:
        dict: Database configuration with keys:
            - host: Database host (default: localhost)
            - port: Database port (from state.yaml)
            - user: Database user (from state.yaml)
            - password: Database password (from state.yaml)
            - database: Database name (from state.yaml)
            
    Raises:
        ValueError: If module not found in state.yaml
        KeyError: If required configuration keys missing
        
    Example:
        >>> config = get_db_config("capacity")
        >>> print(config["port"])
        5434
    """
    state = load_infrastructure_config()
    container_key = f"timescaledb_{module}"
    
    if container_key not in state.get("containers", {}):
        available = [k.replace("timescaledb_", "") 
                     for k in state.get("containers", {}).keys() 
                     if k.startswith("timescaledb_")]
        raise ValueError(
            f"Module '{module}' not found in state.yaml. "
            f"Available modules: {', '.join(available)}"
        )
    
    container = state["containers"][container_key]
    creds = container.get("credentials", {})
    
    # Validate required keys
    required_keys = ["user", "password", "database"]
    missing = [k for k in required_keys if k not in creds]
    if missing:
        raise KeyError(
            f"Missing required credential keys for {module}: {', '.join(missing)}"
        )
    
    return {
        "host": "localhost",  # Always localhost for Docker containers
        "port": container["port"],
        "user": creds["user"],
        "password": creds["password"],
        "database": creds["database"]
    }


def get_redis_config() -> Dict[str, Any]:
    """Get Redis configuration from state.yaml.
    
    Returns:
        dict: Redis configuration with keys:
            - host: Redis host (default: localhost)
            - port: Redis port (from state.yaml)
            
    Raises:
        ValueError: If Redis not configured in state.yaml
        
    Example:
        >>> config = get_redis_config()
        >>> print(config["port"])
        6381
    """
    state = load_infrastructure_config()
    
    if "redis" not in state.get("containers", {}):
        raise ValueError("Redis not configured in state.yaml")
    
    redis = state["containers"]["redis"]
    
    return {
        "host": "localhost",
        "port": redis["port"]
    }


def get_api_port(module: str) -> int:
    """Get API port for a specific module.
    
    Args:
        module: Module name (quotes, capacity, prediction, etc.)
        
    Returns:
        int: API port number
        
    Raises:
        ValueError: If module not found in ports configuration
        
    Example:
        >>> port = get_api_port("capacity")
        >>> print(port)
        8001
    """
    state = load_infrastructure_config()
    ports = state.get("ports", {})
    
    # Find port by searching description
    for port, desc in ports.items():
        if isinstance(desc, str) and f"{module}-api" in desc.lower():
            return int(port)
    
    raise ValueError(
        f"API port for module '{module}' not found in state.yaml ports"
    )


def list_known_conflicts() -> list:
    """List known infrastructure conflicts from state.yaml.
    
    Returns:
        list: List of conflict dicts with id, severity, description, workaround
        
    Example:
        >>> conflicts = list_known_conflicts()
        >>> for c in conflicts:
        ...     print(f"{c['severity']}: {c['description']}")
    """
    state = load_infrastructure_config()
    return state.get("known_conflicts", [])


def validate_local_env(module: str, env_vars: Dict[str, str]) -> Dict[str, Any]:
    """Validate local environment variables against state.yaml.
    
    Args:
        module: Module name (quotes, capacity, etc.)
        env_vars: Dict of current environment variables
        
    Returns:
        dict: Validation result with keys:
            - valid: bool (True if all match)
            - discrepancies: list of (key, env_value, expected_value) tuples
            - missing: list of missing env vars
            
    Example:
        >>> import os
        >>> result = validate_local_env("capacity", {
        ...     "DB_PORT": os.getenv("DB_PORT"),
        ...     "DB_USER": os.getenv("DB_USER")
        ... })
        >>> if not result["valid"]:
        ...     print("Discrepancies:", result["discrepancies"])
    """
    config = get_db_config(module)
    
    mapping = {
        "DB_PORT": str(config["port"]),
        "DB_USER": config["user"],
        "DB_PASSWORD": config["password"],
        "DB_NAME": config["database"]
    }
    
    discrepancies = []
    missing = []
    
    for env_key, expected_value in mapping.items():
        env_value = env_vars.get(env_key)
        
        if env_value is None:
            missing.append(env_key)
        elif str(env_value) != str(expected_value):
            discrepancies.append((env_key, env_value, expected_value))
    
    return {
        "valid": len(discrepancies) == 0 and len(missing) == 0,
        "discrepancies": discrepancies,
        "missing": missing
    }


if __name__ == "__main__":
    # Self-test
    print("🔍 Testing config_loader.py...")
    print()
    
    try:
        # Test 1: Load infrastructure config
        print("✓ Loading state.yaml...")
        state = load_infrastructure_config()
        print(f"  Version: {state['version']}")
        print()
        
        # Test 2: Get DB config for each module
        print("✓ Testing DB configurations:")
        for module in ["quotes", "capacity"]:
            try:
                config = get_db_config(module)
                print(f"  {module}: port={config['port']}, user={config['user']}, db={config['database']}")
            except ValueError as e:
                print(f"  {module}: ⚠️ {e}")
        print()
        
        # Test 3: List conflicts
        print("✓ Known conflicts:")
        conflicts = list_known_conflicts()
        for c in conflicts:
            print(f"  [{c['severity']}] {c['description']}")
        print()
        
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
