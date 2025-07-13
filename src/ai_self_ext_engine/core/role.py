from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional, TypeVar, Union
from dataclasses import dataclass, field

# To avoid circular imports, use TYPE_CHECKING for type hints
if TYPE_CHECKING:
    from .engine import Context

@dataclass
class Context:
    """
    The central data object passed between roles, containing all relevant
    information for the current improvement cycle.
    """
    code_dir: str
    current_code: Optional[str] = None
    goal: Optional[Any] = None  # Will be a Goal object from GoalManager
    todos: List[str] = field(default_factory=list)
    patch: Optional[str] = None
    test_results: Optional[Any] = None # Will be a TestResults object
    accepted: bool = False
    should_abort: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict) # For logging additional info

class Role(ABC):
    """
    Abstract base class for all roles in the self-improvement loop.
    Each role performs a specific task and updates the Context.
    """
    @abstractmethod
    def run(self, context: Context) -> Context:
        """
        Executes the role's logic and returns an updated Context object.
        """
        pass

# Define a type variable for roles to enable type hinting for subclasses
RoleType = TypeVar('RoleType', bound=Role)
