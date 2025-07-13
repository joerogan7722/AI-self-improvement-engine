"""
System Monitor for the God Engine.

This module is responsible for tracking key system metrics that can be used
to dynamically prioritize self-improvement goals.
"""
import time
from collections import defaultdict

class SystemMonitor:
    def __init__(self):
        self.error_counts = defaultdict(int)
        self.function_timings = defaultdict(list)

    def log_error(self, module_name):
        """Logs an error for a specific module."""
        self.error_counts[module_name] += 1
        print(f"SystemMonitor: Logged error for {module_name}. Total errors: {self.error_counts[module_name]}")

    def record_function_timing(self, function_name, duration):
        """Records the execution time for a specific function."""
        self.function_timings[function_name].append(duration)

    def get_error_rates(self):
        """Returns the current error counts for all modules."""
        return self.error_counts

    def get_performance_bottlenecks(self, top_n=5):
        """
        Analyzes function timings to identify the top N performance bottlenecks.
        Returns a list of (function_name, average_duration) tuples.
        """
        avg_timings = {}
        for func, timings in self.function_timings.items():
            if timings:
                avg_timings[func] = sum(timings) / len(timings)
        
        # Sort by average duration in descending order
        sorted_bottlenecks = sorted(avg_timings.items(), key=lambda item: item[1], reverse=True)
        
        return sorted_bottlenecks[:top_n]

    def time_function(self, func):
        """A decorator to easily time a function's execution."""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            self.record_function_timing(func.__name__, duration)
            print(f"SystemMonitor: Recorded execution of {func.__name__} took {duration:.4f} seconds.")
            return result
        return wrapper
