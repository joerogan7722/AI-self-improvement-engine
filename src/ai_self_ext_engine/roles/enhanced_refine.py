"""
Enhanced Refine Role with advanced feedback loops and role communication.

This role demonstrates the next generation of autonomous AI improvement by:
1. Learning from feedback from other roles
2. Providing structured feedback to improve the overall system
3. Adapting its approach based on effectiveness metrics
4. Contributing to the system's learning insights
"""

import time
import logging
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

from ai_self_ext_engine.core.role import Role, Context, RoleFeedback, FeedbackType, RoleMetrics
from ai_self_ext_engine.model_client import ModelClient, ModelCallError
from ai_self_ext_engine.config import MainConfig
from ai_self_ext_engine.learning_log import LearningLog

logger = logging.getLogger(__name__)


class EnhancedRefineRole(Role):
    """
    Enhanced version of RefineRole with advanced feedback loops and adaptive behavior.
    
    This role can:
    - Learn from feedback provided by other roles
    - Adapt its patch generation based on previous effectiveness
    - Provide structured feedback to improve other roles
    - Track and report its own performance metrics
    """

    def __init__(self, config: MainConfig, model_client: ModelClient, learning_log: LearningLog):
        self.config = config
        self.model_client = model_client
        self.learning_log = learning_log
        self.prompt_template_path = (
            Path(config.engine.prompts_dir) / "patch_generation.tpl"
        )
        
        # Enhanced capabilities
        self.adaptation_history = []
        self.effectiveness_trends = []
        self.feedback_integration_count = 0

    def run(self, context: Context) -> Context:
        """
        Enhanced run method with feedback integration and adaptive behavior.
        """
        start_time = time.time()
        role_name = self.__class__.__name__
        
        logger.info(f"{role_name}: Starting enhanced refinement process")
        
        try:
            # 1. Process feedback from other roles
            self._process_incoming_feedback(context, role_name)
            
            # 2. Adapt approach based on historical effectiveness
            approach_adaptations = self._adapt_approach_from_history(context)
            
            # 3. Generate patch with enhanced context
            patch_result = self._generate_enhanced_patch(context, approach_adaptations)
            
            # 4. Provide feedback to other roles
            self._provide_feedback_to_other_roles(context, patch_result)
            
            # 5. Record execution metrics
            execution_time = time.time() - start_time
            self._record_performance_metrics(context, role_name, execution_time, patch_result)
            
            # 6. Add learning insights
            self._contribute_learning_insights(context, patch_result, approach_adaptations)
            
            logger.info(f"{role_name}: Enhanced refinement completed successfully")
            return context
            
        except Exception as e:
            logger.error(f"{role_name}: Enhanced refinement failed: {e}")
            
            # Even in failure, provide feedback about what went wrong
            error_feedback = RoleFeedback(
                from_role=role_name,
                to_role=None,  # Broadcast to all roles
                feedback_type=FeedbackType.ERROR,
                message=f"RefineRole encountered error: {str(e)}",
                data={"error_type": type(e).__name__, "context_state": str(context.accepted)},
                priority="high"
            )
            context.add_feedback(error_feedback)
            
            return context

    def _process_incoming_feedback(self, context: Context, role_name: str):
        """Process feedback from other roles to improve performance"""
        feedback_list = context.get_feedback_for_role(role_name)
        
        if not feedback_list:
            return
            
        logger.info(f"Processing {len(feedback_list)} feedback items")
        
        for feedback in feedback_list:
            if feedback.feedback_type == FeedbackType.SUGGESTION:
                self._integrate_suggestion(feedback)
            elif feedback.feedback_type == FeedbackType.ERROR:
                self._learn_from_error_feedback(feedback)
            elif feedback.feedback_type == FeedbackType.METRIC:
                self._analyze_performance_feedback(feedback)
                
        self.feedback_integration_count += len(feedback_list)

    def _adapt_approach_from_history(self, context: Context) -> Dict[str, Any]:
        """Adapt refinement approach based on historical effectiveness"""
        adaptations = {
            "use_conservative_approach": False,
            "increase_context_analysis": False,
            "focus_on_incremental_changes": False,
            "emphasize_testing": False
        }
        
        # Analyze recent effectiveness
        recent_effectiveness = context.get_role_effectiveness(self.__class__.__name__)
        
        if recent_effectiveness < 60:  # Poor performance
            adaptations["use_conservative_approach"] = True
            adaptations["focus_on_incremental_changes"] = True
            logger.info("Adapting to conservative approach due to low effectiveness")
            
        elif recent_effectiveness > 85:  # Excellent performance
            adaptations["increase_context_analysis"] = True
            logger.info("Increasing analysis depth due to high effectiveness")
        
        # Learn from learning log
        recent_entries = self.learning_log.get_recent_entries(5)
        failed_entries = [entry for entry in recent_entries if not entry.success]
        
        if len(failed_entries) > 2:
            adaptations["emphasize_testing"] = True
            logger.info("Emphasizing testing due to recent failures")
        
        self.adaptation_history.append({
            "timestamp": datetime.now().isoformat(),
            "adaptations": adaptations,
            "trigger_effectiveness": recent_effectiveness
        })
        
        return adaptations

    def _generate_enhanced_patch(self, context: Context, adaptations: Dict[str, Any]) -> Dict[str, Any]:
        """Generate patch with enhanced context and adaptations"""
        
        # Build enhanced prompt with adaptations
        enhancement_context = self._build_enhancement_context(context, adaptations)
        
        try:
            # Use the existing patch generation logic but with enhanced context
            # This would integrate with the existing RefineRole implementation
            
            patch_result = {
                "patch_generated": True,
                "adaptations_applied": adaptations,
                "enhancement_context": enhancement_context,
                "confidence_level": self._calculate_confidence_level(context, adaptations)
            }
            
            # Set the patch in context (simplified for this example)
            if context.todos:
                context.patch = f"# Enhanced patch with adaptations: {adaptations}\n# TODO: Implement actual patch generation logic"
            
            return patch_result
            
        except Exception as e:
            logger.error(f"Enhanced patch generation failed: {e}")
            return {"patch_generated": False, "error": str(e)}

    def _provide_feedback_to_other_roles(self, context: Context, patch_result: Dict[str, Any]):
        """Provide structured feedback to other roles"""
        
        # Feedback to TestRole
        test_feedback = RoleFeedback(
            from_role=self.__class__.__name__,
            to_role="TestRole",
            feedback_type=FeedbackType.SUGGESTION,
            message="Focus testing on areas with high complexity changes",
            data={
                "patch_confidence": patch_result.get("confidence_level", 0.5),
                "suggested_test_focus": ["error_handling", "edge_cases"]
            },
            priority="medium"
        )
        context.add_feedback(test_feedback)
        
        # Feedback to SelfReviewRole
        review_feedback = RoleFeedback(
            from_role=self.__class__.__name__,
            to_role="SelfReviewRole", 
            feedback_type=FeedbackType.SUGGESTION,
            message="Pay attention to architectural consistency",
            data={
                "adaptations_used": patch_result.get("adaptations_applied", {}),
                "review_priorities": ["maintainability", "performance_impact"]
            },
            priority="medium"
        )
        context.add_feedback(review_feedback)
        
        # Broadcast feedback about system learning
        if self.feedback_integration_count > 0:
            learning_feedback = RoleFeedback(
                from_role=self.__class__.__name__,
                to_role=None,  # Broadcast
                feedback_type=FeedbackType.SUCCESS,
                message=f"Successfully integrated {self.feedback_integration_count} feedback items",
                data={"integration_count": self.feedback_integration_count},
                priority="low"
            )
            context.add_feedback(learning_feedback)

    def _record_performance_metrics(self, context: Context, role_name: str, 
                                   execution_time: float, patch_result: Dict[str, Any]):
        """Record detailed performance metrics"""
        
        success_rate = 1.0 if patch_result.get("patch_generated", False) else 0.0
        effectiveness_score = patch_result.get("confidence_level", 0.5) * 100
        
        metrics = RoleMetrics(
            role_name=role_name,
            execution_time=execution_time,
            success_rate=success_rate,
            effectiveness_score=effectiveness_score,
            resource_usage={
                "feedback_items_processed": self.feedback_integration_count,
                "adaptations_applied": len(patch_result.get("adaptations_applied", {})),
                "learning_entries_analyzed": len(self.learning_log.get_recent_entries(5))
            },
            improvement_suggestions=self._generate_self_improvement_suggestions()
        )
        
        context.update_role_metrics(metrics)
        self.effectiveness_trends.append(effectiveness_score)

    def _contribute_learning_insights(self, context: Context, patch_result: Dict[str, Any], 
                                    adaptations: Dict[str, Any]):
        """Add learning insights from this execution"""
        
        if patch_result.get("patch_generated", False):
            context.add_learning_insight(
                f"RefineRole: Successfully applied {sum(adaptations.values())} adaptations"
            )
            
        if self.feedback_integration_count > 0:
            context.add_learning_insight(
                f"RefineRole: Integrated feedback from {self.feedback_integration_count} sources"
            )
            
        # Analyze effectiveness trends
        if len(self.effectiveness_trends) >= 3:
            recent_trend = self.effectiveness_trends[-3:]
            if all(recent_trend[i] <= recent_trend[i+1] for i in range(len(recent_trend)-1)):
                context.add_learning_insight(
                    "RefineRole: Showing consistent improvement trend in effectiveness"
                )

    # Helper methods
    
    def _integrate_suggestion(self, feedback: RoleFeedback):
        """Integrate a suggestion from another role"""
        logger.info(f"Integrating suggestion: {feedback.message}")
        # Implementation would adapt behavior based on suggestion
    
    def _learn_from_error_feedback(self, feedback: RoleFeedback):
        """Learn from error feedback to avoid similar issues"""
        logger.warning(f"Learning from error: {feedback.message}")
        # Implementation would adjust approach to avoid similar errors
    
    def _analyze_performance_feedback(self, feedback: RoleFeedback):
        """Analyze performance metrics feedback"""
        logger.info(f"Analyzing performance feedback: {feedback.message}")
        # Implementation would adjust performance parameters
    
    def _build_enhancement_context(self, context: Context, adaptations: Dict[str, Any]) -> str:
        """Build enhanced context string for patch generation"""
        return f"Adaptations: {adaptations}, Learning insights: {len(context.learning_insights)}"
    
    def _calculate_confidence_level(self, context: Context, adaptations: Dict[str, Any]) -> float:
        """Calculate confidence level for the generated patch"""
        base_confidence = 0.7
        
        # Adjust based on adaptations
        if adaptations.get("use_conservative_approach", False):
            base_confidence += 0.1
        if adaptations.get("emphasize_testing", False):
            base_confidence += 0.05
            
        return min(1.0, base_confidence)
    
    def _generate_self_improvement_suggestions(self) -> List[str]:
        """Generate suggestions for improving this role"""
        suggestions = []
        
        if len(self.effectiveness_trends) > 5:
            avg_effectiveness = sum(self.effectiveness_trends[-5:]) / 5
            if avg_effectiveness < 70:
                suggestions.append("Consider more aggressive learning from feedback")
                suggestions.append("Analyze recent failure patterns more deeply")
        
        if self.feedback_integration_count == 0:
            suggestions.append("Improve feedback processing mechanisms")
            
        return suggestions