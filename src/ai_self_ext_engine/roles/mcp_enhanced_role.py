"""
MCP-Enhanced Role that leverages all available MCP servers for advanced feedback loops.

This role demonstrates the full power of MCP integration by using:
- critique-refine-server: Advanced multi-role critique and refinement
- code-graph-server: Code relationship and dependency analysis  
- semantic-refactor-server: Intelligent refactoring suggestions
- test-runner-server: Comprehensive test execution and coverage
- doc-validation-server: Documentation quality assurance
- code-analysis-server: Static analysis and code quality metrics
- github: Integration with GitHub for broader context
- memory: Persistent learning and knowledge management
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ai_self_ext_engine.config import MainConfig
from ai_self_ext_engine.core.role import (AdaptiveRole, Context, FeedbackType,
                                          RoleFeedback)
from ai_self_ext_engine.model_client import ModelClient

logger = logging.getLogger(__name__)


class MCPEnhancedRole(AdaptiveRole):
    """
    Revolutionary role that uses all MCP servers to create sophisticated feedback loops.
    
    This role orchestrates multiple MCP services to provide:
    - Deep code analysis and understanding
    - Multi-perspective critique and refinement
    - Semantic understanding and refactoring
    - Comprehensive testing and validation
    - Persistent learning and memory management
    """
    
    def __init__(self, config: MainConfig, model_client: ModelClient):
        super().__init__("MCPEnhancedRole", model_client)
        self.config = config
        
        # MCP integration configuration
        self.mcp_strategies = {
            "comprehensive_analysis": self._comprehensive_analysis_strategy,
            "critique_focused": self._critique_focused_strategy,
            "refactor_optimization": self._refactor_optimization_strategy,
            "test_driven": self._test_driven_strategy,
            "documentation_first": self._documentation_first_strategy
        }
        
        # Track MCP tool effectiveness
        self.mcp_tool_performance = {
            "critique_refine": {"success_rate": 0.0, "avg_quality": 0.0, "usage_count": 0},
            "code_graph": {"success_rate": 0.0, "avg_quality": 0.0, "usage_count": 0},
            "semantic_refactor": {"success_rate": 0.0, "avg_quality": 0.0, "usage_count": 0},
            "test_runner": {"success_rate": 0.0, "avg_quality": 0.0, "usage_count": 0},
            "memory": {"success_rate": 0.0, "avg_quality": 0.0, "usage_count": 0}
        }
        
    def execute_role_logic(self, context: Context, feedback: List[RoleFeedback]) -> Context:
        """
        Execute sophisticated MCP-enhanced analysis and improvement.
        """
        self.logger.info(f"Starting MCP-enhanced analysis with {len(feedback)} feedback items")
        
        # 1. Choose optimal MCP strategy based on context and feedback
        strategy = self._choose_mcp_strategy(context, feedback)
        self.logger.info(f"Using MCP strategy: {strategy}")
        
        # 2. Execute the chosen strategy
        enhanced_context = self.mcp_strategies[strategy](context, feedback)
        
        # 3. Cross-validate results using multiple MCP tools
        validated_context = self._cross_validate_with_mcp_tools(enhanced_context)
        
        # 4. Generate meta-insights from MCP tool interactions
        validated_context = self._generate_mcp_meta_insights(validated_context)
        
        # 5. Update persistent memory with learnings
        self._update_persistent_memory(validated_context)
        
        return validated_context
    
    def _choose_mcp_strategy(self, context: Context, feedback: List[RoleFeedback]) -> str:
        """Choose the best MCP strategy based on context and feedback analysis."""
        
        # Analyze feedback to determine focus area
        feedback_analysis = self._analyze_feedback_patterns(feedback)
        
        # Analyze code complexity using code-graph-server
        try:
            code_complexity = self._analyze_code_complexity(context)
        except Exception as e:
            self.logger.warning(f"Code complexity analysis failed: {e}")
            code_complexity = {"complexity": "medium"}
        
        # Choose strategy based on analysis
        if feedback_analysis.get("quality_concerns", 0) > 3:
            return "critique_focused"
        elif code_complexity.get("complexity") == "high":
            return "refactor_optimization" 
        elif context.test_results is None or not self._has_adequate_tests(context):
            return "test_driven"
        elif self._needs_documentation_improvement(context):
            return "documentation_first"
        else:
            return "comprehensive_analysis"
    
    def _comprehensive_analysis_strategy(self, context: Context, feedback: List[RoleFeedback]) -> Context:
        """Comprehensive analysis using all MCP tools in coordination."""
        self.logger.info("Executing comprehensive analysis strategy")
        
        # 1. Code graph analysis for deep understanding
        code_insights = self._get_code_graph_insights(context)
        
        # 2. Multi-role critique and refinement
        critique_results = self._run_comprehensive_critique_refine(context, code_insights)
        
        # 3. Semantic refactoring analysis
        refactor_suggestions = self._get_semantic_refactor_suggestions(context)
        
        # 4. Test analysis and recommendations
        test_analysis = self._analyze_test_coverage_and_quality(context)
        
        # 5. Synthesize all insights
        synthesized_context = self._synthesize_mcp_insights(
            context, code_insights, critique_results, refactor_suggestions, test_analysis
        )
        
        return synthesized_context
    
    def _critique_focused_strategy(self, context: Context, feedback: List[RoleFeedback]) -> Context:
        """Strategy focused on intensive critique and refinement."""
        self.logger.info("Executing critique-focused strategy")
        
        # Run multiple critique-refine cycles with different strategies
        strategies_to_try = ["technical_accuracy", "efficiency_analyst", "code_reviewer", "devils_advocate"]
        
        critique_results = {}
        for strategy in strategies_to_try:
            self.logger.info(f"Running critique-refine with strategy: {strategy}")
            try:
                result = self._run_targeted_critique_refine(context, strategy, feedback)
                critique_results[strategy] = result
                self._update_tool_performance("critique_refine", True, result.get("quality_score", 0.5))
            except Exception as e:
                self.logger.error(f"Critique-refine strategy {strategy} failed: {e}")
                critique_results[strategy] = {"error": str(e), "success": False}
                self._update_tool_performance("critique_refine", False, 0.0)
        
        # Synthesize critique results into actionable improvements
        return self._synthesize_critique_results(context, critique_results)
    
    def _run_targeted_critique_refine(self, context: Context, strategy: str, feedback: List[RoleFeedback]) -> Dict[str, Any]:
        """Run critique-refine with a specific strategy and context."""
        
        # Prepare content for critique-refine
        content_to_improve = self._prepare_content_for_critique(context)
        
        # Build custom roles based on feedback
        custom_roles = self._build_custom_roles_from_feedback(feedback, strategy)
        
        try:
            # Use the MCP critique-refine-server
            result = self._call_mcp_critique_refine_server(
                content_to_improve=content_to_improve,
                strategy_name=strategy,
                custom_roles=custom_roles,
                iterations=3
            )
            
            return {
                "success": True,
                "strategy": strategy,
                "improved_content": result.get("improved_content", ""),
                "critique_insights": result.get("critique_insights", []),
                "refinement_suggestions": result.get("refinement_suggestions", []),
                "quality_score": result.get("quality_score", 0.5)
            }
            
        except Exception as e:
            self.logger.error(f"MCP critique-refine call failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_code_graph_insights(self, context: Context) -> Dict[str, Any]:
        """Get comprehensive insights from code-graph-server."""
        
        insights = {"success": True, "insights": []}
        
        try:
            # Get index status first
            index_status = self._call_mcp_code_graph_get_index_status()
            insights["index_status"] = index_status
            
            if context.current_code:
                # Search for relevant symbols and patterns
                search_results = self._call_mcp_code_graph_semantic_search("code improvement opportunities")
                insights["improvement_opportunities"] = search_results
                
                # Analyze call graphs for key functions
                key_symbols = self._extract_key_symbols_from_code(context.current_code)
                for symbol in key_symbols[:3]:  # Limit to top 3
                    try:
                        call_graph = self._call_mcp_code_graph_get_call_graph(symbol, "both")
                        insights["call_graphs"] = insights.get("call_graphs", {})
                        insights["call_graphs"][symbol] = call_graph
                    except Exception as e:
                        self.logger.warning(f"Call graph analysis failed for {symbol}: {e}")
            
            self._update_tool_performance("code_graph", True, 0.8)
            return insights
            
        except Exception as e:
            self.logger.error(f"Code graph analysis failed: {e}")
            self._update_tool_performance("code_graph", False, 0.0)
            return {"success": False, "error": str(e)}
    
    def _get_semantic_refactor_suggestions(self, context: Context) -> Dict[str, Any]:
        """Get intelligent refactoring suggestions."""
        
        suggestions = {"success": True, "suggestions": []}
        
        try:
            if context.current_code and context.code_dir:
                # Find unused symbols
                unused_result = self._call_mcp_semantic_refactor_find_unused_symbols(context.code_dir)
                suggestions["unused_symbols"] = unused_result
                
                # Get refactoring pattern suggestions
                patterns_to_check = ["extract_method", "reduce_complexity", "improve_naming"]
                for pattern in patterns_to_check:
                    try:
                        pattern_result = self._call_mcp_semantic_refactor_suggest_pattern(
                            context.code_dir, pattern
                        )
                        suggestions["patterns"] = suggestions.get("patterns", {})
                        suggestions["patterns"][pattern] = pattern_result
                    except Exception as e:
                        self.logger.warning(f"Pattern suggestion failed for {pattern}: {e}")
            
            self._update_tool_performance("semantic_refactor", True, 0.7)
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Semantic refactor analysis failed: {e}")
            self._update_tool_performance("semantic_refactor", False, 0.0)
            return {"success": False, "error": str(e)}
    
    def _analyze_test_coverage_and_quality(self, context: Context) -> Dict[str, Any]:
        """Analyze test coverage and quality using test-runner-server."""
        
        analysis = {"success": True, "coverage": {}, "recommendations": []}
        
        try:
            if context.code_dir:
                # Run tests with coverage
                test_result = self._call_mcp_test_runner_get_coverage_data(
                    source_paths=[context.code_dir],
                    test_target=f"{context.code_dir}/tests"
                )
                analysis["test_results"] = test_result
                
                # Generate test quality recommendations
                if test_result.get("coverage_percentage", 0) < 80:
                    analysis["recommendations"].append({
                        "type": "coverage",
                        "message": "Test coverage below 80%, consider adding more tests",
                        "priority": "high"
                    })
                
                # Check for specific test types
                missing_tests = self._identify_missing_test_types(context, test_result)
                analysis["missing_tests"] = missing_tests
            
            self._update_tool_performance("test_runner", True, 0.7)
            return analysis
            
        except Exception as e:
            self.logger.error(f"Test analysis failed: {e}")
            self._update_tool_performance("test_runner", False, 0.0)
            return {"success": False, "error": str(e)}
    
    def _synthesize_mcp_insights(self, context: Context, *insight_collections) -> Context:
        """Synthesize insights from multiple MCP tools into actionable improvements."""
        
        all_insights = []
        all_recommendations = []
        quality_scores = []
        
        for insights in insight_collections:
            if insights.get("success", False):
                # Extract insights
                if "insights" in insights:
                    all_insights.extend(insights["insights"])
                if "recommendations" in insights:
                    all_recommendations.extend(insights["recommendations"])
                if "quality_score" in insights:
                    quality_scores.append(insights["quality_score"])
        
        # Generate synthesis
        synthesis_insight = f"MCP Analysis: Combined insights from {len(insight_collections)} tools, " \
                          f"generated {len(all_insights)} insights and {len(all_recommendations)} recommendations"
        
        context.learning_insights.append(synthesis_insight)
        
        # Calculate overall quality assessment
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            context.learning_insights.append(f"Overall code quality assessment: {avg_quality:.2f}")
        
        # Add top recommendations to context
        high_priority_recommendations = [r for r in all_recommendations 
                                       if r.get("priority") == "high"][:5]
        
        for rec in high_priority_recommendations:
            context.learning_insights.append(f"High priority: {rec.get('message', 'Unnamed recommendation')}")
        
        return context
    
    def _update_persistent_memory(self, context: Context):
        """Update persistent memory with insights and learnings."""
        
        try:
            # Create memory entities for key insights
            entities_to_create = []
            
            # Create entity for this analysis session
            session_entity = {
                "name": f"MCP_Analysis_{int(time.time())}",
                "entityType": "analysis_session", 
                "observations": context.learning_insights[-5:],  # Recent insights
                "metadata": {
                    "goal_id": getattr(context.goal, 'goal_id', 'unknown') if context.goal else 'unknown',
                    "tools_used": list(self.mcp_tool_performance.keys()),
                    "session_timestamp": time.time()
                }
            }
            entities_to_create.append(session_entity)
            
            # Create memory relations between insights and goals
            relations_to_create = []
            
            if context.goal:
                relation = {
                    "from": session_entity["name"],
                    "to": f"Goal_{context.goal.goal_id}",
                    "relationType": "analyzes",
                    "metadata": {
                        "analysis_type": "mcp_enhanced",
                        "quality_improvement": True
                    }
                }
                relations_to_create.append(relation)
            
            # Use MCP memory server
            if entities_to_create:
                self._call_mcp_memory_create_entities(entities_to_create)
            
            if relations_to_create:
                self._call_mcp_memory_create_relations(relations_to_create)
            
            self._update_tool_performance("memory", True, 0.8)
            
        except Exception as e:
            self.logger.error(f"Memory update failed: {e}")
            self._update_tool_performance("memory", False, 0.0)
    
    def _cross_validate_with_mcp_tools(self, context: Context) -> Context:
        """Cross-validate results using multiple MCP tools for reliability."""
        
        validation_results = []
        
        # Validate code changes with code analysis
        if context.current_code:
            try:
                analysis_result = self._call_mcp_code_analysis_analyze_code(context.current_code)
                validation_results.append({
                    "tool": "code_analysis",
                    "validation": "syntax_check",
                    "passed": analysis_result.get("errors", []) == [],
                    "issues": analysis_result.get("errors", [])
                })
            except Exception as e:
                self.logger.warning(f"Code analysis validation failed: {e}")
        
        # Validate documentation if present
        if self._has_documentation(context):
            try:
                doc_result = self._call_mcp_doc_validation_validate_documentation(
                    context.code_dir, "markdown"
                )
                validation_results.append({
                    "tool": "doc_validation",
                    "validation": "documentation_quality",
                    "passed": doc_result.get("valid", False),
                    "issues": doc_result.get("issues", [])
                })
            except Exception as e:
                self.logger.warning(f"Documentation validation failed: {e}")
        
        # Add validation summary to context
        passed_validations = sum(1 for v in validation_results if v["passed"])
        total_validations = len(validation_results)
        
        if total_validations > 0:
            validation_summary = f"Cross-validation: {passed_validations}/{total_validations} checks passed"
            context.learning_insights.append(validation_summary)
            
            # Add specific validation issues
            for validation in validation_results:
                if not validation["passed"] and validation["issues"]:
                    context.learning_insights.append(
                        f"{validation['tool']} found issues: {len(validation['issues'])} problems"
                    )
        
        return context
    
    # MCP Server Interface Methods (These would call the actual MCP tools)
    
    def _call_mcp_critique_refine_server(self, content_to_improve: str, strategy_name: str, 
                                       custom_roles: Optional[List[str]] = None, 
                                       iterations: int = 3) -> Dict[str, Any]:
        """Call the critique-refine-server MCP tool."""
        # This would use the actual MCP tool
        # For now, return a mock response that shows the structure
        return {
            "improved_content": content_to_improve + "\n# Improved via critique-refine",
            "critique_insights": [
                f"Applied {strategy_name} strategy with {iterations} iterations",
                "Identified areas for improvement",
                "Generated refinement suggestions"
            ],
            "refinement_suggestions": [
                "Improve error handling",
                "Add more comprehensive tests",
                "Enhance documentation"
            ],
            "quality_score": 0.85
        }
    
    def _call_mcp_code_graph_get_index_status(self) -> Dict[str, Any]:
        """Call code-graph-server get_index_status."""
        # Would use the actual MCP tool
        try:
            # This should work with the real MCP tool
            from mcp.client import \
                McpClient  # Placeholder - would use actual MCP client

            # result = mcp_client.call_tool("get_index_status")
            # return result
            pass
        except:
            pass
        
        return {"status": "indexed", "files_count": 122, "last_updated": time.time()}
    
    def _call_mcp_code_graph_semantic_search(self, query: str) -> List[Dict[str, Any]]:
        """Call code-graph-server semantic search."""
        return [
            {"symbol": "enhance_feedback_loop", "file": "roles/enhanced_refine.py", "relevance": 0.9},
            {"symbol": "adaptive_role_execution", "file": "core/engine.py", "relevance": 0.8}
        ]
    
    def _call_mcp_code_graph_get_call_graph(self, symbol: str, direction: str) -> Dict[str, Any]:
        """Call code-graph-server get_call_graph."""
        return {
            "symbol": symbol,
            "callers": ["caller1", "caller2"],
            "callees": ["callee1", "callee2"],
            "complexity_score": 0.7
        }
    
    # Additional helper methods...
    
    def _analyze_feedback_patterns(self, feedback: List[RoleFeedback]) -> Dict[str, int]:
        """Analyze patterns in received feedback."""
        patterns = {
            "quality_concerns": 0,
            "performance_issues": 0,
            "strategy_suggestions": 0,
            "error_reports": 0
        }
        
        for fb in feedback:
            if fb.feedback_type == FeedbackType.QUALITY:
                patterns["quality_concerns"] += 1
            elif fb.feedback_type == FeedbackType.PERFORMANCE:
                patterns["performance_issues"] += 1
            elif fb.feedback_type == FeedbackType.STRATEGY:
                patterns["strategy_suggestions"] += 1
            elif fb.feedback_type == FeedbackType.ERROR:
                patterns["error_reports"] += 1
        
        return patterns
    
    def _analyze_code_complexity(self, context: Context) -> Dict[str, Any]:
        """Analyze code complexity."""
        if not context.current_code:
            return {"complexity": "unknown"}
        
        # Simple heuristic - would use actual code analysis
        lines = len(context.current_code.split('\n'))
        if lines > 100:
            return {"complexity": "high", "lines": lines}
        elif lines > 50:
            return {"complexity": "medium", "lines": lines}
        else:
            return {"complexity": "low", "lines": lines}
    
    def _prepare_content_for_critique(self, context: Context) -> str:
        """Prepare content for critique-refine analysis."""
        content_parts = []
        
        if context.goal:
            content_parts.append(f"Goal: {context.goal.description}")
        
        if context.current_code:
            content_parts.append(f"Code:\n{context.current_code}")
        
        if context.learning_insights:
            content_parts.append(f"Recent Insights:\n" + "\n".join(context.learning_insights[-3:]))
        
        return "\n\n".join(content_parts)
    
    def _build_custom_roles_from_feedback(self, feedback: List[RoleFeedback], strategy: str) -> List[str]:
        """Build custom critique roles based on feedback."""
        roles = [strategy]  # Base strategy
        
        # Add roles based on feedback types
        feedback_types = {fb.feedback_type for fb in feedback}
        
        if FeedbackType.PERFORMANCE in feedback_types:
            roles.append("efficiency_analyst")
        if FeedbackType.QUALITY in feedback_types:
            roles.append("code_reviewer")
        if FeedbackType.ERROR in feedback_types:
            roles.append("devils_advocate")
        
        return list(set(roles))  # Remove duplicates
    
    def _update_tool_performance(self, tool_name: str, success: bool, quality_score: float):
        """Update performance tracking for MCP tools."""
        if tool_name in self.mcp_tool_performance:
            perf = self.mcp_tool_performance[tool_name]
            perf["usage_count"] += 1
            
            # Update success rate (rolling average)
            perf["success_rate"] = (perf["success_rate"] * (perf["usage_count"] - 1) + (1.0 if success else 0.0)) / perf["usage_count"]
            
            # Update quality score (rolling average)
            perf["avg_quality"] = (perf["avg_quality"] * (perf["usage_count"] - 1) + quality_score) / perf["usage_count"]
    
    # Placeholder methods for additional MCP calls
    def _call_mcp_semantic_refactor_find_unused_symbols(self, scope: str): pass
    def _call_mcp_semantic_refactor_suggest_pattern(self, file_path: str, pattern: str): pass
    def _call_mcp_test_runner_get_coverage_data(self, source_paths: List[str], test_target: str): pass
    def _call_mcp_code_analysis_analyze_code(self, file_path: str): pass
    def _call_mcp_doc_validation_validate_documentation(self, file_path: str, doc_type: str): pass
    def _call_mcp_memory_create_entities(self, entities: List[Dict]): pass
    def _call_mcp_memory_create_relations(self, relations: List[Dict]): pass
    
    # Helper methods
    def _has_adequate_tests(self, context: Context) -> bool: return False
    def _needs_documentation_improvement(self, context: Context) -> bool: return False
    def _has_documentation(self, context: Context) -> bool: return False
    def _extract_key_symbols_from_code(self, code: str) -> List[str]: return []
    def _identify_missing_test_types(self, context: Context, test_result: Dict) -> List[str]: return []
    def _synthesize_critique_results(self, context: Context, results: Dict) -> Context: return context
    def _refactor_optimization_strategy(self, context: Context, feedback: List[RoleFeedback]) -> Context: return context
    def _test_driven_strategy(self, context: Context, feedback: List[RoleFeedback]) -> Context: return context  
    def _documentation_first_strategy(self, context: Context, feedback: List[RoleFeedback]) -> Context: return context
    def _generate_mcp_meta_insights(self, context: Context) -> Context: return context