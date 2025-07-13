import json
import os # Import os
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

# Assuming Context is defined in ai_self_ext_engine.core.role
from ai_self_ext_engine.core.role import Context

class SnapshotStore:
    """
    Manages the storage and retrieval of improvement cycle snapshots.
    Each snapshot includes code, critiques, and other relevant metadata.
    """
    def __init__(self, memory_path: str):
        self.memory_dir = Path(memory_path) # Use relative path
        self.memory_dir.mkdir(parents=True, exist_ok=True) # Ensure directory exists

    def record(self, context: Context):
        """
        Records a snapshot of the current context.
        Each goal will have its own subdirectory.
        """
        if not context.goal:
            print("Cannot record snapshot: No goal in context.")
            return

        goal_snapshot_dir = self.memory_dir / context.goal.goal_id
        goal_snapshot_dir.mkdir(parents=True, exist_ok=True) # Ensure goal-specific directory exists

        # Sanitize timestamp for filename: replace colons with hyphens
        timestamp = context.metadata.get("timestamp", datetime.now().isoformat()).replace(":", "-")
        snapshot_file_path = os.path.join(str(goal_snapshot_dir), f"{timestamp}.json")
        
        # Prepare data for serialization
        snapshot_data = {
            "cycle": context.metadata.get("cycle"),
            "goal_id": context.goal.goal_id,
            "description": context.goal.description,
            "current_code": context.current_code,
            "todos": context.todos,
            "patch": context.patch,
            "test_results": context.test_results,
            "accepted": context.accepted,
            "should_abort": context.should_abort,
            "metadata": context.metadata
        }

        try:
            with open(snapshot_file_path, 'w', encoding='utf-8') as f: # Use the new path variable
                json.dump(snapshot_data, f, indent=2)
            print(f"Snapshot recorded for goal '{context.goal.goal_id}' at {snapshot_file_path}")
        except Exception as e:
            print(f"Error recording snapshot for goal '{context.goal.goal_id}': {e}")

    def has(self, goal: Any) -> bool:
        """
        Checks if a snapshot for a given goal already exists.
        For simplicity, it just checks if the goal's directory exists and is not empty.
        """
        goal_snapshot_dir = self.memory_dir / goal.goal_id
        return goal_snapshot_dir.exists() and any(goal_snapshot_dir.iterdir())

    def load_latest(self, goal_id: str) -> Optional[Context]:
        """
        Loads the latest snapshot for a given goal.
        (Implementation can be more sophisticated to find actual latest by timestamp)
        """
        goal_snapshot_dir = self.memory_dir / goal_id
        if not goal_snapshot_dir.exists():
            return None
        
        # For simplicity, just pick the first json file found
        for f in goal_snapshot_dir.iterdir():
            if f.suffix == ".json":
                try:
                    with open(f, 'r', encoding='utf-8') as sf:
                        data = json.load(sf)
                        # Reconstruct Context object (simplified)
                        context = Context(
                            code_dir=data.get("code_dir", "."), # Assuming code_dir is stored
                            current_code=data.get("current_code"),
                            goal=None, # Need to load Goal object separately if needed
                            todos=data.get("todos", []),
                            patch=data.get("patch"),
                            test_results=data.get("test_results"),
                            accepted=data.get("accepted", False),
                            should_abort=data.get("should_abort", False),
                            metadata=data.get("metadata", {})
                        )
                        return context
                except Exception as e:
                    print(f"Error loading snapshot from {f}: {e}")
        return None
