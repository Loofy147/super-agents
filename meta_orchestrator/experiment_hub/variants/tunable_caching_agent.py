import time
from typing import Dict, Any
from collections import OrderedDict

from ...core.base_variant import AgentVariant
from ...core.interpreter import Interpreter
from ..registry import register

# Note: We don't register this class directly, as the orchestrator
# will be responsible for instantiating it with specific parameters.
# However, we can register a default instance for standard runs if desired.

class TunableCachingAgent(AgentVariant):
    """
    A caching agent whose behavior is controlled by tunable hyperparameters.
    """

    def __init__(self, params: Dict[str, Any] = None):
        """
        Initializes the agent with specific parameters.

        Expected params:
        - cache_size (int): The maximum number of items to store in the cache.
        - strategy (str): The cache eviction strategy ('LRU' or 'FIFO').
        """
        super().__init__(params)
        self.cache_size = self.params.get("cache_size", 100)
        self.strategy = self.params.get("strategy", "LRU")

        # Use an OrderedDict to simulate a simple cache with eviction policies
        self._cache = OrderedDict()

    def _evict(self):
        """Evicts an item from the cache based on the chosen strategy."""
        if self.strategy == 'LRU':
            # For LRU, pop the first item (least recently used)
            self._cache.popitem(last=False)
        elif self.strategy == 'FIFO':
            # For FIFO, pop the first item inserted
            self._cache.popitem(last=False)

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs the caching logic, respecting the configured cache size and strategy.
        """
        interpreter = context.get("interpreter")
        task_id = context.get("task_id")

        if not isinstance(interpreter, Interpreter):
            raise TypeError("Context must include an 'interpreter' of type Interpreter.")
        if not task_id:
            raise ValueError("Context must include a 'task_id'.")

        # Cache check
        if task_id in self._cache:
            # For LRU, move the accessed item to the end to mark it as recently used
            if self.strategy == 'LRU':
                self._cache.move_to_end(task_id)

            return {
                "success": 1,
                "cost": 0.0001,
                "autonomy": 0.9,
                "was_cached": True,
                "result": self._cache[task_id]
            }
        else:
            # Cache miss
            time.sleep(0.15)
            result_payload = f"result_for_{task_id}"

            # Add to cache
            self._cache[task_id] = result_payload

            # Enforce cache size limit
            if len(self._cache) > self.cache_size:
                self._evict()

            return {
                "success": 1,
                "cost": 0.008,
                "autonomy": 0.9,
                "was_cached": False,
                "result": result_payload
            }

# We can register a default version for non-tuning experiments
default_params = {"cache_size": 100, "strategy": "LRU"}
register("tunable_caching_agent_default")(TunableCachingAgent(default_params))