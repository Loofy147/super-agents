import ast
from typing import List, Dict, Any

class CodeModernizer:
    """
    A class to analyze Python source code and suggest modernizations.
    """
    def __init__(self):
        self.suggestions = []

    def analyze_and_suggest(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Analyzes a Python file and returns a list of modernization suggestions.

        Args:
            filepath: The path to the Python file to analyze.

        Returns:
            A list of dictionaries, where each dictionary represents a suggestion.
        """
        self.suggestions = []
        with open(filepath, 'r') as f:
            source = f.read()

        tree = ast.parse(source)
        self._check_for_fstrings(tree)
        self._check_for_type_hints(tree)

        print(f"Analysis complete for {filepath}. Found {len(self.suggestions)} suggestions.")
        return self.suggestions

    def _add_suggestion(self, line: int, suggestion_type: str, message: str):
        self.suggestions.append({
            "line": line,
            "type": suggestion_type,
            "message": message
        })

    def _check_for_fstrings(self, tree: ast.AST):
        """
        Walks the AST to find uses of .format() or % formatting that could be f-strings.
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'format':
                if isinstance(node.func.value, ast.Str):
                    self._add_suggestion(
                        node.lineno,
                        "F-String Suggestion",
                        "Consider replacing str.format() with an f-string for better readability."
                    )
            elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod) and isinstance(node.left, ast.Str):
                self._add_suggestion(
                    node.lineno,
                    "F-String Suggestion",
                    "Consider replacing %-style formatting with an f-string."
                )

    def _check_for_type_hints(self, tree: ast.AST):
        """
        Walks the AST to find function definitions that are missing type hints.
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for missing return type hint
                if not node.returns:
                    self._add_suggestion(
                        node.lineno,
                        "Type Hint Suggestion",
                        f"Consider adding a return type hint to the function '{node.name}'."
                    )

                # Check for missing arg type hints
                for arg in node.args.args:
                    if not arg.annotation and arg.arg != 'self':
                        self._add_suggestion(
                            arg.lineno,
                            "Type Hint Suggestion",
                            f"Consider adding a type hint to the argument '{arg.arg}' in function '{node.name}'."
                        )

# Example Usage
if __name__ == '__main__':
    # Create a dummy file to analyze
    dummy_code = """
import sys

def old_style_greeting(name):
    return "Hello, {}!".format(name)

def another_function(value, count):
    result = "The value is %s" % value
    return result

class MyClass:
    def method(self, arg1):
        pass
"""
    dummy_filepath = "dummy_test_file.py"
    with open(dummy_filepath, "w") as f:
        f.write(dummy_code)

    modernizer = CodeModernizer()
    suggestions = modernizer.analyze_and_suggest(dummy_filepath)

    import json
    print(json.dumps(suggestions, indent=2))

    import os
    os.remove(dummy_filepath)