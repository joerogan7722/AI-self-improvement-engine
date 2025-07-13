from typing import List, Optional, Any, Dict
from datetime import datetime # Import datetime for timestamp
from .role import Context, Role
from ..config import EngineConfig
from pathlib import Path # Import Path for directory creation
from ..goal_manager import GoalManager, Goal # Import Goal as well
from ..snapshot_store import SnapshotStore
from ..model_client import ModelClient # Import ModelClient

class Engine:
    """
    Orchestrates the self-improvement process, managing cycles,
    goals, roles, and snapshots.
    """
    def __init__(self, config: EngineConfig):
        self.config = config
        self.goal_manager = GoalManager(config.goals_path)
        self.snapshot_store = SnapshotStore(config.memory_path)
        self.model_client = ModelClient() # Initialize ModelClient

        # Ensure core directories exist for the project structure
        Path(self.config.code_dir).mkdir(parents=True, exist_ok=True) # Ensure the base code_dir exists
        (Path(self.config.code_dir) / "src").mkdir(parents=True, exist_ok=True) # Ensure 'src/' exists
        (Path(self.config.code_dir) / "src" / "core").mkdir(parents=True, exist_ok=True) # Ensure 'src/core/' exists
        (Path(self.config.code_dir) / "src" / "roles").mkdir(parents=True, exist_ok=True) # Ensure 'src/roles/' exists
        # Ensure the directory for prompt templates exists
        Path(self.config.prompts_dir).mkdir(parents=True, exist_ok=True)
        self.roles = self._load_roles(config.role_sequence)

    def _load_roles(self, role_sequence: List[str]) -> List[Role]:
        """
        Dynamically loads and instantiates roles based on the role_sequence in config.
        """
        loaded_roles: List[Role] = []
        for role_name in role_sequence:
            try:
                # Import the src.roles package itself
                import src.roles
                # Get the role class from the src.roles package
                role_class = getattr(src.roles, role_name)
                loaded_roles.append(role_class(self.config, self.model_client))
            except (ImportError, AttributeError) as e:
                print(f"Error loading role '{role_name}': {e}")
                raise # Re-raise to stop execution if a critical role can't be loaded
        return loaded_roles

    def run_cycles(self):
        """
        Main loop for the self-improvement process.
        """
        print("Starting self-improvement cycle...")
        context = Context(code_dir=self.config.code_dir)

        for cycle in range(self.config.max_cycles):
            print(f"\n--- Cycle {cycle + 1}/{self.config.max_cycles} ---")
            
            context.goal = self.goal_manager.next_goal()
            if not context.goal:
                print("No more pending goals. Exiting.")
                break
            
            if self.snapshot_store.has(context.goal):
                print(f"Goal '{context.goal.goal_id}' already processed. Skipping.")
                continue

            # Add current cycle and timestamp to context metadata
            context.metadata["cycle"] = cycle + 1
            context.metadata["timestamp"] = datetime.now().isoformat()

            for role in self.roles:
                print(f"Executing role: {role.__class__.__name__}")
                context = role.run(context)
                if context.should_abort:
                    print(f"Role {role.__class__.__name__} requested abort. Stopping cycle.")
                    break
            
            self.snapshot_store.record(context) # Re-enable snapshot recording
            
            if context.should_abort:
                print("Cycle aborted.")
                break
            
            if context.accepted: # If accepted, mark goal as done
                self.goal_manager.mark_done(context.goal.goal_id)
                print(f"Goal '{context.goal.goal_id}' completed and accepted.")
            else:
                print(f"Current changes for goal '{context.goal.goal_id}' not accepted. Stopping cycle.")
                break

        print("\nSelf-improvement cycle finished.")
