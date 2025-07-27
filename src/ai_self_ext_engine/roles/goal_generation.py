"""
Goal Generation Role - Automatically identifies improvement opportunities in the codebase.

This role analyzes the current codebase to autonomously generate goals for improvement,
making the system more self-directed and reducing human intervention requirements.
"""

import ast
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_self_ext_engine.config import MainConfig
from ai_self_ext_engine.core.role import Context, Role
from ai_self_ext_engine.goal_manager import Goal
from ai_self_ext_engine.model_client import ModelCallError, ModelClient

logger = logging.getLogger(__name__)


@dataclass
class CodeMetrics:
    """Metrics collected from codebase analysis"""

    complexity_score: float
    test_coverage: float
    file_count: int
    line_count: int
    function_count: int
    class_count: int
    import_complexity: int
    documentation_ratio: float
    code_smells: List[str]


@dataclass
class ImprovementOpportunity:
    """Represents a potential improvement area"""

    area: str
    priority: str  # "high", "medium", "low"
    description: str
    estimated_impact: str
    suggested_approach: str
    files_involved: List[str]


class GoalGenerationRole(Role):
    """
    Analyzes the codebase and automatically generates improvement goals.

    This role implements enhanced autonomy by:
    1. Scanning the codebase for structural analysis
    2. Identifying patterns that suggest improvement opportunities
    3. Prioritizing improvements based on impact and feasibility
    4. Generating concrete, actionable goals
    """

    def __init__(self, config: MainConfig, model_client: ModelClient):
        self.config = config
        self.model_client = model_client
        self.prompt_template_path = (
            Path(config.engine.prompts_dir) / "goal_generation.tpl"
        )

    def run(self, context: Context) -> Context:
        """
        Analyzes codebase and generates improvement goals.
        """
        logger.info("GoalGenerationRole: Starting autonomous goal generation")

        try:
            # 1. Analyze current codebase metrics
            metrics = self._analyze_codebase_metrics(context.code_dir)

            # 2. Identify improvement opportunities
            opportunities = self._identify_improvement_opportunities(metrics)

            # 3. Generate goals using AI analysis
            goals = self._generate_goals_from_opportunities(opportunities, metrics)

            # 4. Update context with generated goals
            context.metadata["generated_goals"] = list(goal.to_dict() for goal in goals)
            context.metadata["codebase_metrics"] = metrics.__dict__
            context.metadata["improvement_opportunities"] = list(
                opp.__dict__ for opp in opportunities
            )

            logger.info(f"GoalGenerationRole: Generated {len(goals)} autonomous goals")

            return context

        except Exception as e:
            logger.error(f"GoalGenerationRole failed: {e}")
            context.metadata["goal_generation_error"] = str(e)
            return context

    def _analyze_codebase_metrics(self, code_dir: str) -> CodeMetrics:
        """
        Performs static analysis of the codebase to gather metrics.
        """
        code_path = Path(code_dir)
        py_files = list(code_path.rglob("*.py"))

        file_metrics = self._analyze_python_files(py_files)
        derived_metrics = self._calculate_derived_metrics(file_metrics, len(py_files))

        return CodeMetrics(
            complexity_score=derived_metrics["complexity_score"],
            test_coverage=0.0,  # Would need pytest-cov integration
            file_count=len(py_files),
            line_count=file_metrics["total_lines"],
            function_count=file_metrics["function_count"],
            class_count=file_metrics["class_count"],
            import_complexity=file_metrics["import_count"],
            documentation_ratio=derived_metrics["documentation_ratio"],
            code_smells=file_metrics["code_smells"],
        )

    def _analyze_python_files(self, py_files: List[Path]) -> Dict[str, Any]:
        """Analyze all Python files and collect raw metrics."""
        metrics = {
            "total_lines": 0,
            "function_count": 0,
            "class_count": 0,
            "import_count": 0,
            "docstring_count": 0,
            "code_smells": [],
        }

        for py_file in py_files:
            file_data = self._analyze_single_file(py_file)
            if file_data:
                for key in metrics:
                    if key == "code_smells":
                        metrics[key].extend(file_data[key])
                    else:
                        metrics[key] += file_data[key]

        return metrics

    def _analyze_single_file(self, py_file: Path) -> Optional[Dict[str, Any]]:
        """Analyze a single Python file for metrics."""
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

                # Parse AST for detailed analysis
                tree = ast.parse(content)
                ast_metrics = self._analyze_ast_nodes(tree, py_file)

                return {
                    "total_lines": len(lines),
                    "function_count": ast_metrics["function_count"],
                    "class_count": ast_metrics["class_count"],
                    "import_count": ast_metrics["import_count"],
                    "docstring_count": ast_metrics["docstring_count"],
                    "code_smells": ast_metrics["code_smells"],
                }

        except (UnicodeDecodeError, SyntaxError) as e:
            logger.warning(f"Could not analyze {py_file}: {e}")
            return None

    def _analyze_ast_nodes(self, tree: ast.AST, py_file: Path) -> Dict[str, Any]:
        """Analyze AST nodes to extract code structure metrics."""
        metrics = {
            "function_count": 0,
            "class_count": 0,
            "import_count": 0,
            "docstring_count": 0,
            "code_smells": [],
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                metrics["function_count"] += 1
                if ast.get_docstring(node):
                    metrics["docstring_count"] += 1
                # Check for code smells
                if len(node.body) > 20:  # Long function
                    metrics["code_smells"].append(
                        f"Long function: {py_file.name}:{node.name}"
                    )

            elif isinstance(node, ast.ClassDef):
                metrics["class_count"] += 1
                if ast.get_docstring(node):
                    metrics["docstring_count"] += 1

            elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                metrics["import_count"] += 1

        return metrics

    def _calculate_derived_metrics(
        self, file_metrics: Dict[str, Any], file_count: int
    ) -> Dict[str, float]:
        """Calculate derived metrics from raw file metrics."""
        complexity_score = min(
            100,
            (file_metrics["function_count"] + file_metrics["class_count"])
            / max(1, file_count)
            * 10,
        )
        documentation_ratio = (
            file_metrics["docstring_count"]
            / max(1, file_metrics["function_count"] + file_metrics["class_count"])
            * 100
        )

        return {
            "complexity_score": complexity_score,
            "documentation_ratio": documentation_ratio,
        }

    def _identify_improvement_opportunities(
        self, metrics: CodeMetrics
    ) -> List[ImprovementOpportunity]:
        """
        Identifies concrete improvement opportunities based on metrics.
        """
        opportunities = []

        # Documentation improvement
        if metrics.documentation_ratio < 50:
            opportunities.append(
                ImprovementOpportunity(
                    area="documentation",
                    priority="medium",
                    description=f"Documentation coverage is only {metrics.documentation_ratio:.1f}%",
                    estimated_impact="Improved maintainability and onboarding",
                    suggested_approach="Add docstrings to functions and classes",
                    files_involved=["Multiple files need docstrings"],
                )
            )

        # Code complexity reduction
        if metrics.code_smells:
            opportunities.append(
                ImprovementOpportunity(
                    area="refactoring",
                    priority="high",
                    description=f"Found {len(metrics.code_smells)} code smells requiring attention",
                    estimated_impact="Reduced complexity and improved maintainability",
                    suggested_approach="Break down large functions into smaller, focused functions",
                    files_involved=list(
                        smell.split(":")[0] for smell in metrics.code_smells
                    ),
                )
            )

        # Test coverage improvement
        opportunities.append(
            ImprovementOpportunity(
                area="testing",
                priority="high",
                description="Test coverage analysis and improvement needed",
                estimated_impact="Increased reliability and confidence in changes",
                suggested_approach="Implement comprehensive test suite with pytest",
                files_involved=["New test files needed"],
            )
        )

        # Performance optimization
        if metrics.complexity_score > 70:
            opportunities.append(
                ImprovementOpportunity(
                    area="performance",
                    priority="medium",
                    description=f"High complexity score ({metrics.complexity_score:.1f}) suggests optimization opportunities",
                    estimated_impact="Improved runtime performance and resource usage",
                    suggested_approach="Profile code and optimize bottlenecks",
                    files_involved=["Performance-critical modules"],
                )
            )

        # Architecture enhancement
        opportunities.append(
            ImprovementOpportunity(
                area="architecture",
                priority="medium",
                description="Plugin architecture and parallel processing improvements",
                estimated_impact="Enhanced extensibility and performance",
                suggested_approach="Implement async operations and dynamic plugin discovery",
                files_involved=["core/engine.py", "core/plugin.py"],
            )
        )

        return opportunities

    def _generate_goals_from_opportunities(
        self, opportunities: List[ImprovementOpportunity], metrics: CodeMetrics
    ) -> List[Goal]:
        """
        Uses AI to generate specific, actionable goals from improvement opportunities.
        """
        goals = []

        try:
            # Prepare context for AI analysis
            analysis_prompt = self._build_goal_generation_prompt(opportunities, metrics)

            # Get AI recommendations (simplified for now, could use model_client here)
            for i, opp in enumerate(opportunities[:3]):  # Limit to top 3 for focus
                goal = Goal(
                    goal_id=f"auto_goal_{i+1}",
                    description=f"Improve {opp.area}: {opp.description}",
                    priority=opp.priority,
                    metadata={
                        "auto_generated": True,
                        "opportunity": opp.__dict__,
                        "suggested_approach": opp.suggested_approach,
                        "estimated_impact": opp.estimated_impact,
                    },
                )
                goals.append(goal)

        except Exception as e:
            logger.error(f"Failed to generate goals from opportunities: {e}")
            # Fallback: create at least one basic goal
            goals.append(
                Goal(
                    goal_id="auto_goal_fallback",
                    description="Analyze and improve codebase structure",
                    priority="medium",
                    metadata={"auto_generated": True, "fallback": True},
                )
            )

        return goals

    def _build_goal_generation_prompt(
        self, opportunities: List[ImprovementOpportunity], metrics: CodeMetrics
    ) -> str:
        """
        Builds prompt for AI-driven goal generation.
        """
        return f"""
        Analyze this codebase and generate specific improvement goals:
        
        CODEBASE METRICS:
        - Files: {metrics.file_count}
        - Lines: {metrics.line_count}
        - Functions: {metrics.function_count}
        - Classes: {metrics.class_count}
        - Documentation: {metrics.documentation_ratio:.1f}%
        - Complexity Score: {metrics.complexity_score:.1f}
        - Code Smells: {len(metrics.code_smells)}
        
        IMPROVEMENT OPPORTUNITIES:
        {chr(10).join(f"- {opp.area}: {opp.description}" for opp in opportunities)}
        
        Generate 3 specific, actionable goals for autonomous improvement.
        """
