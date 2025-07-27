import logging
from importlib import import_module
from pathlib import Path
from typing import Dict, List, cast

from ..config import MainConfig, PluginConfig, RoleConfig
from ..goal_manager import Goal, GoalManager
from ..learning_log import LearningLog, create_learning_entry
from ..model_client import ModelClient
from ..snapshot_store import SnapshotStore
from .plugin import Plugin
from .role import Context, Role


class Engine:
    """
    Orchestrates the self-improvement process, managing cycles,
    goals, roles, and snapshots.
    """

    logger = logging.getLogger(__name__)

    def __init__(self, config: MainConfig):
        """Initialize the Engine with configuration.

        Args:
            config: Main configuration object containing engine settings, paths, and model configuration
        """
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
        """Dynamically loads and instantiates roles based on the role_configs.

        Args:
            role_configs: List of role configuration objects specifying modules and classes to load

        Returns:
            List of instantiated role objects ready for execution
        """
        loaded_roles: List[Role] = []
        for role_conf in role_configs:
            try:
                module = import_module(role_conf.module)
                role_class = getattr(module, role_conf.class_name)
                # Pass learning_log to RefineRole, but not to others
                if role_conf.class_name == "RefineRole":
                    loaded_roles.append(
                        role_class(self.config, self.model_client, self.learning_log)
                    )
                else:
                    loaded_roles.append(role_class(self.config, self.model_client))
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
        """Dynamically loads plugins based on the plugin_configs.

        Args:
            plugin_configs: Dictionary mapping plugin names to their configuration objects

        Returns:
            Dictionary mapping plugin names to instantiated plugin objects
        """
        loaded_plugins: Dict[str, Plugin] = {}
        for plugin_name, plugin_conf in plugin_configs.items():
            try:
                module_path, class_name = plugin_conf.entry_point.rsplit(".", 1)
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
        """Main loop for the self-improvement process.

        Enhanced with autonomous goal generation. Continuously processes goals from the goal manager,
        executing them through configured roles until completion or abort. Automatically generates
        new goals when the queue is empty.

        Returns:
            None: This method runs until all goals are processed or autonomous generation fails
        """
        self.logger.info("Starting self-improvement engine cycles...")

        while True:
            goal = self._get_next_goal()
            if not goal:
                break

            context = self._setup_goal_context(goal)
            self._execute_goal_attempts(context)

    def _get_next_goal(self) -> Goal | None:
        """Get the next goal to process, with autonomous generation fallback.

        Returns:
            Goal | None: The next goal to process, or None if no goals available and generation failed
        """
        goal = self.goal_manager.next_goal()
        if not goal:
            self.logger.info(
                "No pending goals found. Attempting autonomous goal generation..."
            )
            if self._attempt_autonomous_goal_generation():
                return (
                    self.goal_manager.next_goal()
                )  # Try again with newly generated goals
            else:
                self.logger.info(
                    "No more goals available and auto-generation failed. Exiting."
                )
                return None
        return goal

    def _setup_goal_context(self, goal: Goal) -> Context:
        """Set up the context for goal processing, handling snapshot restoration.

        Args:
            goal: The goal to set up context for

        Returns:
            Context: Configured context object ready for goal processing
        """
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

        return context

    def _execute_goal_attempts(self, context: Context) -> None:
        """Execute multiple attempts for a goal until completion or max cycles reached."""
        for attempt in range(self.config.engine.max_cycles):
            goal = cast(Goal, context.goal)  # Ensure goal is not None
            self.logger.info(
                "\n--- Goal '%s' Attempt %s/%s ---",
                goal.goal_id,
                attempt + 1,
                self.config.engine.max_cycles,
            )

            self._reset_attempt_state(context)
            result = self._execute_roles(context)
            self._record_attempt_results(context, goal)

            if result == "completed":
                self.goal_manager.mark_done(goal.goal_id)
                self.logger.info(
                    "Goal '%s' completed in %s attempts.",
                    goal.goal_id,
                    attempt + 1,
                )
                break
            elif result == "aborted":
                self.logger.warning(
                    "Goal '%s' aborted after %s attempts.",
                    goal.goal_id,
                    attempt + 1,
                )
                break  # Move to the next pending goal

    def _reset_attempt_state(self, context: Context) -> None:
        """Reset transient state for a new attempt."""
        context.patch = None
        context.test_results = None
        context.review = None
        context.accepted = False
        context.should_abort = False

    def _execute_roles(self, context: Context) -> str:
        """Execute all roles and return the result status.

        Args:
            context: The execution context containing goal and state information

        Returns:
            str: Status string - "completed", "aborted", or "continue"
        """
        for role in self.roles:
            self.logger.info("Executing role: %s", role.__class__.__name__)
            context = role.run(context)
            if context.should_abort:
                self.logger.warning(
                    "Role %s requested abort. Stopping attempt.",
                    role.__class__.__name__,
                )
                return "aborted"

        if context.accepted:
            return "completed"
        return "continue"

    def _record_attempt_results(self, context: Context, goal: Goal) -> None:
        """Record snapshot and learning entry for the attempt."""
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

    def _attempt_autonomous_goal_generation(self) -> bool:
        """
        Attempts to autonomously generate new goals when none are available.
        Returns True if goals were successfully generated and added.
        """
        try:
            self.logger.info("Initiating autonomous goal generation...")
            goal_generator = self._create_goal_generator()
            context = self._run_goal_generation(goal_generator)
            return self._process_generated_goals(context)
        except ImportError as e:
            self.logger.error(f"GoalGenerationRole not available: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Autonomous goal generation failed: {e}")
            return False

    def _create_goal_generator(self):
        """Create and return a GoalGenerationRole instance."""
        from ai_self_ext_engine.roles.goal_generation import GoalGenerationRole

        return GoalGenerationRole(self.config, self.model_client)

    def _run_goal_generation(self, goal_generator) -> Context:
        """Run goal generation and return the updated context."""
        context = Context(code_dir=self.config.engine.code_dir)
        return goal_generator.run(context)

    def _process_generated_goals(self, context: Context) -> bool:
        """Process generated goals from context and add them to goal manager."""
        if "generated_goals" not in context.metadata:
            self.logger.warning("Goal generation completed but no goals were produced")
            return False

        generated_goals = context.metadata["generated_goals"]
        self.logger.info(f"Generated {len(generated_goals)} autonomous goals")

        goals_added = 0
        for goal_data in generated_goals:
            if self._add_single_goal(goal_data):
                goals_added += 1

        return goals_added > 0

    def _add_single_goal(self, goal_data: dict) -> bool:
        """Add a single goal to the goal manager."""
        try:
            from ai_self_ext_engine.goal_manager import Goal

            goal = Goal(
                goal_id=goal_data["id"],
                description=goal_data["description"],
                priority=goal_data.get("priority", "medium"),
                metadata=goal_data.get("metadata", {}),
            )
            self.goal_manager.add_goal(goal)
            self.logger.info(f"Added autonomous goal: {goal.description}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add generated goal: {e}")
            return False
