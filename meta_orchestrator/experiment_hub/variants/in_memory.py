import time
from typing import Dict, Any
from ..registry import register
from ...core.base_variant import AgentVariant

class InMemoryProbe(AgentVariant):
    """A simple, fast, in-memory agent simulation."""
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        time.sleep(0.02)  # Simulate work
        return {
            "success": 1,
            "cost": 0.001,
            "autonomy": 0.8
        }

class SlowerReliableProbe(AgentVariant):
    """A slightly slower but more autonomous agent simulation."""
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        time.sleep(0.1)  # Simulate more complex work
        return {
            "success": 1,
            "cost": 0.005,
            "autonomy": 0.95
        }

# Register instances of the classes.
# The __call__ method in the base class makes them behave like functions.
register("in_memory_probe")(InMemoryProbe())
register("slower_reliable_probe")(SlowerReliableProbe())