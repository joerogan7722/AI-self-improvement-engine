from pathlib import Path
import json
from ai_self_ext_engine.core.role import Role, Context
from ai_self_ext_engine.model_client import ModelClient, ModelCallError
from ai_self_ext_engine.config import MainConfig
import subprocess
import os
import logging

logger = logging.getLogger(__name__)

class SelfReviewRole(Role):
    """
    Role responsible for evaluating the acceptance of changes based on
    a code review from an LLM and test results.
    """
    def __init__(self, config: MainConfig, model_client: ModelClient):
        self.config = config
        self.model_client = model_client
        self.prompt_template_path = Path(config.engine.prompts_dir) / "self_review.tpl"

    def run(self, context: Context) -> Context:
        if context.should_abort or not context.patch:
            logger.info("SelfReviewRole: Context aborted or no patch to review. Skipping self-review.")
            return context

        logger.info("SelfReviewRole: Reviewing generated patch...")

        try:
            # Load prompt template
            if not self.prompt_template_path.exists():
                raise FileNotFoundError(f"Prompt template not found at {self.prompt_template_path}")
            
            prompt_template = self.prompt_template_path.read_text(encoding="utf-8")

            # Format todos for the prompt
            todos_formatted = "\n".join([
                f"- File: {todo.get('file_path', 'N/A')}, Type: {todo.get('change_type', 'modify')}, Description: {todo.get('description', 'No description')}"
                for todo in context.todos
            ])
            
            prompt = prompt_template.format(
                todos=todos_formatted,
                current_code=context.current_code,
                patch=context.patch
            )
            
            response_text = self.model_client.call_model(
                self.config.model.model_name,
                prompt=prompt
            )

            # Parse the review from the LLM
            review = json.loads(response_text)
            patch_accepted = review.get("patch_accepted", False)
            feedback = review.get("feedback", "No feedback provided.")
            
            logger.info("SelfReviewRole: Review feedback: %s", feedback)
            
            # Evaluate based on test results and LLM review
            tests_passed = context.test_results and context.test_results.get("passed", False)
            
            if patch_accepted and tests_passed:
                logger.info("SelfReviewRole: Patch accepted by review and tests passed. Changes are accepted.")
                context.accepted = True
            else:
                logger.info("SelfReviewRole: Patch not accepted or tests failed. Reverting changes.")
                context.accepted = False
                self._git_reset_all(os.getcwd())
                context.should_abort = True

        except (ModelCallError, json.JSONDecodeError, FileNotFoundError) as e:
            logger.error("SelfReviewRole: Error during self-review: %s", e)
            context.accepted = False
            self._git_reset_all(os.getcwd())
            context.should_abort = True
        except Exception as e:
            logger.exception("SelfReviewRole: An unexpected error occurred: %s", e)
            context.accepted = False
            self._git_reset_all(os.getcwd())
            context.should_abort = True
            
        return context

    def _git_reset_all(self, cwd: str):
        """Resets all changes in the git repository."""
        try:
            logger.info("SelfReviewRole: Resetting git repository in %s...", cwd)
            subprocess.run(
                ["git", "reset", "--hard"],
                check=True,
                cwd=cwd,
                capture_output=True,
            )
            logger.info("SelfReviewRole: Git reset successful.")
        except subprocess.CalledProcessError:
            logger.exception("SelfReviewRole: Error resetting git.")
        except Exception:
            logger.exception("SelfReviewRole: An unexpected error occurred during git reset.")
