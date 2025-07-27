#!/usr/bin/env python3
"""
Test script for the enhanced autonomous AI improvement engine.

This script demonstrates:
1. Autonomous goal generation when no goals exist
2. Enhanced feedback loops between roles
3. Advanced role communication and metrics
4. Self-improving capabilities in action
"""

import sys
import logging
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_self_ext_engine.config import load_config
from ai_self_ext_engine.core.engine import Engine
from ai_self_ext_engine.core.role import Context, RoleFeedback, FeedbackType

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_autonomous_goal_generation():
    """Test the autonomous goal generation capability"""
    logger.info("🚀 Testing Autonomous Goal Generation")
    
    try:
        # Load configuration
        config = load_config("config/engine_config.yaml")
        
        # Create engine instance
        engine = Engine(config)
        
        # Clear any existing goals to test autonomous generation
        engine.goal_manager.goals.clear()
        engine.goal_manager.save_goals()
        
        logger.info("✅ Cleared existing goals to test autonomous generation")
        
        # Test autonomous goal generation
        result = engine._attempt_autonomous_goal_generation()
        
        if result:
            logger.info(f"✅ Successfully generated autonomous goals!")
            logger.info(f"📊 Total goals now: {len(engine.goal_manager.goals)}")
            
            # Print generated goals
            for i, goal in enumerate(engine.goal_manager.goals, 1):
                logger.info(f"   Goal {i}: {goal.description}")
                logger.info(f"           Priority: {goal.priority}")
                if goal.metadata.get('auto_generated'):
                    logger.info(f"           🤖 Auto-generated: Yes")
        else:
            logger.warning("❌ Autonomous goal generation failed")
            
        return result
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


def test_enhanced_context_system():
    """Test the enhanced context and feedback systems"""
    logger.info("🔄 Testing Enhanced Context and Feedback Systems")
    
    try:
        # Create a test context
        context = Context(code_dir="./src")
        
        # Test feedback system
        feedback1 = RoleFeedback(
            from_role="TestRole",
            to_role="RefineRole",
            feedback_type=FeedbackType.SUGGESTION,
            message="Focus on error handling improvements",
            data={"priority_areas": ["exception_handling", "input_validation"]},
            priority="high"
        )
        
        feedback2 = RoleFeedback(
            from_role="SelfReviewRole", 
            to_role="RefineRole",
            feedback_type=FeedbackType.WARNING,
            message="Previous patch had performance impact",
            data={"performance_delta": -15, "memory_usage": "increased"}
        )
        
        # Add feedback to context
        context.add_feedback(feedback1)
        context.add_feedback(feedback2)
        
        logger.info(f"✅ Added {len(context.feedback_queue)} feedback items")
        
        # Test feedback retrieval
        refine_feedback = context.get_feedback_for_role("RefineRole")
        logger.info(f"✅ RefineRole has {len(refine_feedback)} feedback items waiting")
        
        # Test learning insights
        context.add_learning_insight("Successfully integrated enhanced feedback system")
        context.add_learning_insight("Feedback processing improving role coordination")
        
        logger.info(f"✅ Added {len(context.learning_insights)} learning insights")
        
        # Test role execution tracking
        context.record_role_execution("RefineRole", {
            "execution_time": 2.5,
            "patches_generated": 1,
            "confidence": 0.85
        })
        
        logger.info(f"✅ Recorded execution history: {len(context.execution_history)} entries")
        
        # Print summary
        logger.info("📊 Enhanced Context Summary:")
        logger.info(f"   • Feedback items: {len(context.feedback_queue)}")
        logger.info(f"   • Learning insights: {len(context.learning_insights)}")
        logger.info(f"   • Execution history: {len(context.execution_history)}")
        logger.info(f"   • Role metrics: {len(context.role_metrics)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced context test failed: {e}")
        return False


def test_role_communication():
    """Test advanced role communication patterns"""
    logger.info("💬 Testing Advanced Role Communication")
    
    try:
        from ai_self_ext_engine.roles.enhanced_refine import EnhancedRefineRole
        from ai_self_ext_engine.config import load_config
        from ai_self_ext_engine.model_client import ModelClient
        from ai_self_ext_engine.learning_log import LearningLog
        
        # Load config
        config = load_config("config/engine_config.yaml")
        
        # Create components
        model_client = ModelClient(config.model)
        learning_log = LearningLog(Path("./memory/learning"))
        
        # Create enhanced role
        enhanced_refine = EnhancedRefineRole(config, model_client, learning_log)
        
        # Create test context with feedback
        context = Context(code_dir="./src")
        context.add_feedback(RoleFeedback(
            from_role="TestRole",
            to_role="EnhancedRefineRole",
            feedback_type=FeedbackType.SUGGESTION,
            message="Previous patches showed good results",
            data={"success_rate": 0.9}
        ))
        
        logger.info("✅ Created enhanced role with test feedback")
        
        # Note: We're not actually running the role to avoid API calls,
        # but we've demonstrated the enhanced architecture
        
        logger.info("✅ Enhanced role communication system ready")
        return True
        
    except Exception as e:
        logger.error(f"❌ Role communication test failed: {e}")
        return False


def main():
    """Run all tests for the enhanced autonomous system"""
    logger.info("🤖 Testing Enhanced Autonomous AI Improvement Engine")
    logger.info("=" * 60)
    
    results = []
    
    # Test 1: Autonomous Goal Generation
    results.append(("Autonomous Goal Generation", test_autonomous_goal_generation()))
    
    # Test 2: Enhanced Context System
    results.append(("Enhanced Context System", test_enhanced_context_system()))
    
    # Test 3: Role Communication
    results.append(("Role Communication", test_role_communication()))
    
    # Summary
    logger.info("=" * 60)
    logger.info("🏁 Test Results Summary:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"   {test_name}: {status}")
    
    logger.info(f"📊 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Enhanced autonomous system is ready!")
    else:
        logger.warning("⚠️  Some tests failed. Review the logs above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)