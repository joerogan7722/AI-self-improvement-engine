import argparse
from pathlib import Path
import os
import sys
import yaml
import logging # New import
import json # New import for JSON formatter
from datetime import datetime # New import for JSON formatter
from pydantic import ValidationError # Import ValidationError

from .config import MainConfig, LoggingConfig
from .core.engine import Engine

# Set up a logger for the CLI module
logger = logging.getLogger(__name__)

class JsonFormatter(logging.Formatter):
    """A custom logging formatter that outputs logs in JSON format."""
    def format(self, record):
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            log_record["stack_info"] = self.formatStack(record.stack_info)

        return json.dumps(log_record)

def _setup_logging(log_config: LoggingConfig):
    """Configures the root logger based on the provided logging configuration."""
    level_map = {level: getattr(logging, level.upper()) for level in ["debug", "info", "warning", "error", "critical"]}
    log_level = level_map.get(log_config.level.lower(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    for handler in root_logger.handlers[:]: # Clear existing handlers
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level)

    if log_config.format == "json":
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if log_file is specified)
    if log_config.log_file:
        log_file_path = Path(log_config.log_file)
        log_file_path.parent.mkdir(parents=True, exist_ok=True) # Ensure log directory exists
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    logger.info("Logging configured to level '%s' with format '%s'. Outputting to console and %s.", 
                log_config.level, log_config.format, log_config.log_file if log_config.log_file else "console only")

def main():
    parser = argparse.ArgumentParser(description="AI Self-Extending Engine")
    parser.add_argument("--config", type=str, default="config/engine_config.yaml",
                        help="Path to the engine configuration file.")
    parser.add_argument("--verbose", action="store_true", 
                        help="Enable verbose logging (DEBUG level). Overrides config.")
    args = parser.parse_args()

    # Load and validate configuration
    config: MainConfig
    try:
        config_path = Path(args.config)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found at {config_path.absolute()}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        config = MainConfig(**config_data) # Use MainConfig for validation

        # Override log level if --verbose flag is set
        if args.verbose:
            config.logging.level = "DEBUG"

        # Configure logging as early as possible after config is loaded
        _setup_logging(config.logging)

    except FileNotFoundError as e:
        logger.error("Error: Config file not found at %s. %s", config_path.absolute(), e, exc_info=False)
        sys.exit(1)
    except ValidationError as e:
        logger.error("Configuration validation error: %s", e, exc_info=True)
        sys.exit(1)
    except Exception as e:
        logger.error("Error loading or parsing configuration: %s", e, exc_info=True)
        sys.exit(1)

    engine = Engine(config)
    engine.run_cycles()

if __name__ == "__main__":
    main()
