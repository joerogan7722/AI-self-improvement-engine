from typing import List
from pathlib import Path # Import Path
from ai_self_ext_engine.core.role import Role, Context
from ai_self_ext_engine.model_client import ModelClient, ModelCallError
from ai_self_ext_engine.config import MainConfig # Use MainConfig
import subprocess
import os # Import os
import logging # New import

logger = logging.getLogger(__name__) # New logger

class RefineRole(Role):
    def __init__(self, config: MainConfig, model_client: ModelClient):
        self.config = config
        self.model_client = model_client
        self.prompt_template_path = Path(config.engine.prompts_dir) / "patch_generation.tpl"

    def run(self, context: Context) -> Context:
        if not context.todos:
            logger.info("RefineRole: No todos in context. Skipping.")
            return context

        logger.info("RefineRole: Generating and applying patch for todos: %s", context.todos)

        try:
            current_code = self._read_code_from_dir(self.config.engine.code_dir) # Use config.engine.code_dir
            context.current_code = current_code # Update context with current code

            # Load prompt template from file
            if not self.prompt_template_path.exists():
                raise FileNotFoundError(f"Prompt template not found at {self.prompt_template_path}")
            
            prompt_template = self.prompt_template_path.read_text(encoding="utf-8")
            
            prompt = prompt_template.format(
                current_code=current_code,
                todos="\n".join([f"- {todo}" for todo in context.todos])
            )
            # The LLM is expected to output only the patch. We might need to strip leading/trailing text.
            patch = self.model_client.call_model(
                self.config.model.model_name, # Use model from config
                prompt=prompt
            ).strip()

            # Ensure the patch starts with the diff header
            if not patch.startswith("---"):
                # Attempt to find the start of the patch if the LLM added preamble
                patch_start_idx = patch.find("--- ")
                if patch_start_idx != -1:
                    patch = patch[patch_start_idx:]
                else:
                    logger.warning("RefineRole: Generated patch does not start with '---'. May be invalid.")

            context.patch = patch
            logger.debug("RefineRole: Generated patch:\n%s", patch)
            if patch:
                # Use the actual current working directory as cwd for git apply
                if self._apply_patch(patch, os.getcwd()): # Use os.getcwd()
                    logger.info("RefineRole: Patch applied successfully.")
                else:
                    logger.error("RefineRole: Failed to apply patch. Aborting cycle.")
                    context.should_abort = True
            else:
                logger.info("RefineRole: No patch generated. Skipping application.")

        except ModelCallError as e:
            logger.error("RefineRole: Model call error: %s", e)
            context.should_abort = True
        except Exception as e:
            logger.exception("RefineRole: An unexpected error occurred: %s", e)
            context.should_abort = True

        return context

    def _read_code_from_dir(self, code_dir: str) -> str:
        """
        Reads all Python files in the specified directory and concatenates them.
        This is a simplified approach for demonstration.
        """
        full_code = []
        # Construct the absolute path to the ai_self_ext_engine package
        target_code_dir = Path(os.getcwd()) / self.config.engine.code_dir / "ai_self_ext_engine"
        if not target_code_dir.exists():
            logger.warning("Code directory %s does not exist.", target_code_dir)
            return ""

        # Exclude common temporary/generated directories
        exclude_dirs = ["__pycache__", "sim_memory", "_memory_snapshots"]
        
        # Walk through the target code directory, excluding specified paths
        for root, dirs, files in os.walk(target_code_dir):
            # Modify dirs in-place to prune the search
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file_name in files:
                if file_name.endswith(".py"):
                    file_path = Path(root) / file_name
                    try:
                        # Ensure we don't try to read temp.patch or other non-source files
                        if file_path.name == "temp.patch" or file_path.name.startswith("test_"):
                            continue
                        
                        # Adjust relative path to be relative to the project root for display purposes
                        relative_path = file_path.relative_to(os.getcwd())
                        full_code.append(f"# File: {relative_path}\n")
                        full_code.append(file_path.read_text(encoding="utf-8"))
                        full_code.append("\n\n")
                    except Exception as e:
                        logger.warning("Could not read %s: %s", file_path, e)
        return "".join(full_code)

    def _apply_patch(self, patch_text: str, cwd: str) -> bool:
        """Applies a patch to the codebase using git apply."""
        if not patch_text:
            return False
        try:
            # Create a temporary patch file in the current working directory (root)
            patch_file_path = Path("./temp.patch")
            patch_file_path.write_text(patch_text, encoding="utf-8")

            # Apply the patch using git from the specified cwd
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
            if isinstance(e, subprocess.CalledProcessError):
                logger.error("Patch stderr:\n%s", e.stderr.decode())
            return False
        except FileNotFoundError as e:
            logger.error("Error: git command not found. %s", e)
            return False
