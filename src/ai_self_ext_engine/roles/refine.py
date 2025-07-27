import logging
import os
import re  # Added import for regex
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, List

from ai_self_ext_engine.config import MainConfig
from ai_self_ext_engine.core.role import Context, Role
from ai_self_ext_engine.learning_log import LearningLog
from ai_self_ext_engine.model_client import ModelCallError, ModelClient

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
        with improved handling of various formats.
        """
        # Try multiple extraction patterns
        patterns = [
            r"```diff\n(.*?)\n```",  # Standard diff format
            r"```patch\n(.*?)\n```", # Alternative patch format  
            r"```\n(.*?)\n```",      # Generic code block
            r"--- a/(.*?)\+\+\+ b/(.*)",  # Direct patch detection
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response_text, re.DOTALL)
            if match:
                patch = match.group(1).strip()
                # Validate that it looks like a patch
                if ('--- a/' in patch and '+++ b/' in patch) or ('def ' in patch or 'class ' in patch):
                    return patch
        
        # If no standard patch found, try to extract any code-like content
        if 'def ' in response_text or 'class ' in response_text:
            # Extract potential Python code additions
            lines = response_text.split('\n')
            code_lines = []
            in_code = False
            
            for line in lines:
                if 'def ' in line or 'class ' in line:
                    in_code = True
                    code_lines.append(f'+{line}')
                elif in_code and (line.startswith('    ') or line.strip() == ''):
                    code_lines.append(f'+{line}')
                elif in_code and not line.startswith('    '):
                    break
            
            if code_lines:
                # Create a simple patch format for new code
                return '\n'.join(code_lines)
        
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
        """Applies changes directly by parsing patch and modifying files."""
        if not patch_text:
            return False
        
        try:
            # Parse the patch to extract file changes
            file_changes = self._parse_patch_to_changes(patch_text)
            
            if not file_changes:
                logger.error("RefineRole: No valid file changes found in patch")
                return False
            
            # Apply each file change directly
            for file_path, changes in file_changes.items():
                if self._apply_file_changes(file_path, changes, cwd):
                    logger.info(f"RefineRole: Successfully applied changes to {file_path}")
                else:
                    logger.error(f"RefineRole: Failed to apply changes to {file_path}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"RefineRole: Error in patch application: {e}")
            return False

    def _parse_patch_to_changes(self, patch_text: str) -> dict:
        """Parse patch text into file changes that can be applied directly."""
        file_changes = {}
        
        # Split patch by files (look for --- and +++ markers)
        lines = patch_text.split('\n')
        current_file = None
        changes = []
        
        for line in lines:
            if line.startswith('--- a/'):
                # Save previous file changes
                if current_file and changes:
                    file_changes[current_file] = changes
                # Start new file
                current_file = line[6:]  # Remove '--- a/'
                changes = []
            elif line.startswith('+++ b/'):
                continue  # Skip +++ lines
            elif line.startswith('@@'):
                continue  # Skip hunk headers for now - just do full replacements
            elif line.startswith('+') and not line.startswith('+++'):
                # Addition
                changes.append(('add', line[1:]))
            elif line.startswith('-') and not line.startswith('---'):
                # Deletion  
                changes.append(('remove', line[1:]))
            elif line.startswith(' '):
                # Context line
                changes.append(('context', line[1:]))
        
        # Save final file
        if current_file and changes:
            file_changes[current_file] = changes
            
        return file_changes
    
    def _apply_file_changes(self, file_path: str, changes: list, cwd: str) -> bool:
        """Apply changes directly to a file using robust insertion logic."""
        try:
            full_path = Path(cwd) / file_path
            
            if not full_path.exists():
                logger.error(f"RefineRole: File does not exist: {full_path}")
                return False
            
            # Read current content and create backup for rollback
            content = full_path.read_text(encoding='utf-8')
            backup_path = full_path.with_suffix(full_path.suffix + '.backup')
            backup_path.write_text(content, encoding='utf-8')
            lines = content.splitlines()
            
            # Extract meaningful additions (code improvements)
            additions = []
            for change_type, line_content in changes:
                if change_type == 'add' and line_content.strip():
                    # Clean up the line content
                    clean_line = line_content.rstrip()
                    if clean_line and not clean_line.startswith('#'):  # Skip comments
                        additions.append(clean_line)
            
            if not additions:
                logger.info(f"RefineRole: No meaningful additions found for {file_path}")
                return True
            
            # Smart insertion strategy based on content type
            success = False
            if self._contains_function_or_class(additions):
                success = self._insert_functions_and_classes(full_path, lines, additions)
            else:
                success = self._insert_code_improvements(full_path, lines, additions)
            
            # CRITICAL: Validate syntax after changes to prevent breaking the engine
            if success and self._validate_python_syntax(full_path):
                logger.info(f"RefineRole: Successfully applied and validated changes to {file_path}")
                backup_path.unlink()  # Remove backup after success
                return True
            else:
                # ROLLBACK on failure to prevent engine damage
                logger.error(f"RefineRole: Validation failed for {file_path}, rolling back changes")
                full_path.write_text(content, encoding='utf-8')  # Restore original
                backup_path.unlink()  # Clean up backup
                return False
                
        except Exception as e:
            logger.error(f"RefineRole: Error applying changes to {file_path}: {e}")
            # Ensure rollback on any exception
            try:
                if 'backup_path' in locals() and backup_path.exists():
                    full_path.write_text(backup_path.read_text(encoding='utf-8'), encoding='utf-8')
                    backup_path.unlink()
            except:
                pass
            return False
    
    def _contains_function_or_class(self, lines: list) -> bool:
        """Check if additions contain function or class definitions."""
        return any('def ' in line or 'class ' in line for line in lines)
    
    def _insert_functions_and_classes(self, file_path: Path, original_lines: list, additions: list) -> bool:
        """Insert new functions and classes at appropriate locations."""
        try:
            # Find insertion point (before last line or after imports)
            insert_idx = len(original_lines)
            
            # Try to find a good insertion point after imports/existing functions
            for i, line in enumerate(original_lines):
                if line.strip().startswith('if __name__'):
                    insert_idx = i
                    break
            
            # Insert with proper spacing
            new_lines = original_lines[:insert_idx]
            if new_lines and new_lines[-1].strip():
                new_lines.append('')  # Add blank line before new code
            
            new_lines.append('# AI-generated improvements:')
            new_lines.extend(additions)
            
            if insert_idx < len(original_lines):
                new_lines.append('')  # Add blank line after new code
                new_lines.extend(original_lines[insert_idx:])
            
            # Write back
            new_content = '\n'.join(new_lines)
            file_path.write_text(new_content, encoding='utf-8')
            logger.info(f"RefineRole: Successfully inserted {len(additions)} lines into {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"RefineRole: Error inserting functions/classes: {e}")
            return False
    
    def _insert_code_improvements(self, file_path: Path, original_lines: list, additions: list) -> bool:
        """Insert general code improvements."""
        try:
            # For non-function improvements, append at end with documentation
            new_lines = original_lines[:]
            
            if new_lines and new_lines[-1].strip():
                new_lines.append('')
            
            new_lines.append('# AI-generated code improvements:')
            new_lines.extend(additions)
            
            # Write back
            new_content = '\n'.join(new_lines)
            file_path.write_text(new_content, encoding='utf-8')
            logger.info(f"RefineRole: Successfully added {len(additions)} improvement lines to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"RefineRole: Error inserting improvements: {e}")
            return False
    
    def _validate_python_syntax(self, file_path: Path) -> bool:
        """Validate Python file syntax after modifications - CRITICAL SAFETY CHECK."""
        try:
            import ast
            content = file_path.read_text(encoding='utf-8')
            ast.parse(content)
            logger.debug(f"RefineRole: Syntax validation passed for {file_path}")
            return True
        except SyntaxError as e:
            logger.error(f"RefineRole: SYNTAX ERROR in {file_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"RefineRole: Error validating syntax for {file_path}: {e}")
            return False
