import importlib.util
import logging
from pathlib import Path
from typing import Dict, Type, Any, List, Optional

logger = logging.getLogger(__name__)

# Define a simple base class for plugins
class BasePlugin:
    """
    Base class for all plugins managed by the PluginManager.
    Plugins should inherit from this class and implement the required methods.
    """
    name: str = "UnnamedPlugin"
    description: str = "A generic plugin."

    def __init__(self, **kwargs):
        """
        Initializes the base plugin. Concrete plugins can extend this to accept
        configuration or dependencies.
        """
        pass

    async def execute(self, context: Any) -> Any:
        """
        Execute the plugin's primary action.
        This method must be implemented by concrete plugin classes.
        It is designed to be async to facilitate future parallel execution.

        Args:
            context: The current execution context, which can be modified by the plugin.

        Returns:
            The updated execution context.
        """
        raise NotImplementedError("Plugin must implement the 'execute' method.")

    def __repr__(self):
        return f"<Plugin: {self.name}>"

class PluginManager:
    """
    Manages the loading, registration, and access to various plugins.
    Lays the groundwork for improved plugin architecture and facilitates future
    parallel execution of plugin actions by managing plugins that conform to
    an async interface (`BasePlugin`).
    """
    def __init__(self):
        self._plugins: Dict[str, BasePlugin] = {}
        logger.debug("PluginManager initialized.")

    def register_plugin(self, plugin_instance: BasePlugin):
        """
        Registers a plugin instance with the manager.

        Args:
            plugin_instance: An instance of a class inheriting from BasePlugin.
        """
        if not isinstance(plugin_instance, BasePlugin):
            raise TypeError(f"Provided object is not an instance of BasePlugin: {type(plugin_instance)}")

        if plugin_instance.name in self._plugins:
            logger.warning(f"Plugin '{plugin_instance.name}' already registered. Overwriting existing plugin.")

        self._plugins[plugin_instance.name] = plugin_instance
        logger.info(f"Plugin '{plugin_instance.name}' registered.")

    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """
        Retrieves a registered plugin by its name.

        Args:
            name: The name of the plugin to retrieve.

        Returns:
            The BasePlugin instance if found, otherwise None.
        """
        return self._plugins.get(name)

    def get_all_plugins(self) -> Dict[str, BasePlugin]:
        """
        Retrieves a copy of all registered plugins, keyed by their names.
        """
        return self._plugins.copy()

    def load_plugins_from_directory(self, plugin_dir: Path, plugin_base_class: Type[BasePlugin] = BasePlugin):
        """
        Scans a directory for Python files, attempts to import them as modules,
        and registers classes inheriting from `plugin_base_class` as plugins.
        """
        if not plugin_dir.is_dir():
            logger.warning(f"Plugin directory not found or is not a directory: {plugin_dir}")
            return

        logger.info(f"Loading plugins from directory: {plugin_dir}")
        for filepath in plugin_dir.glob("*.py"):
            if filepath.name == "__init__.py":

# AI-generated improvements:
    # A dictionary to expose specific capabilities (e.g., tools, data handlers)
    capabilities: Dict[str, Any] = {}
        # Store capabilities exposed by registered plugins
        self._all_plugin_capabilities: Dict[str, Dict[str, Any]] = {}
        # Store the plugin's capabilities
        if plugin_instance.capabilities:
            self._all_plugin_capabilities[plugin_instance.name] = plugin_instance.capabilities
            logger.info(f"Plugin '{plugin_instance.name}' registered with capabilities: {list(plugin_instance.capabilities.keys())}")
        else:
            logger.info(f"Plugin '{plugin_instance.name}' registered.")
    def get_plugin_capabilities(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the capabilities exposed by a specific registered plugin.
        Args:
            plugin_name: The name of the plugin.
        Returns:
            A dictionary of capabilities if the plugin is found and exposes any, otherwise None.
        """
        return self._all_plugin_capabilities.get(plugin_name)
    def get_all_plugin_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """
        Retrieves a copy of all capabilities registered by all plugins,
        keyed by plugin name.
        Returns:
            A dictionary where keys are plugin names and values are their
            respective capabilities dictionaries.
        """
        return self._all_plugin_capabilities.copy()