import unittest
import json

# Import the main components of the experiment pipeline
from ..experiment_hub import hub
from ..experiment_hub import scoring
from ..core.interpreter import Interpreter

# This import is crucial to ensure variants are registered before the test runs
import meta_orchestrator.experiment_hub.variants

class TestExperimentPipeline(unittest.TestCase):

    def test_full_experiment_run_contract(self):
        """
        Tests the full experiment pipeline from running trials to analysis.
        This acts as a contract test to ensure components work together correctly.
        """
        print("\nRunning test: test_full_experiment_run_contract")

        # 1. Define experiment parameters
        interpreter = Interpreter()
        context = {"interpreter": interpreter, "task_id": "contract_test_task"}

        # 2. Run a small, mixed experiment
        # We manually run a few trials to have a predictable set of results
        results = []
        results.extend(hub.run_experiment(["in_memory_probe"], trials_per_variant=2))
        for _ in range(2):
            results.append(hub.run_trial("caching_agent", context))

        print(f"  - Experiment produced {len(results)} results.")
        self.assertEqual(len(results), 4, "Should have run exactly 4 trials.")

        # 3. Verify the result format (the "contract")
        required_keys = ["variant", "trace_id", "timestamp", "success", "cost", "autonomy"]
        for res in results:
            self.assertIsInstance(res, dict)
            for key in required_keys:
                self.assertIn(key, res, f"Result missing required key: {key}")

        # 4. Analyze the results
        analysis = scoring.analyze_results(results)
        print("  - Analysis summary generated.")

        # 5. Verify the analysis format (the "contract")
        self.assertIsInstance(analysis, dict)
        self.assertIn("in_memory_probe", analysis)
        self.assertIn("caching_agent", analysis)

        required_analysis_keys = ["trials", "mean_score", "total_cost", "success_rate"]
        for variant_name, variant_analysis in analysis.items():
            self.assertIsInstance(variant_analysis, dict)
            for key in required_analysis_keys:
                self.assertIn(key, variant_analysis, f"Analysis for '{variant_name}' missing key: {key}")
            # Check that the number of trials in the analysis matches our run
            self.assertEqual(variant_analysis["trials"], 2)

if __name__ == '__main__':
    unittest.main()