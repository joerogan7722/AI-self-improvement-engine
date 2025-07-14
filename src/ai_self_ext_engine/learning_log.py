import json
from pathlib import Path
from typing import List, Dict, Any, Optional


class LearningLog:
    """
    Manages a log of self-improvement cycles to facilitate learning.
    """

    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "learning_log.jsonl"

    def record_entry(self, entry: Dict[str, Any]):
        """
        Appends a new learning entry to the log file.
        Each entry is a JSON object on a new line.
        """
        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def load_entries(
        self, max_entries: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Loads learning entries from the log file.
        Returns a list of the most recent entries.
        """
        if not self.log_file.exists():
            return []

        entries = []
        with self.log_file.open("r", encoding="utf-8") as f:
            for line in f:
                entries.append(json.loads(line))

        if max_entries:
            return entries[-max_entries:]
        return entries


def create_learning_entry(
    goal: str,
    patch: str,
    test_results: Dict[str, Any],
    review: str,
    success: bool,
) -> Dict[str, Any]:
    """
    Creates a new structured entry for the learning log.
    """
    return {
        "goal": goal,
        "patch": patch,
        "test_results": test_results,
        "review": review,
        "success": success,
    }
