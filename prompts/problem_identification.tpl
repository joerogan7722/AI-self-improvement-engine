Based on the following goal description and the existing project structure, identify a *single, most critical* technical task or 'todo' that needs to be completed to achieve this goal. This task should focus *EXCLUSIVELY* on refactoring, improving, or extending the *existing* AI Self-Extending Engine.

**Project Structure:**
```
{project_structure}
```

Return ONLY a single, most critical technical task as a JSON object, strictly adhering to the `Todo` schema. No additional formatting or punctuation outside the JSON.

**Todo Schema:**
```json
{{
    "file_path": "path/to/file.py",
    "change_type": "add" | "modify" | "delete",
    "description": "A clear description of the task.",
    "line_start": 1,
    "line_end": 10
}}
```
`file_path`: Path to the file relative to the project root.
`change_type`: "add" for new files, "modify" for existing files, "delete" for removing files.
`description`: A concise explanation of what needs to be done.
`line_start` (optional): Starting line number for modifications (for `modify` type).
`line_end` (optional): Ending line number for modifications (for `modify` type).

**CRITICAL RULES FOR TODO GENERATION:**
-   **ONLY** generate tasks that involve modifying existing code files or creating *new* code files with initial content *within the `src/ai_self_ext_engine/` directory.*
-   **Ensure `file_path` always starts with `src/` (e.g., `src/ai_self_ext_engine/module/file.py`).**
-   **DO NOT** generate tasks related to creating new project boilerplate (e.g., `pyproject.toml`, `README.md`, `.gitignore`, `ci.yml`, `main.py` if it's not within `src/ai_self_ext_engine`).
-   **DO NOT** generate tasks related to creating empty directories or `__init__.py` files.
-   **DO NOT** generate tasks for files outside the `src/ai_self_ext_engine/` directory.
-   Ensure the `description` field is specific and actionable, e.g., "Implement X feature in Y module", "Refactor Z class", "Update A configuration".
-   The task should represent a small, atomic step towards the overall goal.

**Example Todo (JSON output only):**
```json
{{
    "file_path": "src/ai_self_ext_engine/roles/refine.py",
    "change_type": "modify",
    "description": "Refactor _read_code_from_dir to read only specified files.",
    "line_start": 120,
    "line_end": 150
}}
```

Goal: {goal_description}
