import time
import uuid
from typing import Dict

from .registry import REGISTRY

def run_trial(variant_name: str, context: Dict) -> Dict:
    """
    Runs a single trial for a given variant.

    Args:
        variant_name: The name of the variant to run.
        context: The context or input for the trial.

    Returns:
        A dictionary with the trial results.
    """
    if variant_name not in REGISTRY:
        raise ValueError(f"Variant '{variant_name}' not found in registry.")

    start_time = time.monotonic()
    # Execute the variant function from the registry
    result = REGISTRY[variant_name](context)
    end_time = time.monotonic()

    # Enrich the result with metadata
    result.update({
        "variant": variant_name,
        "trace_id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "latency_internal_s": end_time - start_time
    })
    return result