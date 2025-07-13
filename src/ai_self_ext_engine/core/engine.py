from typing import List, Optional, Any, Dict
from datetime import datetime
from importlib import import_module
from .role import Context, Role
from .plugin import Plugin # Import Plugin
from ..config import MainConfig, RoleConfig, PluginConfig # Import PluginConfig
from pathlib import Path
import logging


from ..goal_manager import GoalManager, Goal
from ..snapshot_store import SnapshotStore
from ..model_client import ModelClient

class Engine:
    """
    Orchestrates the self-improvement process, managing cycles,
    goals, roles, and snapshots.
    """
    logger = logging.getLogger(__name__)

    def __init__(self, config: MainConfig):
        self.config = config
        self.goal_manager = GoalManager(self.config.engine.goals_path)
        self.snapshot_store = SnapshotStore(self.config.engine.memory_path)
        self.model_client = ModelClient(self.config.model)

        # Ensure core directories exist for the project structure
        Path(self.config.engine.code_dir).mkdir(parents=True, exist_ok=True)
        # We no longer explicitly create src/core/roles as they are part of the package structure
        # and should be handled by the packaging system or user's project setup.

        self.roles = self._load_roles(config.roles)
        self.plugins = self._load_plugins(config.plugins) # Load plugins

    def _load_roles(self, role_configs: List[RoleConfig]) -> List[Role]:
        """
        Dynamically loads and instantiates roles based on the role_configs in config.
        """
        loaded_roles: List[Role] = []
        for role_conf in role_configs:
            try:
                # Dynamically import the module
                module = import_module(role_conf.module)
                # Get the role class from the module
                role_class = getattr(module, role_conf.class_name)
                loaded_roles.append(role_class(self.config, self.model_client))
            except (ImportError, AttributeError, TypeError) as e:
                self.logger.exception("Error loading role '%s' from module '%s': %s", role_conf.class_name, role_conf.module, e)
                raise # Re-raise to stop execution if a critical role can't be loaded
        return loaded_roles

    def _load_plugins(self, plugin_configs: Dict[str, PluginConfig]) -> Dict[str, Plugin]:
        """
        Dynamically loads and instantiates plugins based on the plugin_configs in config.
        """
        loaded_plugins: Dict[str, Plugin] = {}
        for plugin_name, plugin_conf in plugin_configs.items():
            try:
                module_path, class_name = plugin_conf.entry_point.rsplit('.', 1)
                module = import_module(module_path)
                plugin_class = getattr(module, class_name)
                loaded_plugins[plugin_name] = plugin_class(self.config) # Assuming plugin constructor takes config
            except (ImportError, AttributeError, TypeError) as e:
                self.logger.exception("Error loading plugin '%s' from entry point '%s': %s", plugin_name, plugin_conf.entry_point, e)
                raise # Re-raise to stop execution if a critical plugin can't be loaded
        return loaded_plugins

    def run_cycles(self):
        """
        Main loop for the self-improvement process.
        """
        self.logger.info("Starting self-improvement engine cycles...")
        
        # Outer loop: Iterate through pending goals
        while True:
            # Initialize context for the current goal iteration
            # A new context object is created for each *new* goal,
            # but its state might be loaded from a snapshot if resuming.
            context = Context(code_dir=self.config.engine.code_dir)

            # Get the next pending goal
            context.goal = self.goal_manager.next_goal()
            if not context.goal:
                self.logger.info("No more pending goals. Exiting.")
                break

            self.logger.info("\n--- Processing Goal: %s - %s ---", context.goal.goal_id, context.goal.description)

            # Try to load the latest snapshot for this goal to resume progress
            loaded_snapshot_context = self.snapshot_store.load_latest(context.goal.goal_id)
            if loaded_snapshot_context:
                # Preserve the current Goal object from GoalManager (which is the source of truth for 'pending')
                # and overlay other state from the snapshot.
                loaded_snapshot_context.goal = context.goal
                context = loaded_snapshot_context
                self.logger.info("Resuming goal '%s' from previous snapshot.", context.goal.goal_id)
            else:
                self.logger.info("Starting new attempt for goal '%s'.", context.goal.goal_id)
                # For a newly started goal, ensure todos are fresh (ProblemIdentification will populate them)
                context.todos = [] 
            
            # Inner loop: Multiple attempts for the current goal
            for attempt in range(self.config.engine.max_cycles):
                self.logger.info("\n--- Goal '%s' Attempt %s/%s ---", context.goal.goal_id, attempt + 1, self.config.engine.max_cycles)

                # Reset transient states at the beginning of each new attempt
                context.patch = None
                context.test_results = None
                context.accepted = False
                context.should_abort = False
                
                # Update metadata for the current attempt
                context.metadata["current_attempt"] = attempt + 1
                context.metadata["max_attempts_for_goal"] = self.config.engine.max_cycles
                context.metadata["timestamp"] = datetime.now().isoformat()

                # Execute roles for the current attempt
                attempt_aborted_by_role = False
                for role in self.roles:
                    self.logger.info("Executing role: %s", role.__class__.__name__)
                    context = role.run(context)
                    if context.should_abort:
                        self.logger.warning("Role %s requested abort. Stopping current goal attempt.", role.__class__.__name__)
                        attempt_aborted_by_role = True
                        break # Break out of role loop, proceed to snapshot and then next attempt or goal
                
                # Record snapshot after each attempt (even if aborted or failed)
                self.snapshot_store.record(context)

                if context.accepted:
                    self.goal_manager.mark_done(context.goal.goal_id)
                    self.logger.info("Goal '%s' successfully completed after %s attempts.", context.goal.goal_id, attempt + 1)
                    break
                elif attempt_aborted_by_role:
                    self.logger.warning("Goal '%s' attempt %s aborted due to a role's request. Moving to next goal.", context.goal.goal_id, attempt + 1)
                    break # Move to the next pending goal immediately if a role explicitly aborted
