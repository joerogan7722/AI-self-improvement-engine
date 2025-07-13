from typing import List
from src.core.role import Role, Context
from src.core import ModelClient, ModelCallError # Corrected import path
from src.config import EngineConfig # Assuming EngineConfig has model names
import re # Import re for regex

class ProblemIdentificationRole(Role):
    def __init__(self, config: EngineConfig, model_client: ModelClient):
        self.config = config
        self.model_client = model_client
        self.prompt_template_path = f"{config.prompts_dir}/problem_identification_prompt.txt" # Placeholder

    def run(self, context: Context) -> Context:
        if not context.goal:
            print("ProblemIdentificationRole: No goal in context. Skipping.")
            return context

        print(f"ProblemIdentificationRole: Identifying problems for goal '{context.goal.goal_id}'...")

        try:
            # Load prompt template (simplified for now)
            # In a real scenario, you'd load this from self.prompt_template_path
            prompt_template = (
                "Based on the following goal description, "
                "identify a concise list of technical tasks or 'todos' "
                "that need to be completed to achieve this goal. "
                "Return them as a comma-separated list.\n"
                "IMPORTANT: ONLY identify tasks that involve modifying existing code files or creating new code files with initial content. "
                "DO NOT include tasks related to creating empty directories, creating empty `__init__.py` files, "
                "or verifying the existence of directories/files, as these are handled by the engine's initialization logic. "
                "Focus on tasks that require actual code implementation or modification.\n\n"
                "Goal: {goal_description}"
            )
            
            prompt = prompt_template.format(goal_description=context.goal.description)
            
            response_text = self.model_client.call_model(
                self.config.generator_model, # Using generator model for this
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
            print(f"ProblemIdentificationRole: Identified todos: {filtered_todos}")

        except ModelCallError as e:
            print(f"ProblemIdentificationRole: Model call error: {e}")
            context.should_abort = True # Abort if model call fails
        except Exception as e:
            print(f"ProblemIdentificationRole: An unexpected error occurred: {e}")
            context.should_abort = True # Abort on other errors

        return context
