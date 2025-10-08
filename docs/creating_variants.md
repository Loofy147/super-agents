# Creating and Registering New Agent Variants

This guide explains how to create a new agent variant and register it with the `meta-orchestrator` system so it can be used in experiments.

## 1. Understand the `AgentVariant` Base Class

All agent variants must inherit from the `AgentVariant` abstract base class, which is defined in `meta_orchestrator/core/base_variant.py`. This class enforces a standard interface for all agents.

The key requirement is to implement the `run` method:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class AgentVariant(ABC):
    @abstractmethod
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the agent's logic for a single trial.
        """
        pass
```

- **`context`**: A dictionary that provides the agent with any external services or data it needs. For example, the `caching_agent` receives the `interpreter` instance through this context.
- **Return Value**: The `run` method must return a dictionary containing the performance metrics for that trial. The standard metrics are:
    - `success`: A float or int (typically 1 for success, 0 for failure).
    - `cost`: A float representing the monetary or computational cost of the run.
    - `autonomy`: A float between 0 and 1 indicating the agent's level of autonomy.

## 2. Create Your Variant File

Agent variants are typically located in the `meta_orchestrator/experiment_hub/variants/` directory. You can create a new Python file here for your new agent (e.g., `my_new_agent.py`).

## 3. Implement Your Agent Class

Inside your new file, create a class that inherits from `AgentVariant` and implements the `run` method.

### Example: A Simple, Stateless Agent

Here is an example of a simple agent that simulates a quick, low-cost operation.

```python
# In meta_orchestrator/experiment_hub/variants/my_new_agent.py

import time
from typing import Dict, Any
from ...core.base_variant import AgentVariant
from ..registry import register

class MyQuickAgent(AgentVariant):
    """
    A new agent that performs a quick, simulated task.
    """
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # Simulate some work
        time.sleep(0.03)

        # Return the standard performance metrics
        return {
            "success": 1,
            "cost": 0.0015,
            "autonomy": 0.85
        }

# (See step 4 for registration)
```

## 4. Register Your Agent

To make your agent discoverable by the experiment hub, you must register it using the `@register` decorator from `meta_orchestrator.experiment_hub.registry`.

You need to:
1. Import the `register` function.
2. Create an *instance* of your agent class.
3. Call `register()` with a unique name for your agent and pass the instance to it.

Continuing the example from above:

```python
# ... (after the class definition in the same file)

# Register an instance of the class with a unique name.
# The system can now refer to this agent as "my_quick_agent".
register("my_quick_agent")(MyQuickAgent())
```
The `__call__` method in the `AgentVariant` base class allows the instance to be treated like a function, which is what the registry expects.

## 5. Add Your Variant to the `__init__.py`

To ensure your new agent file is imported and registered when the system starts, you need to add it to the `meta_orchestrator/experiment_hub/variants/__init__.py` file.

```python
# In meta_orchestrator/experiment_hub/variants/__init__.py

# This file ensures that all variant modules are imported,
# which triggers their registration.

from . import in_memory
from . import caching_agent
from . import my_new_agent  # <--- Add this line
```

## 6. Add Your Variant to `config.yaml`

Finally, to include your new agent in an experiment, add its registered name (`"my_quick_agent"`) to the list of variants in your `config.yaml` file.

```yaml
# In config.yaml

orchestrator:
  type: "standard"
  standard_settings:
    experiments:
      - name: "Test My New Agent"
        enabled: true
        variants:
          - "in_memory_probe"
          - "my_quick_agent"  # <--- Add your agent here
        trials_per_variant: 50
```

You can now run the experiment hub, and your new agent will be included in the test run!