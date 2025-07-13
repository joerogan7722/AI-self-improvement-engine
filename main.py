import argparse
from pathlib import Path
import os
import sys
import yaml # Import yaml

# Add src directory to PYTHONPATH so modules under src can be imported
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import EngineConfig
from src.core import Engine, Context, Role, Plugin

def main():
    parser = argparse.ArgumentParser(description="AI Self-Extending Engine")
    parser.add_argument("--config", type=str, default="config/engine_config.yaml",
                        help="Path to the engine configuration file.")
    # Add other CLI arguments as needed, e.g., --max-cycles, --code-dir
    args = parser.parse_args()

    # Load configuration
    try:
        config_path = Path(args.config)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found at {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        config = EngineConfig(**config_data)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading or parsing configuration: {e}")
        sys.exit(1)

    engine = Engine(config)
    engine.run_cycles()

if __name__ == "__main__":
    main()
