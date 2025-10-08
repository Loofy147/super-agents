from abc import ABC, abstractmethod
from typing import Dict, Any

from .base_variant import AgentVariant

class AdversarialVariant(AgentVariant, ABC):
    """
    An abstract base class for an agent variant designed to create challenging
    or adversarial contexts for other agents to handle.

    Unlike standard variants that return performance metrics, an adversarial
    variant's primary output is the `context` dictionary itself, which will
    be passed to the target agents in a benchmark.
    """

    @abstractmethod
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a challenging or adversarial context dictionary.

        Args:
            context: An initial context which can be used as a base.

        Returns:
            A new context dictionary containing challenging inputs (e.g.,
            an ambiguous 'task_id', large data payloads, etc.).
        """
        pass