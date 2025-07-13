import json
from pathlib import Path
import logging # Import logging
from typing import Any, Dict, List, Optional

class Goal:
    """Represents a single improvement goal."""
    def __init__(self, goal_id: str, description: str, status: str = "pending"):
        self.goal_id = goal_id
        self.description = description
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.goal_id, "description": self.description, "status": self.status}

class GoalManager:
    """Manages the loading, serving, and tracking of improvement goals."""
    def __init__(self, goals_path: str):
        # Ensure the parent directory for the goals file exists
        Path(goals_path).parent.mkdir(parents=True, exist_ok=True)
        self.goals_path = Path(goals_path)
        self.logger = logging.getLogger(__name__) # New logger
        self.goals: List[Goal] = []
        self._load_goals()
        self._current_goal_index = 0

    def _load_goals(self):
        """Loads goals from the specified JSON file."""
        if not self.goals_path.exists():
            self.logger.info(f"Goals file not found at {self.goals_path}. Starting with no goals.")
            return

        try:
            with open(self.goals_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # If data is a list, assume it's directly the list of goal items
                if isinstance(data, list):
                    goal_items = data
                else: # Otherwise, assume it's a dict with a "goals" key
                    goal_items = data.get("goals", [])

                for item in goal_items:
                    # Map 'id' from JSON to 'goal_id' for Goal constructor
                    item['goal_id'] = item.pop('id') 
                    self.goals.append(Goal(**item))
        except json.JSONDecodeError:
            self.logger.error(f"Error decoding goals JSON from {self.goals_path}. File might be corrupted.")
        except Exception as e:
            self.logger.error(f"Error loading goals from {self.goals_path}: {e}")

    def save_goals(self):
        """Saves the current state of goals back to the JSON file."""
        # Always save as a dictionary with a "goals" key
        data = {"goals": [goal.to_dict() for goal in self.goals]}
        try:
            with open(self.goals_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e: # Catch any file-related errors
            self.logger.error(f"Error saving goals to {self.goals_path}: {e}")

    def next_goal(self) -> Optional[Goal]:
        """Returns the next pending goal, or None if no more pending goals."""
        while self._current_goal_index < len(self.goals):
            goal = self.goals[self._current_goal_index]
            if goal.status == "pending":
                return goal
            self._current_goal_index += 1
        return None

    def mark_done(self, goal_id: str):
        """Marks a goal as completed."""
        for goal in self.goals:
            if goal.goal_id == goal_id:
                goal.status = "completed"
                self.save_goals()
                self.logger.info(f"Goal '{goal_id}' marked as completed.")
                return
        self.logger.warning(f"Goal '{goal_id}' not found when trying to mark as done.")

    def add_goal(self, goal: Goal):
        """Adds a new goal to the manager."""
        self.goals.append(goal)
        self.save_goals()
        self.logger.info(f"Added new goal: {goal.goal_id}")

    def add_goal_from_dict(self, goal_data: Dict[str, Any]):
        """Adds a new goal from a dictionary."""
        self.goals.append(Goal(goal_data["id"], goal_data["description"], goal_data.get("status", "pending")))
        self.save_goals()
        self.logger.info(f"Added new goal: {goal_data['id']}")
