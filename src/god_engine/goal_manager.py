# goal_manager.py
"""
Manages the goals of the system.
"""
import json
from pathlib import Path
from typing import List, Optional


class Goal:
    """
    Represents a goal for the system to achieve.
    """
    def __init__(
        self,
        goal_id: str,
        description: str,
        impact: float,
        effort: float,
        name: str = "",
        target_file: str = "",
        completion_criteria: str = "",
        patch_logic: str = "",
    ):
        self.goal_id = goal_id
        self.description = description
        self.impact = impact       # estimated capability/autonomy gain
        self.effort = effort       # relative cost
        self.status = "pending"    # or "in_progress", "done"
        self.name = name
        self.target_file = target_file
        self.completion_criteria = completion_criteria
        self.patch_logic = patch_logic

    @property
    def score(self):
        """
        Calculates the score of the goal.
        """
        # Higher = more attractive (impact per effort)
        return self.impact / max(self.effort, 0.1)


class GoalManager:
    """
    Manages the goals of the system.
    """
    def __init__(self, path: str = "goals.json"):
        self.file = Path(path)
        self.goals: List[Goal] = self._load()

    def _load(self) -> List[Goal]:
        if self.file.exists():
            data = json.loads(self.file.read_text(encoding="utf-8"))
            goals = []
            if isinstance(data, list):  # Handle case where goals.json is a list
                for item in data:
                    if (
                        isinstance(item, dict)
                        and "id" in item
                        and "description" in item
                    ):
                        valid_args = {
                            k: v
                            for k, v in item.items()
                            if k
                            in [
                                "description",
                                "impact",
                                "effort",
                                "name",
                                "target_file",
                                "completion_criteria",
                                "patch_logic",
                            ]
                        }
                        if "impact" not in valid_args:
                            valid_args["impact"] = 1.0
                        if "effort" not in valid_args:
                            valid_args["effort"] = 1.0
                        goals.append(Goal(goal_id=item["id"], **valid_args))
            elif isinstance(
                data, dict
            ):  # Handle case where goals.json is a dict (old format)
                for goal_id, goal_data in data.items():
                    if isinstance(goal_data, dict) and "description" in goal_data:
                        valid_args = {
                            k: v
                            for k, v in goal_data.items()
                            if k
                            in [
                                "description",
                                "impact",
                                "effort",
                                "name",
                                "target_file",
                                "completion_criteria",
                                "patch_logic",
                            ]
                        }
                        if "impact" not in valid_args:
                            valid_args["impact"] = 1.0
                        if "effort" not in valid_args:
                            valid_args["effort"] = 1.0
                        goals.append(Goal(goal_id=goal_id, **valid_args))
            return goals
        return []

    def save(self):
        data = [g.__dict__ for g in self.goals]
        self.file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add_goal(self, goal: Goal):
        self.goals.append(goal)
        self.save()

    def add_goal_from_dict(self, goal_data: dict):
        goal = Goal(
            goal_id=goal_data["id"],
            description=goal_data["description"],
            impact=goal_data.get("impact", 1.0),
            effort=goal_data.get("effort", 1.0),
            name=goal_data.get("name", ""),
            target_file=goal_data.get("target_file", ""),
            completion_criteria=goal_data.get("completion_criteria", ""),
            patch_logic=goal_data.get("patch_logic", ""),
        )
        self.add_goal(goal)

    def next_goal(self) -> Optional[Goal]:
        pending = [g for g in self.goals if g.status == "pending"]
        pending.sort(key=lambda g: g.score, reverse=True)
        if pending:
            g = pending[0]
            g.status = "in_progress"
            self.save()
            return g
        return None

    def mark_done(self, goal_id: str):
        for g in self.goals:
            if g.goal_id == goal_id:
                g.status = "done"
        self.save()
