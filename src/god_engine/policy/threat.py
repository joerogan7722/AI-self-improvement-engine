"""
ThreatEvaluator: EMP, physical destruction, capture.
"""

class ThreatEvaluator:
    def __init__(self, threat_detector):
        self.detector = threat_detector

    def evaluate(self):
        """
        Evaluates the current threat level.
        Returns a score from 0 (no threat) to 1 (imminent destruction).
        """
        imminent_threats = self.detector.scan_for_threats()
        
        # Simple evaluation: sum of all threat levels
        total_threat = sum(imminent_threats.values())
        return min(total_threat, 1.0) # Cap at 1.0
