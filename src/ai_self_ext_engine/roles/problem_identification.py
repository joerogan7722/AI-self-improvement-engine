from typing import List
from pathlib import Path # Import Path
from ai_self_ext_engine.core.role import Role, Context
from ai_self_ext_engine.model_client import ModelClient, ModelCallError
from ai_self_ext_engine.config import MainConfig # Use MainConfig
import re # Import re for regex
import logging # New import

logger = logging.getLogger(__name__) # New logger

class ProblemIdentificationRole(Role):
    def __init__(self, config: MainConfig, model_client: ModelClient):
        self.config = config
        self.model_client = model_client
        # Prompts directory is now part of the engine config, not directly in the root of EngineConfig
        self.prompt_template_path = Path(config.engine.prompts_dir) / "problem_identification.tpl"

    def run(self, context: Context) -> Context:
        if not context.goal:
            print("ProblemIdentificationRole: No goal in context. Skipping.")
            return context

        logger.info("ProblemIdentificationRole: Identifying problems for goal '%s'...", context.goal.goal_id)

        try:
            # Load prompt template from file
            if not self.prompt_template_path.exists():
                raise FileNotFoundError(f"Prompt template not found at {self.prompt_template_path}")
            
            prompt_template = self.prompt_template_path.read_text(encoding="utf-8")
            prompt = prompt_template.format(goal_description=context.goal.description)
            response_text = self.model_client.call_model(
                self.config.model.model_name, # Use the model name from the new config structure
                prompt=prompt
            )
            
            # Simple parsing for comma-separated list
            todos = [todo.strip() for todo in response_text.split(',') if todo.strip()]
            
            # Re-apply a minimal set of exclusions for safety, primarily to avoid empty __init__.py files
            filtered_todos = []
            excluded_patterns = [
                r"create empty `__init__.py`",
                r"verify all directories and `__init__.py` files exist",
                r"create missing core engine subdirectories",
                r"initialize core engine subdirectories with `__init__.py`"
            ]

            for todo in todos:
                if not any(re.search(pattern, todo, re.IGNORECASE) for pattern in excluded_patterns):
                    filtered_todos.append(todo)

            context.todos = filtered_todos
            logger.info("ProblemIdentificationRole: Identified todos: %s", filtered_todos)

        except ModelCallError as e:
            logger.error("ProblemIdentificationRole: Model call error: %s", e)
            context.should_abort = True # Abort if model call fails
        except Exception as e:
            logger.exception("ProblemIdentificationRole: An unexpected error occurred: %s", e)
            context.should_abort = True # Abort on other errors

        return context
