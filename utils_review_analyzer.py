# roles/self_review.py
from typing import Any, Dict
from ..engine import Role, Context
import importlib
from pathlib import Path

class SelfReviewRole(Role):
    """
    Evaluates whether the proposed patch meets acceptance criteria using rule_engine logic,
    and optionally deeper analysis via ReviewAnalyzer.
    """
    def __init__(self, rule_config: Dict[str, Any] = None, analyzer_config: Dict[str, Any] = None):
        # Load original RuleEngine from god_engine
        module = importlib.import_module('god_engine.rule_engine')
        RuleEngine = getattr(module, 'RuleEngine')
        self.rule_engine = RuleEngine(rule_config or {})

        # Load ReviewAnalyzer for deeper analysis
        analyzer_config = analyzer_config or {}
        log_dir = Path(analyzer_config.get('log_directory', './memory'))
        try:
            analyzer_mod = importlib.import_module('utils.review_analyzer')
            ReviewAnalyzer = getattr(analyzer_mod, 'ReviewAnalyzer')
            self.analyzer = ReviewAnalyzer(log_dir)
        except (ImportError, AttributeError):
            self.analyzer = None

    def run(self, context: Context) -> Context:
        # Evaluate using RuleEngine
        tests = context.test_results or {}
        try:
            accepted = self.rule_engine.evaluate(
                goal=context.goal,
                todos=context.todos,
                test_results=tests
            )
        except Exception as e:
            context.metadata.setdefault('errors', []).append(f"RuleEngine error: {e}")
            accepted = False
        context.accepted = bool(accepted)

        # Optional deeper analysis
        if self.analyzer:
            try:
                analysis = self.analyzer.analyze_patch(
                    patch=context.patch,
                    tests=tests
                )
                context.metadata['analysis'] = analysis
            except Exception as e:
                context.metadata.setdefault('errors', []).append(f"Analyzer error: {e}")

        # Abort if patch not accepted
        if not context.accepted:
            context.should_abort = True
        return context
