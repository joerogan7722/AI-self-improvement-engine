from abc import ABC, abstractmethod
from typing import Any, Optional

class Plugin(ABC):
    """
    Abstract base class for all plugins in the self-extending engine.
    Plugins provide specific capabilities, such as language support or tool integration.
    """
    @abstractmethod
    def detect(self, code: str) -> bool:
        """
        Detects if the plugin is applicable to the given code.
        """
        pass

    @abstractmethod
    def execute(self, command: str, **kwargs) -> Any:
        """
        Executes a command specific to the plugin's capability.
        """
        pass

    @abstractmethod
    def test(self, code: str, tests: Optional[str] = None) -> Any:
        """
        Runs tests for the given code using the plugin's testing framework.
        """
        pass
