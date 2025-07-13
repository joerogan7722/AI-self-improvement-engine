# goal_manager.py
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

class GoalManager:
    """
    Loads goals from a JSON/YAML file and provides them sequentially.
    """
    def __init__(self, goals_path: str):
        self.goals_path = Path(goals_path)
        self.goals = self._load_goals()
        self.index = 0

    def _load_goals(self) -> List[Dict[str, Any]]:
        # Supports JSON or YAML based on file extension
        if self.goals_path.suffix in ['.yaml', '.yml']:
            import yaml
            with open(self.goals_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            with open(self.goals_path, 'r') as f:
                return json.load(f)

    def next_goal(self) -> Optional[Dict[str, Any]]:
        if self.index < len(self.goals):
            goal = self.goals[self.index]
            self.index += 1
            return goal
        return None

    def reset(self) -> None:
        """Reset the internal pointer to reprocess goals from the start."""
        self.index = 0

    def all_goals(self) -> List[Dict[str, Any]]:
        return self.goals

# snapshot_store.py
import os
import json
from pathlib import Path
from typing import Any

class SnapshotStore:
    """
    Manages recording and retrieval of engine snapshots (contexts) to a filesystem directory.
    """
    def __init__(self, memory_path: str):
        self.memory_path = Path(memory_path)
        self.memory_path.mkdir(parents=True, exist_ok=True)

    def has(self, goal: Any) -> bool:
        """
        Check if a snapshot for this goal ID already exists.
        """
        goal_id = self._get_goal_id(goal)
        return (self.memory_path / f"{goal_id}.json").exists()

    def record(self, context: Any) -> None:
        """
        Serialize the context to a JSON file under memory_path.
        """
        goal_id = self._get_goal_id(context.goal)
        snapshot_file = self.memory_path / f"{goal_id}.json"
        data = {
            'goal': context.goal,
            'todos': context.todos,
            'patch': context.patch,
            'test_results': context.test_results,
            'accepted': context.accepted,
            'metadata': context.metadata,
        }
        with open(snapshot_file, 'w') as f:
            json.dump(data, f, indent=2)

    def load(self, goal: Any) -> Any:
        """
        Load a recorded context for the given goal.
        """
        goal_id = self._get_goal_id(goal)
        snapshot_file = self.memory_path / f"{goal_id}.json"
        if snapshot_file.exists():
            with open(snapshot_file, 'r') as f:
                return json.load(f)
        return None

    def _get_goal_id(self, goal: Any) -> str:
        # Assumes goal has an 'id' attribute or key
        if isinstance(goal, dict):
            return str(goal.get('id'))
        return str(getattr(goal, 'id', goal))
