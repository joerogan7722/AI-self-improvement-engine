```python
# engine.py
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type
from abc import ABC, abstractmethod
import importlib
import yaml
from pydantic import BaseModel, ValidationError

# --- Configuration Schema ---
class EngineConfig(BaseModel):
    code_dir: str
    max_cycles: int = 1
    memory_path: str
    goals_path: str
    role_sequence: List[str]  # e.g. ["roles.ProblemIdentificationRole", ...]
    config_version: Optional[int] = 1

# --- Context Definition ---
@dataclass
class Context:
    code_dir: str
    goal: Any = None
    todos: List[str] = field(default_factory=list)
    patch: Optional[str] = None
    test_results: Optional[Dict[str, Any]] = None
    accepted: bool = True
    should_abort: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

# --- Role Interface ---
class Role(ABC):
    @abstractmethod
    def run(self, context: Context) -> Context:
        """
        Execute role logic, update and return the Context.
        """
        pass

# --- Engine ---
class Engine:
    def __init__(self, config_path: str):
        # Load and validate configuration from YAML
        with open(config_path, 'r') as f:
            raw_config = yaml.safe_load(f)
        try:
            self.config = EngineConfig(**raw_config)
        except ValidationError as e:
            raise RuntimeError(f"Invalid configuration: {e}")

        # Initialize components
        self.goal_manager = self._init_goal_manager(self.config.goals_path)
        self.history = self._init_snapshot_store(self.config.memory_path)
        self.roles = self._load_roles(self.config.role_sequence)

    def run_cycles(self):
        context = Context(code_dir=self.config.code_dir)

        for cycle in range(self.config.max_cycles):
            # Fetch next goal
            context.goal = self.goal_manager.next_goal()
            if not context.goal or self.history.has(context.goal):
                break

            # Execute each role in sequence
            for role in self.roles:
                try:
                    context = role.run(context)
                except Exception as e:
                    # Handle errors: log and abort
                    context.metadata.setdefault('errors', []).append(str(e))
                    context.should_abort = True
                    break

            # Record snapshot
            self.history.record(context)

            # Terminate on abort or rejection
            if context.should_abort or not context.accepted:
                break

    def _init_goal_manager(self, goals_path: str) -> Any:
        # Dynamically import GoalManager
        module = importlib.import_module('god_engine.goal_manager')
        GoalManager = getattr(module, 'GoalManager')
        return GoalManager(goals_path)

    def _init_snapshot_store(self, memory_path: str) -> Any:
        # Dynamically import SnapshotStore
        module = importlib.import_module('god_engine.snapshot_store')
        SnapshotStore = getattr(module, 'SnapshotStore')
        return SnapshotStore(memory_path)

    def _load_roles(self, role_sequence: List[str]) -> List[Role]:
        roles: List[Role] = []
        for role_path in role_sequence:
            module_name, class_name = role_path.rsplit('.', 1)
            module = importlib.import_module(module_name)
            role_cls: Type[Role] = getattr(module, class_name)
            roles.append(role_cls())
        return roles

# --- CLI Entrypoint ---
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='AI Self-Extending Engine')
    parser.add_argument('--config', '-c', required=True,
                        help='Path to engine config YAML file')
    args = parser.parse_args()

    engine = Engine(args.config)
    engine.run_cycles()
```
