#!/usr/bin/env python3
"""
End-to-end test of the enhanced autonomous AI improvement engine.
Tests the basic autonomous workflow without running the full engine.
"""

import sys
import os
import logging
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_goal_generation_role():
    """Test the GoalGenerationRole standalone"""
    try:
        from ai_self_ext_engine.roles.goal_generation import GoalGenerationRole, CodeMetrics
        from ai_self_ext_engine.core.role import Context
        from ai_self_ext_engine.config import MainConfig, ModelSectionConfig, EngineSectionConfig
        from ai_self_ext_engine.model_client import ModelClient
        
        # Create minimal config
        config = MainConfig(
            engine=EngineSectionConfig(code_dir="./src"),
            model=ModelSectionConfig(api_key_env="GOOGLE_API_KEY"),
            roles=[],
            plugins={},
            logging={}
        )
        
        # Create mock model client (won't actually call API)
        model_client = ModelClient(config.model)
        
        # Create goal generation role
        goal_generator = GoalGenerationRole(config, model_client)
        
        # Test context
        context = Context(code_dir="./src")
        
        # Run goal generation (this will analyze the codebase)
        result_context = goal_generator.run(context)
        
        # Check results
        if 'generated_goals' in result_context.metadata:
            goals = result_context.metadata['generated_goals']
            logger.info(f"✅ GoalGenerationRole generated {len(goals)} goals")
            
            for i, goal in enumerate(goals, 1):
                logger.info(f"   Goal {i}: {goal['description']}")
                logger.info(f"           Priority: {goal['priority']}")
                
            return True, len(goals)
        else:
            logger.warning("❌ No goals generated")
            return False, 0
            
    except Exception as e:
        logger.error(f"❌ GoalGenerationRole test failed: {e}")
        return False, 0

def test_enhanced_context():
    """Test the enhanced Context with feedback systems"""
    try:
        from ai_self_ext_engine.core.role import Context, RoleFeedback, FeedbackType, RoleMetrics
        
        # Create context
        context = Context(code_dir="./src")
        
        # Test feedback system
        feedback = RoleFeedback(
            from_role="TestRole",
            to_role="RefineRole", 
            feedback_type=FeedbackType.SUGGESTION,
            message="Test feedback message",
            data={"test": True}
        )
        
        context.add_feedback(feedback)
        
        # Test feedback retrieval
        refine_feedback = context.get_feedback_for_role("RefineRole")
        
        if len(refine_feedback) == 1:
            logger.info("✅ Enhanced Context feedback system working")
        else:
            logger.error("❌ Enhanced Context feedback system failed")
            return False
            
        # Test learning insights
        context.add_learning_insight("Test insight")
        
        if len(context.learning_insights) == 1:
            logger.info("✅ Enhanced Context learning insights working")
        else:
            logger.error("❌ Enhanced Context learning insights failed")
            return False
            
        # Test role metrics
        metrics = RoleMetrics(
            role_name="TestRole",
            execution_time=1.0,
            success_rate=0.95,
            effectiveness_score=85.0
        )
        
        context.update_role_metrics(metrics)
        
        if context.get_role_effectiveness("TestRole") == 85.0:
            logger.info("✅ Enhanced Context role metrics working")
        else:
            logger.error("❌ Enhanced Context role metrics failed")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced Context test failed: {e}")
        return False

def test_goal_manager_enhancements():
    """Test the enhanced Goal class with priority and metadata"""
    try:
        from ai_self_ext_engine.goal_manager import Goal, GoalManager
        
        # Test enhanced Goal class
        goal = Goal(
            goal_id="test_goal",
            description="Test autonomous goal",
            priority="high",
            metadata={"auto_generated": True, "test": True}
        )
        
        if goal.priority == "high" and goal.metadata.get("auto_generated"):
            logger.info("✅ Enhanced Goal class working")
        else:
            logger.error("❌ Enhanced Goal class failed")
            return False
            
        # Test goal serialization
        goal_dict = goal.to_dict()
        
        if "priority" in goal_dict and "metadata" in goal_dict:
            logger.info("✅ Enhanced Goal serialization working")
        else:
            logger.error("❌ Enhanced Goal serialization failed") 
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Goal Manager test failed: {e}")
        return False

def test_engine_autonomous_integration():
    """Test if the Engine can attempt autonomous goal generation"""
    try:
        from ai_self_ext_engine.config import MainConfig, ModelSectionConfig, EngineSectionConfig
        from ai_self_ext_engine.core.engine import Engine
        
        # Create minimal config
        config = MainConfig(
            engine=EngineSectionConfig(code_dir="./src"),
            model=ModelSectionConfig(api_key_env="GOOGLE_API_KEY"),
            roles=[],
            plugins={},
            logging={}
        )
        
        # Create engine
        engine = Engine(config)
        
        # Clear goals to test autonomous generation
        engine.goal_manager.goals.clear()
        
        # Test autonomous goal generation method
        result = engine._attempt_autonomous_goal_generation()
        
        if result:
            goals_count = len(engine.goal_manager.goals)
            logger.info(f"✅ Engine autonomous goal generation working - {goals_count} goals created")
            return True, goals_count
        else:
            logger.warning("❌ Engine autonomous goal generation returned False")
            return False, 0
            
    except Exception as e:
        logger.error(f"❌ Engine integration test failed: {e}")
        return False, 0

def main():
    """Run end-to-end tests"""
    logger.info("🤖 Testing Enhanced Autonomous AI Improvement Engine End-to-End")
    logger.info("=" * 70)
    
    results = []
    
    # Test 1: Enhanced Context System
    logger.info("🔄 Testing Enhanced Context System...")
    results.append(("Enhanced Context", test_enhanced_context()))
    
    # Test 2: Goal Manager Enhancements  
    logger.info("🎯 Testing Goal Manager Enhancements...")
    results.append(("Goal Manager", test_goal_manager_enhancements()))
    
    # Test 3: Goal Generation Role
    logger.info("🧠 Testing GoalGenerationRole...")
    goal_result, goal_count = test_goal_generation_role()
    results.append(("Goal Generation Role", goal_result))
    
    # Test 4: Engine Integration
    logger.info("🚀 Testing Engine Autonomous Integration...")
    engine_result, engine_goals = test_engine_autonomous_integration()
    results.append(("Engine Integration", engine_result))
    
    # Summary
    logger.info("=" * 70)
    logger.info("🏁 End-to-End Test Results:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"   {test_name}: {status}")
    
    logger.info(f"📊 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 Enhanced autonomous system is working end-to-end!")
        logger.info(f"💡 Generated {goal_count + engine_goals} autonomous goals total")
    else:
        logger.warning("⚠️ Some components need attention before proceeding")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    print(f"\n{'✅ SYSTEM READY' if success else '❌ SYSTEM NEEDS WORK'}")
    sys.exit(0 if success else 1)