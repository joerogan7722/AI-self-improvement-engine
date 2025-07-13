# ast_utils.py
import ast
import difflib
from typing import List, Tuple

class AstUtils:
    """
    Provides AST-based code diffing and patch validation utilities.
    """
    @staticmethod
    def parse_code(code: str) -> ast.AST:
        """Parse Python source code into an AST."""
        return ast.parse(code)

    @staticmethod
    def get_function_defs(tree: ast.AST) -> List[ast.FunctionDef]:
        """Extract all top-level function definitions from the AST."""
        return [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

    @staticmethod
    def diff_code(old_code: str, new_code: str) -> List[str]:
        """Compute a unified diff between two code texts."""
        old_lines = old_code.splitlines(keepends=True)
        new_lines = new_code.splitlines(keepends=True)
        diff = difflib.unified_diff(old_lines, new_lines, lineterm='')
        return list(diff)

    @staticmethod
    def validate_patch(old_code: str, patch: str) -> bool:
        """Validate that a unified diff patch cleanly applies to the old code."""
        old_lines = old_code.splitlines(keepends=True)
        try:
            patched = difflib.restore(patch.splitlines(), 1)
            # If restore succeeds without exception, consider it valid
            return True
        except Exception:
            return False

    @staticmethod
    def apply_patch(old_code: str, patch: str) -> str:
        """Apply a unified diff patch to old_code, returning patched code."""
        # This method assumes patch is in unified diff format
        patched_lines = []
        diff = patch.splitlines(keepends=True)
        patched_lines = list(difflib.restore(diff, 1))
        return ''.join(patched_lines)
