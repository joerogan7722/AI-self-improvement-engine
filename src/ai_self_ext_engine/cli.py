import argparse
import json  # New import for JSON formatter
import logging  # New import
import os
import sys
from datetime import datetime  # New import for JSON formatter
from pathlib import Path

import yaml
from pydantic import ValidationError  # Import ValidationError

from .config import LoggingConfig, MainConfig
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

# AI-generated improvements:
import subprocess  # New import for running external commands


def _run_tests_with_coverage(test_target: str, config_file_path: Path) -> int:
    """
    Runs pytest with coverage and generates reports.
    Args:
        test_target: The path to run tests on (e.g., '.', 'tests/').
        config_file_path: The path to the main configuration file, used to determine
                          the base directory for placing reports (e.g., 'config/engine_config.yaml').
    Returns:
        The exit code of the pytest process.
    """
    try:
        # Determine the base directory for reports (project root, assuming config is in <project_root>/config/)
        project_root_for_reports = config_file_path.parent.parent
        report_dir = project_root_for_reports / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        coverage_xml_path = report_dir / "coverage.xml"
        coverage_html_dir = report_dir / "htmlcov"
        # The project source directory to measure coverage for is src/ai_self_ext_engine/
        coverage_measure_path = Path(__file__).parent.as_posix()
        cmd = [
            sys.executable, "-m", "pytest",
            test_target,
            f"--cov={coverage_measure_path}",
            "--cov-report=term-missing",
            f"--cov-report=xml:{coverage_xml_path}",
            f"--cov-report=html:{coverage_html_dir}",
            "--durations=0",
        ]
        logger.info("Running tests with coverage: %s", " ".join(cmd))
        process = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if process.stdout: logger.info("Pytest Output:\n%s", process.stdout)
        if process.stderr: logger.error("Pytest Errors:\n%s", process.stderr)
        logger.info("Coverage XML report generated at: %s", coverage_xml_path.absolute())
        logger.info("Coverage HTML report generated at: %s", coverage_html_dir.absolute())
        return process.returncode
    except FileNotFoundError:
        logger.error("Error: 'pytest' or 'python' command not found. Please ensure pytest and pytest-cov are installed (`pip install pytest pytest-cov`).")
        return 1
    except Exception as e:
        logger.exception("An unexpected error occurred during test execution: %s", e)
        return 1
    parser.add_argument("--test", nargs="?", const=".", default=None,
                        help="Run tests with coverage. Optionally specify a path or '.' for all tests. "
                             "Generates XML and HTML coverage reports in a 'reports/' directory at the project root.")
    # Handle --test argument, if present
    if args.test is not None:
        logger.info(f"Test mode activated. Running tests in '{args.test}' with coverage.")
        exit_code = _run_tests_with_coverage(args.test, config_path)
        sys.exit(exit_code)

from typing import Optional

# AI-generated improvements:
import typer
from src.ai_self_ext_engine.test_utils import run_tests_with_coverage

app = typer.Typer()
logger = logging.getLogger(__name__)
@app.command(name="test", help="Run unit tests and generate a comprehensive code coverage report.")
def run_tests_command(
    tests_path: Optional[Path] = typer.Argument(
        None,
        help="Path to tests (file or directory). Defaults to 'tests' directory if exists.",
        exists=True,
        file_okay=True,
        dir_okay=True,
        readable=True,
    ),
    coverage_report_dir: Path = typer.Option(
        Path("coverage_reports"),
        "--coverage-report-dir",
        "-crd",
        help="Directory to save the code coverage XML report.",
        writable=True,
    ),
    project_root: Path = typer.Option(
        Path("."),
        "--project-root",
        "-pr",
        help="The root directory of the project for coverage measurement.",
        exists=True,
        dir_okay=True,
        readable=True,
    ),
):
    """
    Runs unit tests and generates a comprehensive code coverage report.
    """
    if tests_path is None:
        # Prioritize 'tests' in project root, then 'src/ai_self_ext_engine/tests', then 'src/tests'
        if (project_root / "tests").is_dir():
            tests_path = project_root / "tests"
        elif (project_root / "src" / "ai_self_ext_engine" / "tests").is_dir():
             tests_path = project_root / "src" / "ai_self_ext_engine" / "tests"
        elif (project_root / "src" / "tests").is_dir():
             tests_path = project_root / "src" / "tests"
        else:
            logger.error("No specific tests path provided and no 'tests' directory found in common locations. Please specify with 'ai-self-ext-engine test PATH_TO_TESTS'")
            raise typer.Exit(code=1)
    logger.info(f"Running tests from: {tests_path.resolve()}")
    logger.info(f"Generating coverage report in: {coverage_report_dir.resolve()}")
    coverage_report_dir.mkdir(parents=True, exist_ok=True)
    results = run_tests_with_coverage(project_root=project_root, test_path=tests_path, coverage_report_dir=coverage_report_dir)
    if results['success']:
        logger.info(f"\nTests completed successfully.")
        if results.get('coverage_xml_path'):
            logger.info(f"Code coverage report generated at: {results['coverage_xml_path'].resolve()}")
            if results.get('coverage_data'):
                logger.info(f"Coverage Summary:")
                for metric, value in results['coverage_data'].items():
                    logger.info(f"  {metric.replace('_', ' ').title()}: {value}")
        raise typer.Exit(code=0)
    else:
        logger.error(f"\nTests failed!")
        logger.error(f"Stdout:\n{results['stdout']}")
        logger.error(f"Stderr:\n{results['stderr']}")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    main()