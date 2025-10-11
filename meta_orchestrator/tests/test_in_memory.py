import unittest
from meta_orchestrator.experiment_hub.variants.in_memory import InMemoryProbe, SlowerReliableProbe

class TestInMemoryVariants(unittest.TestCase):

    def test_in_memory_probe(self) -> None:
        """
        Tests the specific return values of the InMemoryProbe variant.
        """
        print("\nRunning test: test_in_memory_probe")
        agent = InMemoryProbe()
        context = {}
        result = agent.run(context)

        # Verify the contract of the result dictionary
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        self.assertIn("cost", result)
        self.assertIn("autonomy", result)

        # Verify the specific values for this variant
        self.assertEqual(result["success"], 1)
        self.assertEqual(result["cost"], 0.001)
        self.assertEqual(result["autonomy"], 0.8)

    def test_slower_reliable_probe(self) -> None:
        """
        Tests the specific return values of the SlowerReliableProbe variant.
        """
        print("\nRunning test: test_slower_reliable_probe")
        agent = SlowerReliableProbe()
        context = {}
        result = agent.run(context)

        # Verify the contract of the result dictionary
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        self.assertIn("cost", result)
        self.assertIn("autonomy", result)

        # Verify the specific values for this variant
        self.assertEqual(result["success"], 1)
        self.assertEqual(result["cost"], 0.005)
        self.assertEqual(result["autonomy"], 0.95)

if __name__ == '__main__':
    unittest.main()