import subprocess
import os
import logging
from pathlib import Path
from ai_self_ext_engine.core.role import Role, Context
from ai_self_ext_engine.config import MainConfig
from ai_self_ext_engine.model_client import ModelClient, ModelCallError


logger = logging.getLogger(__name__)


class TestRole(Role):
    """
    Role responsible for generating and running tests on the codebase.
    """

    def __init__(self, config: MainConfig, model_client: ModelClient):
        self.config = config
        self.model_client = model_client
        self.prompt_template_path = (
            Path(config.engine.prompts_dir) / "test_generation.tpl"
        )

    def run(self, context: Context) -> Context:
        if context.should_abort or not context.patch:
            logger.info(
                "TestRole: Context aborted or no patch to test. Skipping."
            )
            return context

        logger.info("TestRole: Generating and applying new tests...")
        self._generate_and_apply_tests(context)

        logger.info("TestRole: Running all tests...")
        self._run_all_tests(context)

        return context

    def _generate_and_apply_tests(self, context: Context):
        """
        Generates and applies new tests based on the current patch.
        """
        if not self.prompt_template_path.exists():
            logger.error(
                "TestRole: Test generation prompt not found at %s",
                self.prompt_template_path,
            )
            return

        prompt_template = self.prompt_template_path.read_text(encoding="utf-8")
        prompt = prompt_template.format(patch_to_be_tested=context.patch)

        try:
            test_patch = self.model_client.call_model(
                self.config.model.model_name, prompt=prompt
            ).strip()

            if test_patch:
                logger.info("TestRole: Applying generated test patch.")
                self._apply_patch(test_patch, os.getcwd())
            else:
                logger.warning("TestRole: No test patch was generated.")

        except ModelCallError as e:
            logger.error(
                "TestRole: Model call failed during test generation: %s", e
            )

    def _run_all_tests(self, context: Context):
        """
        Runs the entire pytest test suite.
        """
        try:
            result = subprocess.run(
                ["pytest"],
                cwd=os.getcwd(),
                capture_output=True,
                text=True,
            )

            tests_passed = result.returncode == 0
            context.test_results = {
                "passed": tests_passed,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }

            if tests_passed:
                logger.info("TestRole: All tests passed successfully.")
            else:
                logger.error(
                    "TestRole: Tests failed. Output:\n%s\nErrors:\n%s",
                    result.stdout,
                    result.stderr,
                )

        except FileNotFoundError:
            logger.error(
                "TestRole: Pytest not found. Please ensure it is installed."
            )
            context.should_abort = True
            context.test_results = {
                "passed": False,
                "error": "pytest not found",
            }
        except Exception as e:
            logger.exception(
                "TestRole: An unexpected error occurred: %s", e
            )
            context.should_abort = True
            context.test_results = {"passed": False, "error": str(e)}

    def _apply_patch(self, patch_text: str, cwd: str) -> bool:
        """
        Applies a patch to the codebase using git apply.
        This is a simplified version for applying test patches.
        """
        if not patch_text:
            return False
        try:
            patch_file_path = Path("./temp_test.patch")
            patch_file_path.write_text(patch_text, encoding="utf-8")

            subprocess.run(
                ["git", "apply", str(patch_file_path)],
                check=True,
                cwd=cwd,
                capture_output=True,
            )
            patch_file_path.unlink()
            return True
        except subprocess.CalledProcessError as e:
            logger.error(
                "Error applying test patch: %s\n%s", e, e.stderr.decode()
            )
            return False
        except FileNotFoundError:
            logger.error("Error: git command not found.")
            return False
