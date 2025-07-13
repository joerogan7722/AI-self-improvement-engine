from typing import Any, Dict, Optional
from ai_self_ext_engine.core.role import Role, Context
from ai_self_ext_engine.model_client import ModelClient, ModelCallError
from ai_self_ext_engine.config import MainConfig
import subprocess # For git reset
import os # Import os for os.getcwd()
import logging # New import

logger = logging.getLogger(__name__) # New logger

class SelfReviewRole(Role):
    """
    Role responsible for evaluating the acceptance of changes based on
    test results, identified problems, and potentially a meta-critique.
    """
    def __init__(self, config: MainConfig, model_client: ModelClient):
        self.config = config
        self.model_client = model_client

    def run(self, context: Context) -> Context:
        if context.should_abort:
            logger.info("SelfReviewRole: Context aborted. Skipping self-review.")
            return context

        logger.info("SelfReviewRole: Evaluating changes...")

        # Step 1: Evaluate based on test results
        if context.test_results and context.test_results.get("passed") is False:
            logger.info("SelfReviewRole: Tests failed. Changes are not accepted.")
            context.accepted = False
            self._git_reset_all(os.getcwd()) # Revert changes from project root
            context.should_abort = True # Abort cycle on failed tests
            return context
        elif context.test_results and context.test_results.get("passed") is True:
            logger.info("SelfReviewRole: Tests passed. Provisionally accepted.")
            context.accepted = True # Still provisionally, might be overridden by other rules
        else:
            logger.info("SelfReviewRole: No test results available or tests not run.")
            # Decide on default behavior if no tests: provisionally accept or require more info
            context.accepted = False # Default to not accepted if no tests or inconclusive

        # Step 2: Evaluate acceptance via rules (placeholder for actual RuleEngine integration)
        # Assuming rule_engine.evaluate would return True/False for acceptance
        # if self.rule_engine.evaluate(context.goal, context.todos, context.test_results):
        #     logger.info("SelfReviewRole: Rules engine accepted changes.")
        #     context.accepted = True
        # else:
        #     logger.info("SelfReviewRole: Rules engine rejected changes.")
        #     context.accepted = False
        #     self._git_reset_all(context.code_dir)
        #     context.should_abort = True

        # Step 3: Optional: Meta-critique/Review Analysis (placeholder)
        # if self.config.meta_critic_model and context.patch:
        #     try:
        #         analysis_prompt = self.review_analyzer.get_analysis_prompt(context.patch, context.test_results)
        #         meta_critique_response = self.model_client.call_model(
        #             model_name=self.config.meta_critic_model,
        #             prompt=analysis_prompt
        #         )
        #         # Parse meta_critique_response to determine final acceptance
        #         # For now, let's assume if it contains "REJECT" it's rejected
        #         if "REJECT" in meta_critique_response.upper():
        #             logger.info("SelfReviewRole: Meta-critique rejected changes.")
        #             context.accepted = False
        #             self._git_reset_all(context.code_dir)
        #             context.should_abort = True
        #         else:
        #             logger.info("SelfReviewRole: Meta-critique accepted changes.")
        #             context.accepted = True
        #     except ModelCallError as e:
        #         logger.error(f"SelfReviewRole: Meta-critique model call error: {e}")
        #     except Exception as e:
        #         logger.exception(f"SelfReviewRole: Error during meta-critique analysis: {e}")


        if context.accepted:
            logger.info("SelfReviewRole: Changes are accepted. Marking goal as completed in next step.")
        else:
            logger.info("SelfReviewRole: Changes are NOT accepted. Reverting code and aborting cycle.")
            self._git_reset_all(os.getcwd()) # Revert changes from project root
            context.should_abort = True # Ensure cycle is aborted if not accepted
            
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
