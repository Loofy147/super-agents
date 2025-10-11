import time
from typing import Dict, Any, List

# Conditionally import ray
try:
    import ray
except ImportError:
    ray = None

from meta_orchestrator.core.base_variant import AgentVariant
from meta_orchestrator.core.resource_manager import ResourceManager
from meta_orchestrator.experiment_hub.registry import register

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
        Orchestrates collaboration, correctly handling both local ResourceManager
        instances and remote Ray Actor handles.
        """
        resource_manager = context.get("resource_manager")
        if resource_manager is None:
            raise ValueError("Context must include a 'resource_manager'.")

        is_ray_actor = ray and isinstance(resource_manager, ray.actor.ActorHandle)

        required_resources = {"cpu_seconds": 2, "planning_credits": 1}

        # 1. Request resources, handling local vs. remote object
        if is_ray_actor:
            # Asynchronous call to the actor, then block for the result
            was_approved = ray.get(resource_manager.request_resources.remote(required_resources))
        else:
            was_approved = resource_manager.request_resources(required_resources)

        if not was_approved:
            return {"success": 0, "cost": 0.0, "autonomy": 0.98, "failure_reason": "RESOURCE_DENIED"}

        try:
            # 2. Proceed with agent logic
            task_description = context.get("task_id", "default_task")
            plan = self._planner_agent(task_description)
            execution_success = self._executor_agent(plan)

            return {
                "success": 1 if execution_success else 0,
                "cost": 0.015,
                "autonomy": 0.98,
                "result_details": {"plan_steps": len(plan)}
            }
        finally:
            # 3. Always release resources
            if is_ray_actor:
                resource_manager.release_resources.remote(required_resources)
            else:
                resource_manager.release_resources(required_resources)

# Register the new collaborative agent variant
register("collaborative_agent_team")(CollaborativeAgentTeam())