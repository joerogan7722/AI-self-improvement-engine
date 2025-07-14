from abc import abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Protocol, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from ai_self_ext_engine.todo_schema import Todo  # Import for type hinting
    from ai_self_ext_engine.goal_manager import Goal


@dataclass
class Context:
    """
    The central data object passed between roles, containing all relevant
    information for the current improvement cycle.
    """
    code_dir: str
    current_code: Optional[str] = None
    goal: Optional["Goal"] = None  # Use the Goal type
    todos: List["Todo"] = field(default_factory=list)  # Use the Todo type
    patch: Optional[str] = None
    test_results: Optional[Any] = None  # Will be a TestResults object
    review: Optional[str] = None
    accepted: bool = False
    should_abort: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)  # For logging
    review_feedback: Optional[Dict[str, Any]] = None


class Role(Protocol):  # Change to Protocol
    """
    Protocol for all roles in the self-improvement loop.
    Each role performs a specific task and updates the Context.
    """
    @abstractmethod
    def run(self, context: Context) -> Context:
        """
        Executes the role's logic and returns an updated Context object.
        """
        pass


# Define a type variable for roles to enable type hinting for subclasses
RoleType = TypeVar("RoleType", bound=Role)
