from typing import List, Dict, cast
from importlib import import_module
from pathlib import Path
import logging

from .role import Context, Role
from .plugin import Plugin
from ..config import MainConfig, RoleConfig, PluginConfig
from ..goal_manager import GoalManager, Goal
from ..snapshot_store import SnapshotStore
from ..model_client import ModelClient
from ..learning_log import LearningLog, create_learning_entry


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
        self.learning_log = LearningLog(
            Path(self.config.engine.memory_path) / "learning"
        )

        # Ensure core directories exist for the project structure
        Path(self.config.engine.code_dir).mkdir(parents=True, exist_ok=True)

        self.roles = self._load_roles(config.roles)
        self.plugins = self._load_plugins(config.plugins)

    def _load_roles(self, role_configs: List[RoleConfig]) -> List[Role]:
        """
        Dynamically loads and instantiates roles based on the role_configs.
        """
        loaded_roles: List[Role] = []
        for role_conf in role_configs:
            try:
                module = import_module(role_conf.module)
                role_class = getattr(module, role_conf.class_name)
                # Pass learning_log to RefineRole, but not to others
                if role_conf.class_name == "RefineRole":
                    loaded_roles.append(
                        role_class(
                            self.config, self.model_client, self.learning_log
                        )
                    )
                else:
                    loaded_roles.append(
                        role_class(self.config, self.model_client)
                    )
            except (ImportError, AttributeError, TypeError) as e:
                self.logger.exception(
                    "Error loading role '%s' from module '%s': %s",
                    role_conf.class_name,
                    role_conf.module,
                    e,
                )
                raise  # Re-raise to stop execution
        return loaded_roles

    def _load_plugins(
        self, plugin_configs: Dict[str, PluginConfig]
    ) -> Dict[str, Plugin]:
        """
        Dynamically loads plugins based on the plugin_configs.
        """
        loaded_plugins: Dict[str, Plugin] = {}
        for plugin_name, plugin_conf in plugin_configs.items():
            try:
                module_path, class_name = plugin_conf.entry_point.rsplit(
                    ".", 1
                )
                module = import_module(module_path)
                plugin_class = getattr(module, class_name)
                loaded_plugins[plugin_name] = plugin_class(self.config)
            except (ImportError, AttributeError, TypeError) as e:
                self.logger.exception(
                    "Error loading plugin '%s' from entry point '%s': %s",
                    plugin_name,
                    plugin_conf.entry_point,
                    e,
                )
                raise  # Re-raise to stop execution
        return loaded_plugins

    def run_cycles(self):
        """
        Main loop for the self-improvement process.
        """
        self.logger.info("Starting self-improvement engine cycles...")

        while True:
            goal = self.goal_manager.next_goal()
            if not goal:
                self.logger.info("No more pending goals. Exiting.")
                break

            context = Context(code_dir=self.config.engine.code_dir, goal=goal)
            goal = cast(Goal, context.goal)  # Ensure goal is correctly typed
            self.logger.info(
                "\n--- Processing Goal: %s - %s ---",
                goal.goal_id,
                goal.description,
            )

            loaded_snapshot = self.snapshot_store.load_latest(goal.goal_id)
            if loaded_snapshot:
                loaded_snapshot.goal = goal
                context = loaded_snapshot
                self.logger.info(
                    "Resuming goal '%s' from previous snapshot.",
                    goal.goal_id,
                )
            else:
                self.logger.info(
                    "Starting new attempt for goal '%s'.",
                    goal.goal_id,
                )
                context.todos = []

            for attempt in range(self.config.engine.max_cycles):
                goal = cast(Goal, context.goal)  # Ensure goal is not None
                self.logger.info(
                    "\n--- Goal '%s' Attempt %s/%s ---",
                    goal.goal_id,
                    attempt + 1,
                    self.config.engine.max_cycles,
                )

                # Reset transient states
                context.patch = None
                context.test_results = None
                context.review = None
                context.accepted = False
                context.should_abort = False

                # Execute roles
                for role in self.roles:
                    self.logger.info(
                        "Executing role: %s", role.__class__.__name__
                    )
                    context = role.run(context)
                    if context.should_abort:
                        self.logger.warning(
                            "Role %s requested abort. Stopping attempt.",
                            role.__class__.__name__,
                        )
                        break

                self.snapshot_store.record(context)

                # Record learning entry
                learning_entry = create_learning_entry(
                    goal=goal.description,
                    patch=context.patch or "",
                    test_results=context.test_results or {},
                    review=context.review or "",
                    success=context.accepted,
                )
                self.learning_log.record_entry(learning_entry)

                if context.accepted:
                    self.goal_manager.mark_done(goal.goal_id)
                    self.logger.info(
                        "Goal '%s' completed in %s attempts.",
                        goal.goal_id,
                        attempt + 1,
                    )
                    break
                elif context.should_abort:
                    self.logger.warning(
                        "Goal '%s' aborted after %s attempts.",
                        goal.goal_id,
                        attempt + 1,
                    )
                    break  # Move to the next pending goal
