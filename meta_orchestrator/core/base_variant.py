from abc import ABC, abstractmethod
from typing import Dict, Any

class AgentVariant(ABC):
    """
    An abstract base class for an agent variant.

    This class defines the standard interface that all agent implementations
    must adhere to. It ensures that each variant is a callable object that
    can be executed by the orchestration engine.
    """

    @abstractmethod
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the agent's logic for a single trial.

        Args:
            context: A dictionary containing the input data or services
                     required by the agent for this trial (e.g., interpreter,
                     task_id).

        Returns:
            A dictionary containing the results of the trial, which must
            include metrics like 'success', 'cost', and 'autonomy'.
        """
        pass

    def __call__(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Allows the agent instance to be called directly as a function.
        This makes it compatible with the existing registry system.
        """
        return self.run(context)