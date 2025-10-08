import time
from typing import Dict, Any, List

from ...core.base_variant import AgentVariant
from ..registry import register

class CollaborativeAgentTeam(AgentVariant):
    """
    A variant that simulates a multi-agent team using a "divide and conquer"
    strategy. It consists of a Planner sub-agent and an Executor sub-agent.
    """

    def _planner_agent(self, task_description: str) -> List[str]:
        """Simulates a planner agent breaking down a task."""
        print("  - PlannerAgent: Analyzing task...")
        time.sleep(0.08)  # Simulate planning overhead
        # A more complex task results in a more detailed plan
        num_steps = 3 + len(task_description) % 3
        plan = [f"step_{i+1}" for i in range(num_steps)]
        print(f"  - PlannerAgent: Generated {len(plan)}-step plan.")
        return plan

    def _executor_agent(self, plan: List[str]) -> bool:
        """Simulates an executor agent carrying out a plan."""
        print(f"  - ExecutorAgent: Starting execution of {len(plan)} steps.")
        for step in plan:
            # Simulate work for each step
            time.sleep(0.04)
        print("  - ExecutorAgent: Execution complete.")
        return True

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrates the collaboration between the Planner and Executor agents.
        """
        task_description = context.get("task_id", "default_task")

        # 1. Planner runs first
        plan = self._planner_agent(task_description)

        # 2. Executor runs second
        execution_success = self._executor_agent(plan)

        # This agent has high autonomy because it manages an internal team.
        # Its cost is higher due to the overhead of two sub-agents.
        # Its success depends on the execution.
        return {
            "success": 1 if execution_success else 0,
            "cost": 0.015,  # Higher base cost for multi-agent coordination
            "autonomy": 0.98,
            "result_details": {
                "plan_steps": len(plan),
                "collaboration_successful": True,
            }
        }

# Register the new collaborative agent variant
register("collaborative_agent_team")(CollaborativeAgentTeam())