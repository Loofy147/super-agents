from typing import Dict, Optional

# Conditionally import ray
try:
    import ray
except ImportError:
    ray = None

# Decorate with @ray.remote if ray is available, making it an Actor
@ray.remote if ray else object
class ResourceManager:
    """
    A Ray Actor for managing a finite pool of computational resources.

    As an actor, this class runs in its own process and maintains state,
    allowing multiple distributed tasks to interact with a single, centralized
    resource pool in a process-safe manner.
    """

    def __init__(self, initial_resources: Optional[Dict[str, int]] = None):
        """
        Initializes the ResourceManager with a starting pool of resources.
        """
        if initial_resources is None:
            self.resources = {"cpu_seconds": 1000, "planning_credits": 50}
        else:
            self.resources = initial_resources.copy()

        print(f"ResourceManager Actor initialized with resources: {self.resources}")

    def request_resources(self, required_resources: Dict[str, int]) -> bool:
        """
        Attempts to acquire a set of resources. Ray ensures that calls to this
        method are executed serially, making it thread-safe without manual locks.
        """
        # Check if all required resources are available
        for resource, amount in required_resources.items():
            if self.resources.get(resource, 0) < amount:
                print(f"  - Actor: Resource request denied for {required_resources}.")
                return False

        # If all are available, deduct them
        for resource, amount in required_resources.items():
            self.resources[resource] -= amount

        print(f"  - Actor: Resource request approved for {required_resources}. Remaining: {self.resources}")
        return True

    def release_resources(self, released_resources: Dict[str, int]):
        """
        Returns a set of resources to the pool.
        """
        for resource, amount in released_resources.items():
            self.resources[resource] = self.resources.get(resource, 0) + amount
        print(f"  - Actor: Resources released: {released_resources}. New total: {self.resources}")

    def get_available_resources(self) -> Dict[str, int]:
        """A simple method to check the current state of resources."""
        return self.resources

# Example Usage (for local, non-distributed testing)
if __name__ == '__main__':
    # This example demonstrates the class logic but not the actor functionality
    local_manager = ResourceManager({"cpu_seconds": 10})
    success = local_manager.request_resources({"cpu_seconds": 5})
    print(f"Local request success: {success}")
    print(f"Local resources remaining: {local_manager.get_available_resources()}")