from typing import List, TYPE_CHECKING
from pathlib import Path
import subprocess
import os
import logging
import re  # Added import for regex
from ai_self_ext_engine.core.role import Role, Context
from ai_self_ext_engine.model_client import ModelClient, ModelCallError
from ai_self_ext_engine.config import MainConfig
from ai_self_ext_engine.learning_log import LearningLog


if TYPE_CHECKING:
    from ai_self_ext_engine.todo_schema import Todo


logger = logging.getLogger(__name__)


class RefineRole(Role):
    def __init__(
        self,
        config: MainConfig,
        model_client: ModelClient,
        learning_log: LearningLog,
    ):
        self.config = config
        self.model_client = model_client
        self.learning_log = learning_log
        self.prompt_template_path = (
            Path(config.engine.prompts_dir) / "patch_generation.tpl"
        )

    def run(self, context: Context) -> Context:
        if not context.todos:
            logger.info("RefineRole: No todos in context. Skipping.")
            return context

        logger.info(
            "RefineRole: Generating and applying patch for todos: %s",
            context.todos,
        )

        try:
            # Read code for each todo and combine
            code_context_for_llm = self._read_code_for_todos(context.todos)
            context.current_code = code_context_for_llm  # Update context

            # Load prompt template from file
            if not self.prompt_template_path.exists():
                raise FileNotFoundError(
                    f"Prompt template not found at {self.prompt_template_path}"
                )

            prompt_template = self.prompt_template_path.read_text(
                encoding="utf-8"
            )

            # Format todos for the prompt
            todos_formatted = "\n".join(
                [
                    f"- File: {todo.get('file_path', 'N/A')}, "
                    f"Type: {todo.get('change_type', 'modify')}, "
                    "Description: "
                    f"{todo.get('description', 'No description')}"
                    for todo in context.todos
                ]
            )
            # Load and format learning examples
            learning_examples = self._format_learning_examples()

            prompt = prompt_template.format(
                current_code=code_context_for_llm,
                todos=todos_formatted,
                learning_examples=learning_examples,
            )

            raw_patch_response = self.model_client.call_model(
                self.config.model.model_name, prompt=prompt
            ).strip()

            # Extract patch using the new delimiters
            patch = self._extract_patch_from_response(raw_patch_response)

            context.patch = patch
            logger.debug("RefineRole: Generated patch:\n%s", patch)

            if patch:
                # Normalize line endings and strip trailing whitespace
                normalized_patch = patch.replace('\r\n', '\n')
                normalized_patch = '\n'.join(line.rstrip() for line in normalized_patch.splitlines())

                # Use the actual current working directory as cwd for git apply
                if self._apply_patch(normalized_patch, os.getcwd()):
                    logger.info("RefineRole: Patch applied successfully.")
                else:
                    logger.error("RefineRole: Failed to apply patch. Aborting.")
                    context.should_abort = True
            else:
                logger.info("RefineRole: No valid patch generated. Skipping application.")
                context.should_abort = True # Abort if no patch is generated for existing todos

        except ModelCallError as e:
            logger.error("RefineRole: Model call error: %s", e)
            context.should_abort = True
        except Exception as e:
            logger.exception("RefineRole: An unexpected error occurred: %s", e)
            context.should_abort = True

        return context

    def _extract_patch_from_response(self, response_text: str) -> str:
        """
        Extracts the unified diff patch string from the LLM's response,
        using the '```diff' and '```' fences.
        """
        match = re.search(r"```diff\n(.*?)\n```", response_text, re.DOTALL)
        if match:
            return match.group(1).strip()
        else:
            return ""

    def _read_code_for_todos(self, todos: List["Todo"]) -> str:
        """
        Reads code from files specified in the todos and concatenates them.
        Only reads files that have a 'file_path' and 'modify' or 'delete'
        change_type.
        """
        code_snippets = []
        for todo in todos:
            file_path_str = todo.get("file_path")
            change_type = todo.get("change_type")

            if not file_path_str or change_type == "add":
                # Skip if no file_path or if it's an 'add' operation
                continue

            # Ensure file_path_str starts with 'src/'
            if not file_path_str.startswith('src/'):
                logger.warning(
                    f"Invalid file_path in todo: {file_path_str}. Skipping."
                )
                continue

            # Construct the absolute path correctly from the project root
            # Assuming os.getcwd() is the project root.
            file_path = Path(os.getcwd()) / file_path_str

            if not file_path.exists():
                logger.warning(
                    "File specified in todo does not exist: %s", file_path
                )
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                # Add file header for context
                code_snippets.append(f"# File: {file_path_str}\n")

                line_start = todo.get("line_start")
                line_end = todo.get("line_end")

                if line_start is not None and line_end is not None:
                    lines = content.splitlines()
                    # Adjust for 0-based indexing
                    start_idx = max(0, line_start - 1)
                    end_idx = min(len(lines), line_end)
                    code_snippets.append(
                        "\n".join(lines[start_idx:end_idx])
                    )
                else:
                    code_snippets.append(content)
                code_snippets.append("\n\n")  # Separator
            except Exception as e:
                logger.warning(
                    "Could not read file %s for todo: %s", file_path, e
                )
        return "".join(code_snippets)

    def _format_learning_examples(self) -> str:
        """
        Loads recent learning entries and formats them for the prompt.
        """
        entries = self.learning_log.load_entries(max_entries=5)
        if not entries:
            return "No past examples available."

        formatted_examples = []
        for entry in entries:
            outcome = "SUCCESS" if entry["success"] else "FAILURE"
            formatted_examples.append(
                f"--- Example: {outcome} ---\n"
                f"Goal: {entry['goal']}\n"
                f"Review: {entry['review']}\n"
                f"Patch:\n{entry['patch']}\n"
            )
        return "\n".join(formatted_examples)

    def _apply_patch(self, patch_text: str, cwd: str) -> bool:
        """Applies a patch using git apply, with a pre-check."""
        if not patch_text:
            return False
        try:
            # Create a temporary patch file
            patch_file_path = Path("./temp.patch")
            patch_file_path.write_text(patch_text, encoding="utf-8")

            # 1. Check if the patch can be applied without errors
            try:
                subprocess.run(
                    ["git", "apply", "--check", str(patch_file_path)],
                    check=True,
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                )
                logger.info("RefineRole: Patch check successful.")
            except subprocess.CalledProcessError as e:
                logger.error(
                    "RefineRole: Patch check failed. Stderr:\n%s",
                    e.stderr,
                )
                patch_file_path.unlink()  # Clean up temp file
                return False

            # 2. If the check passes, apply the patch
            subprocess.run(
                ["git", "apply", str(patch_file_path)],
                check=True,
                cwd=cwd,
                capture_output=True,
            )
            patch_file_path.unlink()  # Delete the temporary patch file
            return True
        except subprocess.CalledProcessError as e:
            logger.error("Error applying patch: %s", e)
            if e.stderr:
                logger.error("Patch stderr:\n%s", e.stderr.decode())
            return False
        except FileNotFoundError:
            logger.error("Error: git command not found.")
            return False
