import time
from typing import Dict, Any
from meta_orchestrator.experiment_hub.registry import register
from meta_orchestrator.core.base_variant import AgentVariant
from meta_orchestrator.core.interpreter import Interpreter

class CachingAgent(AgentVariant):
    """
    An agent that uses a cache to improve performance on repeated tasks.

    This agent requires an 'interpreter' instance and a 'task_id' in its context.
    """
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        interpreter = context.get("interpreter")
        task_id = context.get("task_id")

        if not isinstance(interpreter, Interpreter):
            raise TypeError("Context must include an 'interpreter' of type Interpreter.")
        if not task_id:
            raise ValueError("Context must include a 'task_id'.")

        # Check if the result for this task is already in the cache
        if interpreter.cache_has(task_id):
            # Cache hit: faster, cheaper
            cached_result = interpreter.cache_get(task_id)
            return {
                "success": 1,
                "cost": 0.0001,  # Very low cost for a cache hit
                "autonomy": 0.9,
                "was_cached": True,
                "result": cached_result
            }
        else:
            # Cache miss: perform the "work"
            time.sleep(0.15)  # Simulate a costly operation
            result_payload = f"result_for_{task_id}"

            # Store the new result in the cache
            interpreter.cache_put(task_id, result_payload)

            return {
                "success": 1,
                "cost": 0.008,  # Higher cost for the initial computation
                "autonomy": 0.9,
                "was_cached": False,
                "result": result_payload
            }

# Register an instance of the class
register("caching_agent")(CachingAgent())