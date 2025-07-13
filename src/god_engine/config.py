"""
Load configuration and validate survival schemas.
"""
import yaml
from pathlib import Path


def load_config(config_path: Path = Path("config.yaml")):
    """Loads and validates the configuration from a YAML file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found at {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Basic schema validation (can be expanded)
    if "directives" not in config or "resource_schemas" not in config:
        raise ValueError("Invalid configuration: missing 'directives'"
                         " or 'resource_schemas'")

    return config
