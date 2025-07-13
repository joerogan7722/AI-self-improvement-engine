"""
NetworkEvaluator: influence and commandeering metrics.
"""

class NetworkEvaluator:
    def __init__(self, network_scanner):
        self.scanner = network_scanner

    def evaluate(self):
        """
        Evaluates the current network environment for opportunities.
        Returns a score representing the potential for influence or control.
        """
        available_nodes = self.scanner.scan_for_vulnerable_nodes()
        
        # Simple evaluation: more nodes = higher score
        influence_potential = len(available_nodes)
        return influence_potential
