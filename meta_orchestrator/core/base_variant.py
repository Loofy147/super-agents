from abc import ABC, abstractmethod
from typing import Dict, Any

class AgentVariant(ABC):
    """
    An abstract base class for an agent variant.

    This class defines the standard interface that all agent implementations
    must adhere to. It is designed to be flexible, supporting standard,
    tunable, and adversarial agents through its `__init__` and `run` methods.
    """

    def __init__(self, params: Dict[str, Any] = None):
        """
        Initializes the agent.

        For standard agents, this may do nothing. For tunable agents, this
        is where hyperparameters are accepted and configured.

        Args:
            params: An optional dictionary of parameters for configuration.
        """
        self.params = params if params is not None else {}

    @abstractmethod
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the agent's logic for a single trial.

        The behavior of this method can vary based on the agent's role:
        - For a standard agent, it runs a task and returns performance metrics.
        - For an adversarial agent, it should return a modified 'context'
          dictionary to be used as input for other agents.

        Args:
            context: A dictionary containing input data or services.

        Returns:
            A dictionary containing the results of the trial.
        """
        pass

    def __call__(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Allows the agent instance to be called directly as a function,
        making it compatible with the registry system.
        """
        return self.run(context)