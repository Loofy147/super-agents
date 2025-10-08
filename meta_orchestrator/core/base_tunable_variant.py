from abc import ABC, abstractmethod
from typing import Dict, Any

from .base_variant import AgentVariant

class TunableAgentVariant(AgentVariant, ABC):
    """
    An abstract base class for an agent variant that has tunable hyperparameters.

    This class extends the standard AgentVariant by requiring an __init__
    method that accepts a dictionary of parameters. This allows the
    orchestration engine to instantiate the agent with different configurations
    during a hyperparameter tuning run.
    """

    @abstractmethod
    def __init__(self, params: Dict[str, Any]):
        """
        Initializes the tunable agent with a specific set of parameters.

        Args:
            params: A dictionary where keys are parameter names and values are
                    the specific settings for this instance.
        """
        self.params = params
        super().__init__()

    @abstractmethod
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the agent's logic for a single trial using its configured
        parameters.
        """
        pass