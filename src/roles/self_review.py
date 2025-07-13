from typing import Any, Dict, Optional
from src.core.role import Role, Context
from src.core import ModelClient, ModelCallError # Corrected import path
from src.config import EngineConfig
import subprocess # For git reset

# Placeholder imports for now, will integrate actual modules later
# from src.god_engine.rule_engine import RuleEngine
# from src.utils.review_analyzer import ReviewAnalyzer

class SelfReviewRole(Role):
    """
    Role responsible for evaluating the acceptance of changes based on
    test results, identified problems, and potentially a meta-critique.
    """
    def __init__(self, config: EngineConfig, model_client: ModelClient):
        self.config = config
        self.model_client = model_client
        # self.rule_engine = RuleEngine(config) # Will initialize with actual config
        # self.review_analyzer = ReviewAnalyzer(config) # Will initialize with actual config

    def run(self, context: Context) -> Context:
        if context.should_abort:
            print("SelfReviewRole: Context aborted. Skipping self-review.")
            return context

        print("SelfReviewRole: Evaluating changes...")

        # Step 1: Evaluate based on test results
        if context.test_results and context.test_results.get("passed") is False:
            print("SelfReviewRole: Tests failed. Changes are not accepted.")
            context.accepted = False
            self._git_reset_all(context.code_dir) # Revert changes
            context.should_abort = True # Abort cycle on failed tests
            return context
        elif context.test_results and context.test_results.get("passed") is True:
            print("SelfReviewRole: Tests passed. Provisionally accepted.")
            context.accepted = True # Still provisionally, might be overridden by other rules
        else:
            print("SelfReviewRole: No test results available or tests not run.")
            # Decide on default behavior if no tests: provisionally accept or require more info
            context.accepted = False # Default to not accepted if no tests or inconclusive

        # Step 2: Evaluate acceptance via rules (placeholder for actual RuleEngine integration)
        # Assuming rule_engine.evaluate would return True/False for acceptance
        # if self.rule_engine.evaluate(context.goal, context.todos, context.test_results):
        #     print("SelfReviewRole: Rules engine accepted changes.")
        #     context.accepted = True
        # else:
        #     print("SelfReviewRole: Rules engine rejected changes.")
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
        #             print("SelfReviewRole: Meta-critique rejected changes.")
        #             context.accepted = False
        #             self._git_reset_all(context.code_dir)
        #             context.should_abort = True
        #         else:
        #             print("SelfReviewRole: Meta-critique accepted changes.")
        #             context.accepted = True
        #     except ModelCallError as e:
        #         print(f"SelfReviewRole: Meta-critique model call error: {e}")
        #     except Exception as e:
        #         print(f"SelfReviewRole: Error during meta-critique analysis: {e}")


        if context.accepted:
            print("SelfReviewRole: Changes are accepted. Marking goal as completed in next step.")
        else:
            print("SelfReviewRole: Changes are NOT accepted. Reverting code and aborting cycle.")
            self._git_reset_all(context.code_dir)
            context.should_abort = True # Ensure cycle is aborted if not accepted
            
        return context

    def _git_reset_all(self, cwd: str):
        """Resets all changes in the git repository."""
        try:
            print(f"SelfReviewRole: Resetting git repository in {cwd}...")
            subprocess.run(
                ["git", "reset", "--hard"],
                check=True,
                cwd=cwd,
                capture_output=True,
            )
            print("SelfReviewRole: Git reset successful.")
        except subprocess.CalledProcessError as e:
            print(f"SelfReviewRole: Error resetting git: {e}")
            print(e.stderr.decode())
        except Exception as e:
            print(f"SelfReviewRole: An unexpected error occurred during git reset: {e}")
