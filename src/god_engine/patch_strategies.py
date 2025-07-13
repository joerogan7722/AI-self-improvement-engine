"""
Patch Generation Strategies for the God Engine.

This module contains individual functions for handling different
patch generation goals.
"""
import subprocess
import ast
import astor

from .patch_generation import AstRefactorer


def add_module_docstring(goal, original_content):
    """Adds a module-level docstring."""
    print(f"PatchGenerationModule: Adding module docstring for {goal.target_file}...")
    lines = original_content.splitlines(keepends=True)
    new_content_lines = []

    # Check for shebang and encoding declarations
    insert_index = 0
    for i, line in enumerate(lines):
        if line.startswith('#!') or line.startswith('# -*- coding:'):
            new_content_lines.append(line)
            insert_index = i + 1
        else:
            break  # Stop looking after the first non-special line

    # Insert the docstring and a blank line after it for separation
    new_content_lines.insert(
        insert_index, goal.completion_criteria + "\n\n"
    )

    # Add the rest of the original content
    new_content_lines.extend(lines[insert_index:])

    return "".join(new_content_lines)


def fix_trailing_whitespace(goal, original_content):
    """Fixes trailing whitespace on a specific line."""
    print(f"PatchGenerationModule: Fixing trailing whitespace for {goal.target_file}...")
    lines = original_content.splitlines(keepends=True)
    fixed_lines = []
    for i, line in enumerate(lines):
        try:
            line_num_from_goal = int(goal.name.split('_')[-1])
            if i + 1 == line_num_from_goal:
                fixed_lines.append(
                    line.rstrip(' \t') +
                    ("\n" if line.endswith('\n') else "")
                )
            else:
                fixed_lines.append(line)
        except (ValueError, IndexError):
            fixed_lines.append(line)
    return "".join(fixed_lines)


def simplify_if_else_return(goal, original_content, code_root):
    """Simplifies 'if-else-return' structures using AST."""
    print(f"PatchGenerationModule: Simplifying if/else/return in {goal.target_file}.")
    try:
        tree = ast.parse(original_content)
        transformer = AstRefactorer()
        new_tree = transformer.visit(tree)
        ast.fix_missing_locations(new_tree)
        return astor.to_source(new_tree)
    except Exception as e:
        print(
            "Error during AST refactoring for SIMPLIFY_IF_ELSE_RETURN: "
            f"{e}"
        )
        return original_content


def run_external_tool(tool_name, args, file_path, code_root):
    """Helper to run external tools like isort, autoflake, autopep8."""
    command = [tool_name] + args + [file_path]
    try:
        subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            cwd=code_root
        )
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except subprocess.CalledProcessError as e:
        print(f"Error running {tool_name}: {e.stderr}")
        return None
    except FileNotFoundError:
        print(
            f"Error: '{tool_name}' command not found. "
            "Make sure it's installed and in your PATH."
        )
        return None


def fix_import_order(goal, original_content, code_root):
    """Fixes import order using isort."""
    print(
        "PatchGenerationModule: Fixing import order for "
        f"{goal.target_file} using isort..."
    )
    return run_external_tool(
        "isort", [], goal.target_file, code_root
    ) or original_content


def remove_unused_import(goal, original_content, code_root):
    """Removes unused imports using autoflake."""
    print(
        "PatchGenerationModule: Removing unused import in "
        f"{goal.target_file} using autoflake..."
    )
    args = ["--in-place", "--remove-unused-variables"]
    return run_external_tool(
        "autoflake", args, goal.target_file, code_root
    ) or original_content


def fix_line_length(goal, original_content, code_root):
    """Fixes line length using autopep8."""
    print(
        "PatchGenerationModule: Fixing line length for "
        f"{goal.target_file} using autopep8..."
    )
    args = ["--in-place", "--max-line-length=88"]
    return run_external_tool(
        "autopep8", args, goal.target_file, code_root
    ) or original_content
