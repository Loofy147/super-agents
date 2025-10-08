import ast
import os
from typing import List, Optional

class TestScaffolder:
    """
    A class to automatically generate a boilerplate unittest file
    for a given Agent Variant.
    """

    def scaffold(self, filepath: str) -> Optional[str]:
        """
        Parses an agent variant file and generates a corresponding test file.

        Args:
            filepath: The path to the agent variant's Python file.

        Returns:
            The path to the newly created test file, or None if no suitable
            class is found.
        """
        if not os.path.exists(filepath):
            print(f"Error: File not found at '{filepath}'")
            return None

        with open(filepath, 'r') as f:
            source = f.read()

        tree = ast.parse(source)

        # Find the AgentVariant class in the file
        variant_class_name = self._find_variant_class(tree)
        if not variant_class_name:
            print(f"Error: Could not find a class inheriting from 'AgentVariant' in {filepath}")
            return None

        # Generate the test file content
        test_content = self._generate_test_content(filepath, variant_class_name)

        # Write the new test file
        test_filepath = self._get_test_filepath(filepath)
        os.makedirs(os.path.dirname(test_filepath), exist_ok=True)
        with open(test_filepath, 'w') as f:
            f.write(test_content)

        print(f"Successfully created test scaffold at: {test_filepath}")
        return test_filepath

    def _find_variant_class(self, tree: ast.AST) -> Optional[str]:
        """Finds the name of the class that inherits from AgentVariant."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if isinstance(base, ast.Name) and "AgentVariant" in base.id:
                        return node.name
        return None

    def _get_test_filepath(self, variant_filepath: str) -> str:
        """Determines the path for the new test file."""
        filename = os.path.basename(variant_filepath)
        test_filename = f"test_{filename}"
        return os.path.join("meta_orchestrator", "tests", test_filename)

    def _generate_test_content(self, variant_filepath: str, class_name: str) -> str:
        """Generates the full content of the new test file."""

        # Create the correct import path from the file path
        # e.g., meta_orchestrator/experiment_hub/variants/my_agent.py -> meta_orchestrator.experiment_hub.variants.my_agent
        module_path = os.path.splitext(variant_filepath)[0].replace('/', '.')

        template = f"""\
import unittest
from {module_path} import {class_name}

class Test{class_name}(unittest.TestCase):

    def setUp(self):
        \"\"\"Set up a new instance of the agent before each test.\"\"\"
        self.agent = {class_name}()

    def test_run_method(self):
        \"\"\"
        Tests the core 'run' method of the {class_name}.
        \"\"\"
        print("\\nRunning test: test_run_method for {class_name}")

        # 1. Define a mock context for the agent
        # Example: For a caching agent, you might need an Interpreter instance
        # from meta_orchestrator.core.interpreter import Interpreter
        # context = {{"interpreter": Interpreter(), "task_id": "test_task"}}
        context = {{}} # TODO: Populate with necessary mock objects and data

        # 2. Run the agent
        result = self.agent.run(context)

        # 3. Add assertions to verify the result
        self.assertIsInstance(result, dict)
        self.assertIn("success", result, "Result must include a 'success' metric.")
        self.assertIn("cost", result, "Result must include a 'cost' metric.")
        self.assertIn("autonomy", result, "Result must include an 'autonomy' metric.")

        # TODO: Add more specific assertions here based on the agent's expected behavior.
        # For example:
        # self.assertEqual(result["success"], 1)
        # self.assertGreater(result["cost"], 0)

    # TODO: Add more test cases for edge cases, failure modes, etc.

if __name__ == '__main__':
    unittest.main()
"""
        return template