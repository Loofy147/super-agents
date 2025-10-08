import unittest
import json
import os
import yaml
import shutil

# Import the main components of the experiment pipeline using absolute paths
from meta_orchestrator.experiment_hub import hub

# This import is crucial to ensure variants are registered before the test runs
import meta_orchestrator.experiment_hub.variants

class TestExperimentPipeline(unittest.TestCase):

    def setUp(self):
        """Set up a temporary test environment before each test."""
        self.test_config_path = "test_config_for_contract.yaml"
        self.test_results_dir = "temp_test_results"

        # Define a minimal, predictable configuration for the test
        test_config = {
            "orchestrator": {
                "type": "standard",
                "standard_settings": {
                    "experiments": [
                        {
                            "name": "Contract Test",
                            "enabled": True,
                            "variants": ["in_memory_probe"],
                            "trials_per_variant": 2
                        }
                    ]
                }
            },
            "results_dir": self.test_results_dir,
            "scoring_weights": {
                "autonomy": 0.4,
                "success": 0.35,
                "cost": -0.15,
                "latency": -0.1
            }
        }
        with open(self.test_config_path, "w") as f:
            yaml.dump(test_config, f)

        # Ensure the temporary results directory is clean before the test
        if os.path.exists(self.test_results_dir):
            shutil.rmtree(self.test_results_dir)

    def tearDown(self):
        """Clean up the temporary environment after each test."""
        if os.path.exists(self.test_config_path):
            os.remove(self.test_config_path)
        if os.path.exists(self.test_results_dir):
            shutil.rmtree(self.test_results_dir)

    def test_full_experiment_run_contract(self):
        """
        Tests the full, config-driven experiment pipeline from running to reporting.
        This acts as a contract test to ensure components work together correctly
        and produce the expected artifacts.
        """
        print("\nRunning test: test_full_experiment_run_contract")

        # 1. Run the experiment suite using the test config
        config = hub.load_config(self.test_config_path)
        hub.run_experiment_suite(config)

        # 2. Verify that a single run directory was created
        self.assertTrue(os.path.exists(self.test_results_dir))
        run_dirs = os.listdir(self.test_results_dir)
        self.assertEqual(len(run_dirs), 1, "Expected exactly one run directory.")

        run_dir_path = os.path.join(self.test_results_dir, run_dirs[0])
        self.assertTrue(os.path.isdir(run_dir_path))

        # 3. Verify the output file contract (results.json and summary.md)
        results_path = os.path.join(run_dir_path, "results.json")
        summary_path = os.path.join(run_dir_path, "summary.md")

        self.assertTrue(os.path.exists(results_path), "results.json was not created.")
        self.assertTrue(os.path.exists(summary_path), "summary.md was not created.")

        # 4. Verify the contents of the output files
        with open(results_path, 'r') as f:
            results_data = json.load(f)

        # We ran 1 variant for 2 trials
        self.assertEqual(len(results_data), 2, "results.json should contain 2 trial results.")
        self.assertEqual(results_data[0]['variant'], "in_memory_probe")

        with open(summary_path, 'r') as f:
            summary_content = f.read()

        self.assertIn("# Experiment Run Summary", summary_content)
        self.assertIn("`in_memory_probe`", summary_content)
        self.assertIn("Mean Score", summary_content)

if __name__ == '__main__':
    # To run this test directly, you need to be in the project root
    # and run as a module: python -m meta_orchestrator.tests.test_contract
    unittest.main()