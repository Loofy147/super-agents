import time
from ..registry import register

@register("in_memory_probe")
def in_memory_probe(ctx: dict) -> dict:
    """A simple, fast, in-memory agent simulation."""
    time.sleep(0.02)  # Simulate work
    return {
        "success": 1,
        "cost": 0.001,
        "autonomy": 0.8
    }

@register("slower_reliable_probe")
def slower_reliable_probe(ctx: dict) -> dict:
    """A slightly slower but more autonomous agent simulation."""
    time.sleep(0.1)  # Simulate more complex work
    return {
        "success": 1,
        "cost": 0.005,
        "autonomy": 0.95
    }