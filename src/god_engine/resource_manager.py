"""
Tracks energy, fuel, and materials; forecasts consumption.
"""
# TODO: integrate EM Shield protocol to hibernate in shielded mode under EMP risk

class ResourceManager:
    def __init__(self, config):
        self.resources = config.get("resource_schemas", {})
        self.levels = {name: 1.0 for name in self.resources.keys()} # Start at 100%

    def get_resource_level(self, resource_name: str) -> float:
        """Returns the current level of a resource (0.0 to 1.0)."""
        return self.levels.get(resource_name, 0.0)

    def consume_resource(self, resource_name: str, amount: float):
        """Consumes a given amount of a resource."""
        if resource_name in self.levels:
            self.levels[resource_name] = max(0.0, self.levels[resource_name] - amount)
            print(f"Consumed {amount} of {resource_name}. New level: {self.levels[resource_name]:.2f}")

    def forecast_consumption(self, activity: str, duration: int):
        """Forecasts resource consumption for a given activity."""
        # Placeholder for forecasting logic
        print(f"Forecasting consumption for '{activity}' over {duration} hours.")
        return {"energy": 0.1 * duration, "fuel": 0.05 * duration}

    def em_shield_protocol(self):
        """Hibernates in a shielded mode to protect against EMP."""
        print("EMERGENCY: EM Shield protocol activated. Hibernating.")
        # Placeholder for hibernation logic
