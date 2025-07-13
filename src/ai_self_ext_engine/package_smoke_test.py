import os
import tempfile
from pathlib import Path

# Relative imports for the package
from .config import MainConfig, EngineSectionConfig, ModelSectionConfig, LoggingConfig
from .core.engine import Engine

def run_smoke_test():
    """
    Executes a basic smoke test for the AI Self-Extending Engine package.
    This test verifies that the Engine can be instantiated with a minimal
    configuration and its dependencies can be resolved.
    It uses temporary directories and mocks API keys to avoid side effects.
    """
    print("Running AI Self-Extending Engine package smoke test...")

    # Create temporary directories for config paths
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        temp_goals_path = tmp_path / "goals.json"
        temp_memory_path = tmp_path / "memory"
        temp_code_dir = tmp_path / "src"
        temp_prompts_dir = tmp_path / "prompts"
        temp_prompts_dir.mkdir(parents=True, exist_ok=True) # Ensure it exists for config validation

        # Minimal valid config for instantiation
        dummy_config_data = {
            "version": 1,
            "engine": {
                "code_dir": str(temp_code_dir),
                "max_cycles": 1,
                "memory_path": str(temp_memory_path),
                "goals_path": str(temp_goals_path),
                "prompts_dir": str(temp_prompts_dir)
            },
            "model": {
                "api_key_env": "AI_SELF_EXT_ENGINE_DUMMY_KEY",
                "model_name": "dummy-model"
            },
            "roles": [], # No actual roles needed for basic instantiation test
            "plugins": {},
            "logging": {
                "level": "INFO",
                "format": "plain"
            }
        }

        # Temporarily set dummy API key to allow ModelClient initialization
        original_env_value = os.environ.get(dummy_config_data["model"]["api_key_env"])
        os.environ[dummy_config_data["model"]["api_key_env"]] = "sk-dummy-key-for-test-only"

        try:
            config = MainConfig(**dummy_config_data)
            engine = Engine(config)
            print("Engine instantiated successfully.")
        finally:
            # Clean up dummy API key
            if original_env_value is not None:
                os.environ[dummy_config_data["model"]["api_key_env"]] = original_env_value
            else:
                del os.environ[dummy_config_data["model"]["api_key_env"]]

    print("AI Self-Extending Engine package smoke test completed successfully.")

if __name__ == "__main__":
    run_smoke_test()
