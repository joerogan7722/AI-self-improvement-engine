# roles/self_review.py
from typing import Any, Dict
from ..engine import Role, Context
import importlib

class SelfReviewRole(Role):
    """
    Evaluates whether the proposed patch meets acceptance criteria using rule_engine logic,
    and optionally deeper analysis via review_analyzer.
    """
    def __init__(self, rule_config: Dict[str, Any] = None, analyzer_config: Dict[str, Any] = None):
        # Dynamically load the original RuleEngine from god_engine
        module = importlib.import_module('god_engine.rule_engine')
        RuleEngine = getattr(module, 'RuleEngine')
        # Initialize with the same config dict schema
        self.rule_engine = RuleEngine(rule_config or {})
        # Optionally load review_analyzer
        try:
            analyzer_mod = importlib.import_module('review_analyzer')
            self.analyzer = getattr(analyzer_mod, 'ReviewAnalyzer')(analyzer_config or {})
        except (ImportError, AttributeError):
            self.analyzer = None

    def run(self, context: Context) -> Context:
        # 1. Evaluate tests
        tests = context.test_results or {}
        # 2. Evaluate rules
        try:
            accepted = self.rule_engine.evaluate(
                goal=context.goal,
                todos=context.todos,
                test_results=tests
            )
        except Exception as e:
            # If rule evaluation fails, decline by default
            context.metadata.setdefault('errors', []).append(f"RuleEngine error: {e}")
            accepted = False

        context.accepted = bool(accepted)

        # 3. Optional deeper analysis
        if self.analyzer:
            try:
                analysis = self.analyzer.analyze_patch(
                    patch=context.patch,
                    tests=tests
                )
                context.metadata['analysis'] = analysis
            except Exception as e:
                context.metadata.setdefault('errors', []).append(f"Analyzer error: {e}")

        # 4. Set abort flag on rejection
        if not context.accepted:
            context.should_abort = True

        return context
