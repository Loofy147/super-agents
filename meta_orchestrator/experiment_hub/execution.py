import time
import uuid
from typing import Dict

# Conditionally import ray to allow the system to function without it
try:
    import ray
except ImportError:
    ray = None

from .registry import REGISTRY

# This will be set by the hub to determine the execution strategy
EXECUTION_BACKEND = "local"

def configure_execution_backend(backend_type: str):
    """Sets the global execution backend for all trial runs."""
    global EXECUTION_BACKEND
    if backend_type not in ["local", "ray"]:
        raise ValueError(f"Unsupported backend type: {backend_type}")
    if backend_type == "ray" and not ray:
        raise ImportError("Cannot configure Ray backend, 'ray' is not installed.")
    EXECUTION_BACKEND = backend_type

def _run_trial_local(variant, context: Dict) -> Dict:
    """The core logic for running a single trial, executed locally."""
    if not callable(variant):
        if variant not in REGISTRY:
            raise ValueError(f"Variant '{variant}' not found in registry.")
        variant_callable = REGISTRY[variant]
    else:
        variant_callable = variant

    start_time = time.monotonic()
    result = variant_callable(context)
    end_time = time.monotonic()

    # Get the variant name, whether it's a string or an object
    variant_name = variant if isinstance(variant, str) else variant.__class__.__name__

    result.update({
        "variant": variant_name,
        "trace_id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "latency_internal_s": end_time - start_time
    })
    return result

# Define the remote version of the function if ray is installed
if ray:
    @ray.remote
    def run_trial_remote(variant, context: Dict) -> Dict:
        """The Ray remote version of the trial execution function."""
        # This function runs on a remote worker, so it needs to re-import REGISTRY
        # or have it passed in. For simplicity, we assume it's available if the
        # code is shipped correctly.
        return _run_trial_local(variant, context)

# The main run_trial function is now a dispatcher
def run_trial(variant, context: Dict) -> Dict:
    """
    Dispatcher function for running a single trial. It calls the appropriate
    local or remote execution function based on the configured backend.
    """
    if EXECUTION_BACKEND == "ray":
        return ray.get(run_trial_remote.remote(variant, context))
    else:
        return _run_trial_local(variant, context)