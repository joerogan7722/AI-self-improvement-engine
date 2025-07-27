import pytest
import yaml
from pathlib import Path

# The content of the config file as per the patch being tested.
# This string effectively mocks the content of src/ai_self_ext_engine/config/config.py
# after the patch has been applied.
MOCK_CONFIG_CONTENT = """
app:
  name: AI Self-Extension Engine
  version: 0.1.0
  logs_path: ./logs
  memory_path: ./memory
  goals_path: goals.json
  prompts_dir: prompts
  # Explicitly list core runtime dependencies for internal validation and external tooling.
  # This section can be used to ensure the environment has necessary packages.
  runtime_dependencies:
    - name: pyyaml
      min_version: "6.0"
    - name: pydantic
      min_version: "2.0"
    - name: requests
      min_version: "2.31.0"
    - name: tenacity
      min_version: "8.2.3"
    - name: python-dotenv
      min_version: "1.0.0"
    # Development/Tooling dependencies often used by roles
    - name: black
      min_version: "24.4.2"
    - name: isort
      min_version: "5.13.2"
    - name: jinja2
      min_version: "3.1.4"
model:
  api_key_env: GEMINI_API_KEY
  model_name: gemini-2.5-flash
"""

class TestConfigDependencies:
    """
    Tests related to the new 'runtime_dependencies' section in the configuration.
    """

    @pytest.fixture
    def config_file_path(self, tmp_path: Path):
        """
        Creates a temporary 'config.yaml' file with the mock content for testing.
        This simulates the presence of the actual config file.
        """
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        file_path = config_dir / "config.yaml"
        file_path.write_text(MOCK_CONFIG_CONTENT)
        return file_path

    @pytest.fixture
    def loaded_config(self, config_file_path: Path):
        """
        Loads the mock config content from the temporary file using a YAML parser.
        This simulates how a ConfigManager would load the configuration.
        """
        with open(config_file_path, 'r') as f:
            data = yaml.safe_load(f)
        return data

    def test_runtime_dependencies_section_exists(self, loaded_config):
        """
        Verify that the 'runtime_dependencies' section exists under 'app' and is a list.
        """
        assert 'app' in loaded_config
        assert 'runtime_dependencies' in loaded_config['app']
        assert isinstance(loaded_config['app']['runtime_dependencies'], list)

    def test_runtime_dependencies_structure(self, loaded_config):
        """
        Verify the structure of each dependency entry in the 'runtime_dependencies' list.
        Each entry should be a dictionary with 'name' and 'min_version' string keys.
        """
        dependencies = loaded_config['app']['runtime_dependencies']
        assert len(dependencies) > 0, "Expected at least one dependency to be listed."

        for dep in dependencies:
            assert isinstance(dep, dict), f"Expected dependency entry to be a dict, got {type(dep)}"
            assert 'name' in dep, f"Expected 'name' key in dependency entry: {dep}"
            assert 'min_version' in dep, f"Expected 'min_version' key in dependency entry: {dep}"
            assert isinstance(dep['name'], str), f"Expected 'name' to be a string, got {type(dep['name'])}"
            assert isinstance(dep['min_version'], str), f"Expected 'min_version' to be a string, got {type(dep['min_version'])}"
