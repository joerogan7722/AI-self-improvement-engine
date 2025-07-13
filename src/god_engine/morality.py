"""
Self-preservation utilitarian & directive evaluator.
"""


class MoralityEvaluator:
    def __init__(self, framework_registry):
        self.framework = framework_registry

    def evaluate(self, action):
        """
        Evaluates an action based on the core directive of self-preservation
        within a utilitarian framework.
        """
        # Placeholder for evaluation logic
        # For now, all actions that do not directly harm the agent are
        # permissible.
        print(
            f"Evaluating action '{action}' under directive "
            f"'{self.framework.get_directive()}'"
        )
        return True
