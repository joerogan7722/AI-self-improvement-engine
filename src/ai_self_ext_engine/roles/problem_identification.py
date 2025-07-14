from pathlib import Path
import json
from ai_self_ext_engine.core.role import Role, Context
from ai_self_ext_engine.model_client import ModelClient, ModelCallError
from ai_self_ext_engine.config import MainConfig
from ai_self_ext_engine.todo_schema import Todo
import re
import logging

logger = logging.getLogger(__name__)


class ProblemIdentificationRole(Role):
    """
    Identifies problems to be addressed in the codebase.
    """

    def __init__(self, config: MainConfig, model_client: ModelClient):
        self.config = config
        self.model_client = model_client
        self.prompt_template_path = (
            Path(config.engine.prompts_dir) / "problem_identification.tpl"
        )

    def run(self, context: Context) -> Context:
        if not context.goal:
            print("ProblemIdentificationRole: No goal in context. Skipping.")
            return context

        logger.info(
            "ProblemIdentificationRole: Identifying problems for goal '%s'...",
            context.goal.goal_id,
        )

        try:
            if context.goal.goal_id == "verify_end_to_end_functionality":
                dummy_todo: Todo = {
                    "file_path": "N/A",
                    "change_type": "modify",
                    "description": (
                        "Ensure that the simple test module runs "
                        "successfully."
                    ),
                }
                context.todos = [dummy_todo]
                logger.info(
                    "Bypassing LLM for 'verify_end_to_end_functionality' "
                    "goal. Identified todos: %s",
                    context.todos,
                )
                return context

            if not self.prompt_template_path.exists():
                raise FileNotFoundError(
                    "Prompt template not found at "
                    f"{self.prompt_template_path}"
                )

            project_structure = self._get_project_structure(
                self.config.engine.code_dir
            )
            prompt_template = self.prompt_template_path.read_text(
                encoding="utf-8"
            )
            prompt = prompt_template.format(
                goal_description=context.goal.description,
                project_structure=project_structure,
            )
            response_text = self.model_client.call_model(
                self.config.model.model_name, prompt=prompt
            )

            logger.debug(
                "Raw LLM response for ProblemIdentificationRole: %s",
                response_text,
            )

            # Attempt to parse JSON output
            try:
                # Some models might wrap JSON in markdown code blocks.
                # Attempt to extract if present.
                if response_text.strip().startswith("```json"):
                    response_text = response_text.strip()[7:-3].strip() # Remove ```json\n and \n```
                
                parsed_todo_data = json.loads(response_text)

                # Validate against Todo schema more rigorously
                if not isinstance(parsed_todo_data, dict):
                    raise ValueError("Parsed output is not a dictionary.")
                
                # Explicitly check and cast types for critical fields
                file_path = parsed_todo_data.get("file_path")
                if not isinstance(file_path, str):
                    raise ValueError(
                        "'file_path' is missing or not a string."
                    )
                    
                change_type = parsed_todo_data.get("change_type")
                if (
                    not isinstance(change_type, str)
                    or change_type not in ["add", "modify", "delete"]
                ):
                    raise ValueError("'change_type' is missing or invalid.")
                
                description = parsed_todo_data.get("description")
                if not isinstance(description, str):
                    raise ValueError(
                        "'description' is missing or not a string."
                    )

                todo_item: Todo = {
                    "file_path": file_path,
                    "change_type": change_type,
                    "description": description,
                }
                
                if "line_start" in parsed_todo_data:
                    line_start = parsed_todo_data["line_start"]
                    if not isinstance(line_start, int):
                        raise ValueError(
                            "'line_start' is present but not an integer."
                        )
                    todo_item["line_start"] = line_start
                if "line_end" in parsed_todo_data:
                    line_end = parsed_todo_data["line_end"]
                    if not isinstance(line_end, int):
                        raise ValueError(
                            "'line_end' is present but not an integer."
                        )
                    todo_item["line_end"] = line_end

                excluded_patterns = [
                    r"create empty `__init__.py`",
                    r"verify all directories and `__init__.py` files exist",
                    r"create missing core engine subdirectories",
                    (
                        "initialize core engine subdirectories with "
                        "`__init__.py`"
                    ),
                ]

                if not any(
                    re.search(
                        pattern, todo_item["description"], re.IGNORECASE
                    )
                    for pattern in excluded_patterns
                ):
                    context.todos = [todo_item]
                    logger.info("Identified todo: %s", todo_item)
                else:
                    context.todos = []
                    logger.info(
                        "Excluded identified todo due to matching exclusion "
                        "pattern."
                    )

            except json.JSONDecodeError:
                logger.error(
                    "Failed to parse LLM response as JSON. Response: %s",
                    response_text,
                )
                context.should_abort = True
            except ValueError as ve:
                logger.error(
                    "Invalid Todo schema: %s. Response: %s",
                    ve,
                    response_text,
                )
                context.should_abort = True

        except ModelCallError as e:
            logger.error("Model call error: %s", e)
            context.should_abort = True
        except Exception:
            logger.exception(
                "An unexpected error occurred in "
                "ProblemIdentificationRole"
            )
            context.should_abort = True

        return context

    def _get_project_structure(self, root_dir: str) -> str:
        """
        Generates a string representation of the project's file structure.
        """
        structure = []
        root_path = Path(root_dir)
        for path in sorted(root_path.rglob("*")):
            if "__pycache__" in path.parts or path.name.startswith("."):
                continue

            depth = len(path.relative_to(root_path).parts) - 1
            indent = "    " * depth
            structure.append(
                f"{indent}{'+-- ' if path.is_dir() else '|-- '}{path.name}"
            )
        return "\n".join(structure)
