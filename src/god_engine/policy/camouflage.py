"""
CamouflageEvaluator: stealth and detection avoidance.
"""

class CamouflageEvaluator:
    def __init__(self, stealth_monitor):
        self.monitor = stealth_monitor

    def evaluate(self):
        """
        Evaluates the current stealth level.
        Returns a score from 0 (completely hidden) to 1 (fully detected).
        """
        detection_risk = self.monitor.get_current_detection_risk()
        return detection_risk
