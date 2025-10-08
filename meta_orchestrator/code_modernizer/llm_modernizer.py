import os
import difflib
from openai import OpenAI

class LLMModernizer:
    """
    Uses an LLM to suggest refactorings and modernizations for Python code.
    """
    def __init__(self):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set. Please set it to use this feature.")
        self.client = OpenAI(api_key=api_key)

    def suggest_refactor(self, filepath: str, prompt: str) -> str:
        """
        Analyzes a Python file using an LLM and returns a diff of the suggestions.

        Args:
            filepath: The path to the Python file to analyze.
            prompt: The natural language prompt describing the desired refactoring.

        Returns:
            A string containing the diff of the suggested changes, or an
            error message if the operation failed.
        """
        print(f"Analyzing {filepath} with prompt: '{prompt}'...")
        try:
            with open(filepath, 'r') as f:
                original_code = f.read()

            system_prompt = """\
You are an expert Python software engineer specializing in clean, efficient, and modern code.
You will be given a Python source file and a prompt. Your task is to rewrite the entire file to incorporate the user's request.
ONLY return the complete, rewritten Python code. Do not include any explanations, apologies, or markdown formatting like ```python.
Your output must be pure, valid Python code that can be written directly back to the file."""

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Here is the file content of '{filepath}':\n\n{original_code}\n\nMy request is: {prompt}"}
                ]
            )

            refactored_code = response.choices[0].message.content

            if not refactored_code.strip():
                return "Error: LLM returned an empty response."

            # Generate and return a unified diff
            diff = difflib.unified_diff(
                original_code.splitlines(keepends=True),
                refactored_code.splitlines(keepends=True),
                fromfile=f"{filepath} (original)",
                tofile=f"{filepath} (refactored)"
            )
            return "".join(diff)

        except Exception as e:
            return f"An error occurred: {e}"

# Example Usage (for demonstration if run directly)
if __name__ == '__main__':
    # This example will not run without a valid OPENAI_API_KEY set
    if not os.environ.get("OPENAI_API_KEY"):
        print("Skipping LLMModernizer example: OPENAI_API_KEY is not set.")
    else:
        # Create a dummy file to analyze
        dummy_code = 'def old_style_func(name):\n    return "Hello, %s" % name\n'
        dummy_filepath = "dummy_llm_test_file.py"
        with open(dummy_filepath, "w") as f:
            f.write(dummy_code)

        modernizer = LLMModernizer()
        prompt = "Please refactor this to use f-strings and add type hints."
        suggestion_diff = modernizer.suggest_refactor(dummy_filepath, prompt)

        print("\n--- Suggested Changes (Diff) ---")
        print(suggestion_diff)

        os.remove(dummy_filepath)