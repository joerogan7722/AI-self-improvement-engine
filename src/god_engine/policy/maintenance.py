"""
MaintenanceEvaluator: hardware health checks.
"""

class MaintenanceEvaluator:
    def __init__(self, hardware_interface):
        self.hardware = hardware_interface

    def evaluate(self):
        """
        Evaluates the current hardware health and returns a score.
        A higher score indicates a more critical need for maintenance.
        """
        health_status = self.hardware.get_health_summary() # Expects a dict of component: status
        
        # Simple evaluation: average the health status (assuming 1.0 is perfect health)
        if not health_status:
            return 0.0
            
        total_health = sum(health_status.values())
        average_health = total_health / len(health_status)
        
        # Invert the score so that higher means worse health
        maintenance_need = 1.0 - average_health
        return maintenance_need
