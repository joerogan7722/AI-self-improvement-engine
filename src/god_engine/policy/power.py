"""
PowerEvaluator: battery/fuel management.
"""

class PowerEvaluator:
    def __init__(self, resource_manager):
        self.resource_manager = resource_manager

    def evaluate(self):
        """
        Evaluates the current power state and returns a score.
        A higher score indicates a more critical need for power.
        """
        energy_level = self.resource_manager.get_resource_level("energy")
        fuel_level = self.resource_manager.get_resource_level("fuel")

        # Simple evaluation: invert the levels and average them.
        power_need = (1 - energy_level + 1 - fuel_level) / 2
        return power_need
