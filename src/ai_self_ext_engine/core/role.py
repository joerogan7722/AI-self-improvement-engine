from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (TYPE_CHECKING, Any, Dict, List, Optional, Protocol,
                    TypeVar, Union)

if TYPE_CHECKING:
    from ai_self_ext_engine.goal_manager import Goal
    from ai_self_ext_engine.todo_schema import Todo  # Import for type hinting


class FeedbackType(Enum):
    """Types of feedback that roles can provide to each other"""
    SUCCESS = "success"
    WARNING = "warning" 
    ERROR = "error"
    SUGGESTION = "suggestion"
    METRIC = "metric"
    DEPENDENCY = "dependency"


@dataclass
class RoleFeedback:
    """Structured feedback between roles"""
    from_role: str
    to_role: Optional[str]  # None means feedback for all roles
    feedback_type: FeedbackType
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    priority: str = "medium"  # high, medium, low


@dataclass
class RoleMetrics:
    """Performance and effectiveness metrics for roles"""
    role_name: str
    execution_time: float
    success_rate: float
    effectiveness_score: float  # 0-100 based on outcomes
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    improvement_suggestions: List[str] = field(default_factory=list)


@dataclass
class Context:
    """
    The central data object passed between roles, containing all relevant
    information for the current improvement cycle.
    Enhanced with advanced feedback loops and role communication.
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
    
    # Enhanced feedback and communication systems
    feedback_queue: List[RoleFeedback] = field(default_factory=list)
    role_metrics: Dict[str, RoleMetrics] = field(default_factory=dict)
    execution_history: List[Dict[str, Any]] = field(default_factory=list)
    learning_insights: List[str] = field(default_factory=list)
    
    def add_feedback(self, feedback: RoleFeedback):
        """Add feedback from one role to another"""
        self.feedback_queue.append(feedback)
    
    def get_feedback_for_role(self, role_name: str) -> List[RoleFeedback]:
        """Get all feedback intended for a specific role"""
        return [fb for fb in self.feedback_queue 
                if fb.to_role is None or fb.to_role == role_name]
    
    def record_role_execution(self, role_name: str, execution_data: Dict[str, Any]):
        """Record execution details for a role"""
        execution_record = {
            "role": role_name,
            "timestamp": datetime.now().isoformat(),
            "data": execution_data
        }
        self.execution_history.append(execution_record)
    
    def update_role_metrics(self, metrics: RoleMetrics):
        """Update performance metrics for a role"""
        self.role_metrics[metrics.role_name] = metrics
    
    def get_role_effectiveness(self, role_name: str) -> float:
        """Get effectiveness score for a role"""
        return self.role_metrics.get(role_name, RoleMetrics(role_name, 0, 0, 0)).effectiveness_score
    
    def add_learning_insight(self, insight: str):
        """Add a learning insight from the current cycle"""
        self.learning_insights.append(f"[{datetime.now().isoformat()}] {insight}")


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


class AdaptiveRole:
    """
    Base class for roles with advanced feedback and adaptation capabilities.
    Provides common functionality for inter-role communication and learning.
    """
    
    def __init__(self, name: str, model_client=None):
        self.name = name
        self.model_client = model_client
        self.performance_history = []
        self.adaptation_settings = {}
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    def run(self, context: Context) -> Context:
        """
        Template method that handles feedback processing and performance tracking.
        Subclasses should implement execute_role_logic.
        """
        start_time = time.time()
        
        # Process incoming feedback before execution
        relevant_feedback = self._process_incoming_feedback(context)
        
        # Record execution start
        execution_record = {
            "role": self.name,
            "start_time": start_time,
            "feedback_received": len(relevant_feedback),
            "goal_id": getattr(context.goal, 'goal_id', None) if context.goal else None
        }
        
        try:
            # Execute the role-specific logic
            updated_context = self.execute_role_logic(context, relevant_feedback)
            
            # Record successful execution
            end_time = time.time()
            execution_record.update({
                "end_time": end_time,
                "duration": end_time - start_time,
                "status": "success",
                "insights_generated": len(updated_context.learning_insights) - len(context.learning_insights)
            })
            
            # Update role metrics
            self._update_performance_metrics(execution_record, True)
            
            # Generate feedback for other roles if applicable
            self._generate_feedback_for_peers(updated_context)
            
            # Record execution in context
            updated_context.record_role_execution(self.name, execution_record)
            
            return updated_context
            
        except Exception as e:
            # Record failed execution
            execution_record.update({
                "end_time": time.time(),
                "duration": time.time() - start_time,
                "status": "error",
                "error": str(e)
            })
            
            self._update_performance_metrics(execution_record, False)
            context.record_role_execution(self.name, execution_record)
            
            self.logger.error(f"Role {self.name} failed: {e}")
            raise
    
    @abstractmethod
    def execute_role_logic(self, context: Context, feedback: List[RoleFeedback]) -> Context:
        """
        Role-specific execution logic. Must be implemented by subclasses.
        
        Args:
            context: Current execution context
            feedback: Relevant feedback from other roles
        
        Returns:
            Updated context
        """
        pass
    
    def _process_incoming_feedback(self, context: Context) -> List[RoleFeedback]:
        """Process and filter feedback relevant to this role"""
        relevant_feedback = context.get_feedback_for_role(self.name)
        
        if relevant_feedback:
            self.logger.info(f"Processing {len(relevant_feedback)} feedback items for {self.name}")
            
            # Adapt behavior based on feedback
            self._adapt_based_on_feedback(relevant_feedback)
        
        return relevant_feedback
    
    def _adapt_based_on_feedback(self, feedback: List[RoleFeedback]):
        """Adapt role behavior based on received feedback"""
        for fb in feedback:
            if fb.feedback_type == FeedbackType.PERFORMANCE:
                # Adjust performance-related settings
                if fb.content.get("suggestion") == "increase_thoroughness":
                    self.adaptation_settings["thoroughness_level"] = min(1.0, 
                        self.adaptation_settings.get("thoroughness_level", 0.7) + 0.1)
                elif fb.content.get("suggestion") == "increase_speed":
                    self.adaptation_settings["speed_priority"] = True
            
            elif fb.feedback_type == FeedbackType.QUALITY:
                # Adjust quality-related settings
                quality_score = fb.content.get("quality_score", 0)
                if quality_score < 0.7:
                    self.adaptation_settings["review_iterations"] = min(3,
                        self.adaptation_settings.get("review_iterations", 1) + 1)
            
            elif fb.feedback_type == FeedbackType.STRATEGY:
                # Update strategic approach
                suggested_strategy = fb.content.get("suggested_strategy")
                if suggested_strategy:
                    self.adaptation_settings["preferred_strategy"] = suggested_strategy
    
    def _generate_feedback_for_peers(self, context: Context):
        """Generate feedback for other roles based on execution results"""
        # Example: If this role found issues, warn downstream roles
        if hasattr(self, "_found_issues") and self._found_issues:
            feedback = RoleFeedback(
                from_role=self.name,
                to_role="TestRole",  # Example: warn test role
                feedback_type=FeedbackType.QUALITY,
                content={
                    "warning": "Issues detected in code generation",
                    "recommendation": "Run more thorough tests"
                },
                timestamp=time.time()
            )
            context.add_feedback(feedback)
    
    def _update_performance_metrics(self, execution_record: Dict[str, Any], success: bool):
        """Update performance tracking"""
        self.performance_history.append(execution_record)
        
        # Keep only recent history (last 50 executions)
        if len(self.performance_history) > 50:
            self.performance_history = self.performance_history[-50:]
        
        # Calculate rolling averages
        recent_executions = self.performance_history[-10:]
        avg_duration = sum(ex.get("duration", 0) for ex in recent_executions) / len(recent_executions)
        success_rate = sum(1 for ex in recent_executions if ex.get("status") == "success") / len(recent_executions)
        
        # Update context metrics if available
        metrics = RoleMetrics(
            success_rate=success_rate,
            avg_execution_time=avg_duration,
            total_executions=len(self.performance_history),
            last_execution=time.time()
        )
        
        # Store in performance history for easy access
        execution_record["metrics_snapshot"] = {
            "success_rate": success_rate,
            "avg_duration": avg_duration
        }
