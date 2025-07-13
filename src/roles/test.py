import subprocess
from typing import Any, Dict, Optional
from src.core.role import Role, Context
from src.core import ModelClient, ModelCallError # Corrected import path
from src.config import EngineConfig

class TestRole(Role):
    """
    Role responsible for running tests on the codebase and updating the context
    with the test results.
    """
    def __init__(self, config: EngineConfig, model_client: Any): # model_client not directly used here but passed for consistency
        self.config = config

    def run(self, context: Context) -> Context:
        if context.should_abort:
            print("TestRole: Context aborted. Skipping tests.")
            return context

        print("TestRole: Running tests...")
        
        try:
            # Assuming pytest is installed and tests are discoverable in code_dir
            # For a more robust solution, we would use the Plugin interface
            # to determine the correct test runner for the language/framework.
            result = subprocess.run(
                ["pytest"],
                check=True,
                cwd=context.code_dir,
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
            print("TestRole: Tests passed successfully.")

        except subprocess.CalledProcessError as e:
            context.test_results = {
                "passed": False,
                "stdout": e.stdout,
                "stderr": e.stderr,
                "returncode": e.returncode
            }
            context.accepted = False # Tests failed, so changes are not accepted
            print(f"TestRole: Tests failed. Output:\n{e.stdout}\nErrors:\n{e.stderr}")
            # Optionally, revert changes if tests fail. This can be handled by SelfReviewRole.
            # self._git_reset_all(context.code_dir) # Moved to SelfReviewRole for decision making
        except FileNotFoundError:
            print("TestRole: Pytest command not found. Please ensure pytest is installed.")
            context.should_abort = True
        except Exception as e:
            print(f"TestRole: An unexpected error occurred during testing: {e}")
            context.should_abort = True

        return context
