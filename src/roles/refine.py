from typing import List
from src.core.role import Role, Context
from src.core import ModelClient, ModelCallError # Corrected import path
from src.config import EngineConfig
import subprocess
from pathlib import Path
import os # Import os

class RefineRole(Role):
    def __init__(self, config: EngineConfig, model_client: ModelClient):
        self.config = config
        self.model_client = model_client
        self.prompt_template_path = f"{config.prompts_dir}/refine_prompt.txt" # Placeholder

    def run(self, context: Context) -> Context:
        if not context.todos:
            print("RefineRole: No todos in context. Skipping.")
            return context

        print(f"RefineRole: Generating and applying patch for todos: {context.todos}")

        try:
            # For now, let's assume current_code is read from the code_dir
            # In a real scenario, you'd load the actual code to be refined
            # For this example, let's just use a dummy code representation
            current_code = self._read_code_from_dir(context.code_dir)
            context.current_code = current_code # Update context with current code

            prompt_template = (
                "You are an expert software engineer tasked with modifying code.\n"
                "Given the following existing codebase (if any) and a list of technical tasks (todos),\n"
                "generate a unified-diff patch that implements the required changes.\n"
                "Adhere strictly to the unified diff format, including:\n"
                "-   `--- a/path/to/old/file`\n"
                "-   `+++ b/path/to/new/file`\n"
                "-   `@@ -start_line,num_lines +start_line,num_lines @@`\n"
                "-   Lines beginning with ` ` (space) for context.\n"
                "-   Lines beginning with `-` for removals.\n"
                "-   Lines beginning with `+` for additions.\n"
                "-   Ensure new files start with `--- /dev/null` and `+++ b/path/to/new/file`.\n"
                "-   Ensure `temp.patch` and `_memory_snapshots/` are completely ignored and not part of the patch.\n"
                "-   The patch should only modify or create files within the 'src/' directory relative to the current working directory.\n"
                "-   Avoid any conversational text or explanations outside the patch itself. The response MUST be ONLY the patch, starting with `---`.\n\n"
                "--- START CODE (Current state of relevant Python files in 'src/' directory) ---\n{current_code}\n--- END CODE ---\n\n"
                "--- START TODOS (Tasks to achieve for the current goal) ---\n{todos}\n--- END TODOS ---\n\n"
                "--- START PATCH (Provide the unified diff here) ---\n" # Indicate to the LLM to start the patch here
            )
            
            prompt = prompt_template.format(
                current_code=current_code,
                todos="\n".join([f"- {todo}" for todo in context.todos])
            )
            
            # The LLM is expected to output only the patch. We might need to strip leading/trailing text.
            patch = self.model_client.call_model(
                self.config.refiner_model,
                prompt=prompt
            ).strip()

            # Ensure the patch starts with the diff header
            if not patch.startswith("---"):
                # Attempt to find the start of the patch if the LLM added preamble
                patch_start_idx = patch.find("--- ")
                if patch_start_idx != -1:
                    patch = patch[patch_start_idx:]
                else:
                    print("RefineRole: Warning: Generated patch does not start with '---'. May be invalid.")

            context.patch = patch
            print(f"RefineRole: Generated patch:\n{patch}")
            
            if patch:
                if self._apply_patch(patch, context.code_dir):
                    print("RefineRole: Patch applied successfully.")
                else:
                    print("RefineRole: Failed to apply patch. Aborting cycle.")
                    context.should_abort = True
            else:
                print("RefineRole: No patch generated. Skipping application.")

        except ModelCallError as e:
            print(f"RefineRole: Model call error: {e}")
            context.should_abort = True
        except Exception as e:
            print(f"RefineRole: An unexpected error occurred: {e}")
            context.should_abort = True

        return context

    def _read_code_from_dir(self, code_dir: str) -> str:
        """
        Reads all Python files in the specified directory and concatenates them.
        This is a simplified approach for demonstration.
        """
        full_code = []
        # Target only the 'src' directory for reading code
        target_code_dir = Path(code_dir) / "src" # Read from the 'src' subdirectory
        if not target_code_dir.exists():
            print(f"Warning: Code directory {target_code_dir} does not exist.")
            return ""

        # Exclude common temporary/generated directories
        exclude_dirs = ["__pycache__", "sim_memory", "_memory_snapshots"] # Keep these exclusions
        
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
                        
                        relative_path = file_path.relative_to(code_dir) # Keep path relative to original code_dir
                        full_code.append(f"# File: {relative_path}\n")
                        full_code.append(file_path.read_text(encoding="utf-8"))
                        full_code.append("\n\n")
                    except Exception as e:
                        print(f"Warning: Could not read {file_path}: {e}")
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
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error applying patch: {e}")
            if isinstance(e, subprocess.CalledProcessError):
                print(e.stderr.decode())
            return False
