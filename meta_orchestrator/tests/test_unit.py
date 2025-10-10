import unittest
import time

import ray
from meta_orchestrator.core.resource_manager import ResourceManager
# Import the components to be tested using absolute paths
from meta_orchestrator.core.interpreter import Interpreter
from meta_orchestrator.experiment_hub.scoring import calculate_score
from meta_orchestrator.experiment_hub.variants.caching_agent import CachingAgent

class TestMetaOrchestrator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Initialize Ray once for all tests in this class
        if not ray.is_initialized():
            ray.init(logging_level="ERROR")

    @classmethod
    def tearDownClass(cls):
        # Shutdown Ray after all tests are done
        if ray.is_initialized():
            ray.shutdown()

    def test_resource_manager_prevents_negative_request(self):
        """
        Tests that the ResourceManager actor correctly rejects requests for
        negative resource amounts.
        """
        print("\nRunning test: test_resource_manager_prevents_negative_request")
        initial_resources = {"credits": 100}

        # Instantiate the ResourceManager as a Ray actor
        manager_actor = ResourceManager.remote(initial_resources)

        # Attempt to exploit the bug by requesting a negative amount
        exploit_request = {"credits": -50}

        # Call the actor method and get the result
        request_approved_future = manager_actor.request_resources.remote(exploit_request)
        request_approved = ray.get(request_approved_future)

        # 1. Assert that the malicious request was denied
        self.assertFalse(request_approved, "The request for negative resources should be denied.")

        # 2. Assert that the resource pool was not altered
        final_resources_future = manager_actor.get_available_resources.remote()
        final_resources = ray.get(final_resources_future)

        self.assertEqual(initial_resources["credits"], final_resources.get("credits", 0),
                         "The resource pool should not change after a denied negative request.")

    def test_calculate_score(self):
        """Tests the scoring function with a known trial result."""
        print("\nRunning test: test_calculate_score")
        trial = {
            "success": 1,
            "cost": 0.01,
            "autonomy": 0.8,
            "latency_internal_s": 0.1
        }
        # The scoring function now requires weights
        weights = {
            "autonomy": 0.4,
            "success": 0.35,
            "cost": -0.15,
            "latency": -0.1
        }
        # Expected score = (0.4 * 0.8) + (0.35 * 1) + (-0.15 * 0.01) + (-0.1 * 0.1)
        # = 0.32 + 0.35 - 0.0015 - 0.01 = 0.6585
        expected_score = 0.6585
        actual_score = calculate_score(trial, weights)
        self.assertAlmostEqual(expected_score, actual_score, places=4)

    def test_interpreter_caching(self):
        """Tests the basic cache functionality of the interpreter."""
        print("\nRunning test: test_interpreter_caching")
        interpreter = Interpreter()
        self.assertFalse(interpreter.cache_has("test_key"))

        interpreter.cache_put("test_key", "test_value")
        self.assertTrue(interpreter.cache_has("test_key"))
        self.assertEqual(interpreter.cache_get("test_key"), "test_value")

    def test_caching_agent_logic(self):
        """Tests the caching agent's behavior on cache hits and misses."""
        print("\nRunning test: test_caching_agent_logic")
        interpreter = Interpreter()
        # Instantiate the agent class to test it
        caching_agent = CachingAgent()
        task_id = "unique_task_for_testing"
        context = {"interpreter": interpreter, "task_id": task_id}

        # --- First run (cache miss) ---
        print("  - Testing cache miss...")
        miss_result = caching_agent(context)  # Use the instance
        self.assertEqual(miss_result["success"], 1)
        self.assertFalse(miss_result["was_cached"])
        self.assertGreater(miss_result["cost"], 0.001)  # Should have the higher cost

        # --- Second run (cache hit) ---
        print("  - Testing cache hit...")
        hit_result = caching_agent(context)  # Use the instance
        self.assertEqual(hit_result["success"], 1)
        self.assertTrue(hit_result["was_cached"])
        self.assertLess(hit_result["cost"], 0.001)  # Should have the lower cost

        # Verify the result payload is consistent
        self.assertEqual(miss_result["result"], hit_result["result"])

if __name__ == '__main__':
    # To run this test directly, you need to be in the project root
    # and run as a module: python -m meta_orchestrator.tests.test_unit
    unittest.main()