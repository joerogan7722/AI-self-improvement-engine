import logging
from typing import Optional
from pathlib import Path

from ..config import MainConfig
from ..model_client import ModelClient, ModelCallError

logger = logging.getLogger(__name__)

class CodeSynthesizer:
    """
    A module responsible for synthesizing initial code improvements or patches
    based on a given goal and the current codebase.
    """
    def __init__(self, config: MainConfig, model_client: ModelClient):
        self.config = config
        self.model_client = model_client

        # NOTE: Due to patch file location constraints (only modifying files within
        # 'src/ai_self_ext_engine/'), the prompt template is embedded here.
        # In a real-world scenario, this would ideally be loaded from a file
        # in a separate 'prompts' directory as per the engine's config.
        self.PROMPT_TEMPLATE = """
You are an expert AI software engineer. Your task is to propose an initial self-improvement or code change based on a given goal and the current codebase.
Your output MUST be a unified diff patch. If no changes are needed, output an empty string.

Goal: {goal_description}

Current Codebase:
```
{current_code}
```

Based on the Goal, generate a unified diff patch to improve the Current Codebase. Focus on the core change needed to address the goal.
Do not include any conversational text or explanations. Provide only the patch.
"""

    def synthesize_initial_patch(self, goal_description: str, current_code: str) -> Optional[str]:
        """
        Synthesizes an initial patch to address the given goal based on the current codebase.

        Args:
            goal_description: The description of the goal to achieve.
            current_code: The concatenated content of the current codebase files.

        Returns:
            A unified diff patch string, or None if an error occurred or no patch was generated.
        """
        logger.info("CodeSynthesizer: Synthesizing initial patch for goal: '%s'", goal_description)

        try:
            prompt = self.PROMPT_TEMPLATE.format(
                goal_description=goal_description,
                current_code=current_code
            )

            response_text = self.model_client.call_model(
                model_name=self.config.model.model_name,
                prompt=prompt
            ).strip()

            if response_text.startswith("---"):
                logger.debug("CodeSynthesizer: Successfully synthesized an initial patch.")
                return response_text
            elif not response_text:
