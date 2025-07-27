import pytest
from pathlib import Path
import logging
import asyncio
import importlib.util

# Assuming the path is correct after the patch is applied
from src.ai_self_ext_engine.core.plugin_manager import BasePlugin, PluginManager

# --- Fixtures ---

@pytest.fixture
def plugin_manager():
    """Provides a fresh PluginManager instance for each test."""
    return PluginManager()

@pytest.fixture
def mock_plugin_class():
    """Provides a basic mock BasePlugin subclass."""
    class MockPlugin(BasePlugin):
        name = "MockPlugin"
        description = "A mock plugin for testing."

        def __init__(self, value=None):
            super().__init__()
            self.value = value
            self.executed_context = None

        async def execute(self, context: dict) -> dict:
            self.executed_context = context
            context["MockPluginExecuted"] = True
            return context
    return MockPlugin

@pytest.fixture
def another_mock_plugin_class():
    """Provides another mock BasePlugin subclass."""
    class AnotherMockPlugin(BasePlugin):
        name = "AnotherMockPlugin"
        description = "Another mock plugin for testing."

        async def execute(self, context: dict) -> dict:
            context["AnotherMockPluginExecuted"] = True
            return context
    return AnotherMockPlugin

# --- Tests for BasePlugin ---

def test_base_plugin_init_and_attributes():
    plugin = BasePlugin()
    assert plugin.name == "UnnamedPlugin"
    assert plugin.description == "A generic plugin."
    assert repr(plugin) == "<Plugin: UnnamedPlugin>"

def test_base_plugin_execute_not_implemented():
    plugin = BasePlugin()
    with pytest.raises(NotImplementedError, match="Plugin must implement the 'execute' method."):
        asyncio.run(plugin.execute({})) # Use asyncio.run for async method

# --- Tests for PluginManager ---

def test_plugin_manager_init(plugin_manager):
    assert isinstance(plugin_manager._plugins, dict)
    assert len(plugin_manager._plugins) == 0
    assert plugin_manager.registered_plugin_names == []

def test_register_plugin_success(plugin_manager, mock_plugin_class):
    mock_plugin_instance = mock_plugin_class()
    plugin_manager.register_plugin(mock_plugin_instance)
    assert len(plugin_manager._plugins) == 1
    assert plugin_manager.get_plugin("MockPlugin") is mock_plugin_instance
    assert "MockPlugin" in plugin_manager.registered_plugin_names

def test_register_plugin_type_error(plugin_manager):
    with pytest.raises(TypeError, match="Provided object is not an instance of BasePlugin"):
        plugin_manager.register_plugin("not_a_plugin")

    class NonPlugin:
        pass
    with pytest.raises(TypeError, match="Provided object is not an instance of BasePlugin"):
        plugin_manager.register_plugin(NonPlugin())

def test_register_plugin_overwrite_warning(plugin_manager, mock_plugin_class, caplog):
    mock_plugin_instance_1 = mock_plugin_class(value=1)
    mock_plugin_instance_2 = mock_plugin_class(value=2)

    plugin_manager.register_plugin(mock_plugin_instance_1)
    
    with caplog.at_level(logging.WARNING):
        plugin_manager.register_plugin(mock_plugin_instance_2)
        assert "Plugin 'MockPlugin' already registered. Overwriting existing plugin." in caplog.text
    
    assert plugin_manager.get_plugin("MockPlugin") is mock_plugin_instance_2
    assert len(plugin_manager._plugins) == 1

def test_get_plugin_found(plugin_manager, mock_plugin_class):
    mock_plugin_instance = mock_plugin_class()
    plugin_manager.register_plugin(mock_plugin_instance)
    retrieved_plugin = plugin_manager.get_plugin("MockPlugin")
    assert retrieved_plugin is mock_plugin_instance

def test_get_plugin_not_found(plugin_manager):
    retrieved_plugin = plugin_manager.get_plugin("NonExistentPlugin")
    assert retrieved_plugin is None

def test_get_all_plugins(plugin_manager, mock_plugin_class, another_mock_plugin_class):
    mock_plugin_1 = mock_plugin_class()
    mock_plugin_2 = another_mock_plugin_class()
    plugin_manager.register_plugin(mock_plugin_1)
    plugin_manager.register_plugin(mock_plugin_2)

    all_plugins = plugin_manager.get_all_plugins()
    assert isinstance(all_plugins, dict)
    assert len(all_plugins) == 2
    assert all_plugins["MockPlugin"] is mock_plugin_1
    assert all_plugins["AnotherMockPlugin"] is mock_plugin_2

    # Verify it's a copy
    all_plugins["NewPlugin"] = "test"
    assert "NewPlugin" not in plugin_manager._plugins

def test_registered_plugin_names(plugin_manager, mock_plugin_class, another_mock_plugin_class):
    assert plugin_manager.registered_plugin_names == []

    plugin_manager.register_plugin(mock_plugin_class())
    assert "MockPlugin" in plugin_manager.registered_plugin_names
    assert len(plugin_manager.registered_plugin_names) == 1

    plugin_manager.register_plugin(another_mock_plugin_class())
    assert set(plugin_manager.registered_plugin_names) == {"MockPlugin", "AnotherMockPlugin"}
    assert len(plugin_manager.registered_plugin_names) == 2

    plugin_manager.unregister_plugin("MockPlugin")
    assert plugin_manager.registered_plugin_names == ["AnotherMockPlugin"]

def test_unregister_plugin_success(plugin_manager, mock_plugin_class):
    mock_plugin_instance = mock_plugin_class()
    plugin_manager.register_plugin(mock_plugin_instance)
    assert "MockPlugin" in plugin_manager._plugins

    result = plugin_manager.unregister_plugin("MockPlugin")
    assert result is True
    assert "MockPlugin" not in plugin_manager._plugins
    assert plugin_manager.get_plugin("MockPlugin") is None

def test_unregister_plugin_not_found(plugin_manager, caplog):
    with caplog.at_level(logging.WARNING):
        result = plugin_manager.unregister_plugin("NonExistentPlugin")
        assert "Attempted to unregister non-existent plugin: 'NonExistentPlugin'." in caplog.text
    assert result is False

# --- Tests for load_plugins_from_directory ---

def create_plugin_file(tmp_path, file_name, content):
    """Helper to create a plugin file in a temporary directory."""
    file_path = tmp_path / file_name
    file_path.write_text(content)
    return file_path

def test_load_plugins_from_directory_success(plugin_manager, tmp_path):
    plugin_code = """
from src.ai_self_ext_engine.core.plugin_manager import BasePlugin

class MyTestPlugin(BasePlugin):
    name = "TestPluginOne"
    description = "A plugin for testing."
    async def execute(self, context):
        context["TestPluginOneExecuted"] = True
        return context
"""
    create_plugin_file(tmp_path, "plugin_one.py", plugin_code)

    plugin_manager.load_plugins_from_directory(tmp_path)
    assert "TestPluginOne" in plugin_manager.registered_plugin_names
    plugin = plugin_manager.get_plugin("TestPluginOne")
    assert isinstance(plugin, BasePlugin)
    
    # Test execution to ensure it's a valid instance
    context = {}
    asyncio.run(plugin.execute(context))
    assert context["TestPluginOneExecuted"] is True


def test_load_plugins_from_directory_multiple_plugins(plugin_manager, tmp_path):
    plugin_code_1 = """
from src.ai_self_ext_engine.core.plugin_manager import BasePlugin
class PluginA(BasePlugin):
    name = "PluginA"
    async def execute(self, context): return context
"""
    plugin_code_2 = """
from src.ai_self_ext_engine.core.plugin_manager import BasePlugin
class PluginB(BasePlugin):
    name = "PluginB"
    async def execute(self, context): return context
"""
    create_plugin_file(tmp_path, "plugin_a.py", plugin_code_1)
    create_plugin_file(tmp_path, "plugin_b.py", plugin_code_2)

    plugin_manager.load_plugins_from_directory(tmp_path)
    assert "PluginA" in plugin_manager.registered_plugin_names
    assert "PluginB" in plugin_manager.registered_plugin_names
    assert len(plugin_manager.registered_plugin_names) == 2

def test_load_plugins_from_directory_no_dir(plugin_manager, caplog):
    non_existent_path = Path("/non/existent/path/for_plugins")
    
    with caplog.at_level(logging.WARNING):
        plugin_manager.load_plugins_from_directory(non_existent_path)
        assert f"Plugin directory not found or is not a directory: {non_existent_path}" in caplog.text
    assert len(plugin_manager.registered_plugin_names) == 0

def test_load_plugins_from_directory_invalid_python_file(plugin_manager, tmp_path, caplog):
    invalid_code = """
this is not valid python syntax
def func():
    return 1
"""
    create_plugin_file(tmp_path, "invalid_plugin.py", invalid_code)

    with caplog.at_level(logging.ERROR):
        plugin_manager.load_plugins_from_directory(tmp_path)
        assert "Failed to load module 'invalid_plugin.py' as a plugin" in caplog.text
    assert len(plugin_manager.registered_plugin_names) == 0

def test_load_plugins_from_directory_file_no_plugin_class(plugin_manager, tmp_path):
    no_plugin_code = """
class JustAClass:
    pass
def some_function():
    pass
"""
    create_plugin_file(tmp_path, "no_plugin_here.py", no_plugin_code)
    
    plugin_manager.load_plugins_from_directory(tmp_path)
    assert len(plugin_manager.registered_plugin_names) == 0

def test_load_plugins_from_directory_skips_init_py(plugin_manager, tmp_path):
    init_code = """
from src.ai_self_ext_engine.core.plugin_manager import BasePlugin
class InitPlugin(BasePlugin):
    name = "InitPlugin"
    async def execute(self, context): return context
"""
    create_plugin_file(tmp_path, "__init__.py", init_code)
    
    plugin_manager.load_plugins_from_directory(tmp_path)
    assert "InitPlugin" not in plugin_manager.registered_plugin_names
    assert len(plugin_manager.registered_plugin_names) == 0

def test_load_plugins_from_directory_custom_base_class(plugin_manager, tmp_path):
    # Create a temporary 'plugins' directory
    plugin_dir = tmp_path / "custom_base_plugins"
    plugin_dir.mkdir()

    # Create a module for the custom base class itself, ensuring it imports from the source
    custom_base_module_code = """
from src.ai_self_ext_engine.core.plugin_manager import BasePlugin

class CustomSpecificBasePlugin(BasePlugin):
    pass
"""
    create_plugin_file(plugin_dir, "custom_base.py", custom_base_module_code)

    # Create a plugin that inherits from CustomSpecificBasePlugin
    # For this to work with `importlib.util`, the `custom_base` module needs to be importable
    # by the plugin module. A common way is to add the plugin_dir to sys.path *before* the import.
    # The `importlib.util.spec_from_file_location` and `module_from_spec` handles this.
    plugin_inheriting_custom_code = """
from custom_base import CustomSpecificBasePlugin

class MyCustomPlugin(CustomSpecificBasePlugin):
    name = "MyCustomPlugin"
    async def execute(self, context):
        context["CustomPluginExecuted"] = True
        return context
"""
