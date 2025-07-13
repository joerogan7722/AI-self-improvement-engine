import re
from pathlib import Path
from typing import List, Dict

TODO_PATTERN = re.compile(r"TODO\[(?P<id>[A-Za-z0-9_-]+)\]:\s*(?P<desc>.+)")


def analyze_codebase(code_dir: str) -> List[Dict]:
    """
    Walk all .py files under code_dir, find TODO[id]: description
    and return structured goals.
    """
    todos: List[Dict] = []
    for py in Path(code_dir).rglob("*.py"):
        for idx, line in enumerate(py.read_text().splitlines(), start=1):
            m = TODO_PATTERN.search(line)
            if m:
                todos.append({
                    "id": m.group("id"),
                    "description": m.group("desc").strip(),
                    "file": str(py.relative_to(code_dir)),
                    "line": idx
                })
    return todos


def generate_goals_from_todos(code_dir: str) -> List[Dict]:
    """
    Adapter for the SelfImprovementModule: wraps analyze_codebase
    into goal dicts with default impact/effort.
    """
    raw = analyze_codebase(code_dir)
    return [
        {
            "id": item["id"],
            "description": f"{item['description']} (at {item['file']}:{item['line']})",
            "impact": 1.0,
            "effort": 1.0
        }
        for item in raw
    ]
