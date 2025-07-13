import subprocess
import os # Import os
import logging # New import
from typing import Any, Dict, Optional
from ai_self_ext_engine.core.role import Role, Context
from ai_self_ext_engine.config import MainConfig # Use MainConfig

logger = logging.getLogger(__name__) # New logger

class TestRole(Role):
    """
    Role responsible for running tests on the codebase and updating the context
    with the test results.
    """
    def __init__(self, config: MainConfig, model_client: Any): # model_client not directly used here but passed for consistency
        self.config = config

    def run(self, context: Context) -> Context:
        if context.should_abort:
            logger.info("TestRole: Context aborted. Skipping tests.")
            return context

        logger.info("TestRole: Running tests...")
        
        try:
            # Assuming pytest is installed and tests are discoverable in code_dir
            # For a more robust solution, we would use the Plugin interface
            # to determine the correct test runner for the language/framework.
            result = subprocess.run(
                ["pytest"],
                check=True,
                cwd=os.getcwd(), # Use current working directory
                capture_output=True,
                text=True # Capture output as text
            )
            context.test_results = {
                "passed": True,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            context.accepted = True # Tests passed, so changes are provisionally accepted
            logger.info("TestRole: Tests passed successfully.")

        except subprocess.CalledProcessError as e:
            context.test_results = {
                "passed": False,
                "stdout": e.stdout,
                "stderr": e.stderr,
                "returncode": e.returncode
            }
            context.accepted = False # Tests failed, so changes are not accepted
            logger.error("TestRole: Tests failed. Output:\n%s\nErrors:\n%s", e.stdout, e.stderr)
            # Optionally, revert changes if tests fail. This can be handled by SelfReviewRole.
            # self._git_reset_all(context.code_dir) # Moved to SelfReviewRole for decision making
        except FileNotFoundError:
            logger.error("TestRole: Pytest command not found. Please ensure pytest is installed.")
            context.should_abort = True
        except Exception as e:
            logger.exception("TestRole: An unexpected error occurred during testing: %s", e)
            context.should_abort = True

        return context
