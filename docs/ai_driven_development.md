# AI-Driven Development & Self-Improvement Roadmap

This document outlines the vision and technical roadmap for incorporating AI-driven development capabilities into the `meta-orchestrator`. These features focus on using AI, particularly Large Language Models (LLMs), to assist in the development, maintenance, and testing of the system's own codebase, creating a powerful meta-level feedback loop.

---

## Feature 1: LLM-Assisted Refactoring & Modernization

**Concept:** Evolve the existing rule-based `CodeModernizer` into a far more powerful and flexible tool by integrating a Large Language Model (LLM). Instead of being limited to predefined rules, the system will be able to perform complex, context-aware refactoring based on high-level natural language prompts.

**Objective:** To create a true "AI-powered developer's assistant" within the project, capable of tasks like improving performance, enhancing readability, adding error handling, or even translating code to a new paradigm, all driven by simple commands.

### Proposed Implementation

1.  **Introduce an `LLMModernizer` Class:**
    -   Create a new class, `code_modernizer.llm_modernizer.LLMModernizer`.
    -   This class will require an API key and configuration for an external LLM service (e.g., OpenAI, Anthropic, or a local model endpoint).
    -   Its core method, `suggest_refactor(filepath, prompt)`, will read the content of the file, combine it with the user's prompt into a request for the LLM, and parse the response.

2.  **Create a New CLI Command:**
    -   The feature will be exposed through a new `suggest-refactor` command in the CLI.
    -   The command will take the file path and a prompt as arguments.

    ```bash
    # Example usage
    python -m meta_orchestrator.cli suggest-refactor meta_orchestrator/experiment_hub/scoring.py \
      --prompt "Refactor this code to be more performant and add more robust error handling."
    ```

3.  **Displaying Results as a Diff:**
    -   A critical part of the user experience is presenting the LLM's suggestion not as a block of new code, but as a `diff`.
    -   The `LLMModernizer` will use Python's `difflib` module to generate a color-coded, unified diff between the original file content and the LLM's suggested replacement. This makes it easy for the developer to review, understand, and accept (or reject) the proposed changes.

### Actionable Next Steps

1.  **Add LLM Client Library:** Add a dependency like `openai` or `anthropic` to `pyproject.toml`.
2.  **Implement `LLMModernizer`:** Build the new class, including the logic for constructing the prompt, calling the LLM API, and handling the response.
3.  **Implement `difflib` Integration:** Write the code to generate and print a colorized diff to the console.
4.  **Update `cli.py`:** Add the new `suggest-refactor` command and its arguments, and wire it to the `LLMModernizer`.
5.  **Add Configuration for API Keys:** Update the project's configuration handling to securely manage LLM API keys (e.g., using environment variables and a `.env` file).

---

## Feature 2: Automated Unit Test Scaffolding

**Concept:** Accelerate the Test-Driven Development (TDD) cycle by automatically generating a boilerplate `unittest` file for any new agent variant. The system will inspect the agent's source code to create a ready-to-use test scaffold.

**Objective:** To lower the barrier to writing comprehensive tests for new variants, improve developer productivity, and enforce a consistent testing structure across the project. This ensures that every new agent starts with a solid testing foundation.

### Proposed Implementation

1.  **Create a `TestScaffolder` Class:**
    -   This new class, `testing.scaffolder.TestScaffolder`, will be the core of the feature.
    -   Its main method, `scaffold(filepath)`, will use Python's `ast` (Abstract Syntax Tree) module to parse the target agent's source file.

2.  **Code Analysis with AST:**
    -   The `scaffold` method will walk the AST to:
        -   Identify the class name of the `AgentVariant`.
        -   Find all public methods within that class.
        -   Inspect the arguments of each method (e.g., `run(self, context)`).

3.  **Test File Generation:**
    -   Based on the analysis, the `TestScaffolder` will generate a new file, e.g., `tests/test_my_new_agent.py`.
    -   This generated file will contain:
        -   All necessary imports (`unittest`, the agent class itself).
        -   A `unittest.TestCase` class definition.
        -   A placeholder test method for each public method found in the agent (e.g., `test_run_method(self)`).
        -   Inside each test method, boilerplate code to instantiate the agent and comments guiding the developer on where to add assertions (`# TODO: Add assertions here`).
        -   A basic `if __name__ == '__main__':` block.

4.  **Create a New CLI Command:**
    -   This feature will be exposed through a `scaffold-tests` command in the CLI.

    ```bash
    # Example usage
    python -m meta_orchestrator.cli scaffold-tests meta_orchestrator/experiment_hub/variants/my_new_agent.py
    ```
    -   The command will print the path to the newly created test file.

### Actionable Next Steps

1.  **Implement `TestScaffolder`:** Build the class and its `scaffold` method.
2.  **Implement AST Parsing Logic:** Write the code to walk the AST and extract the necessary class and method information.
3.  **Implement Test File Template:** Create a template for the test file and the logic to populate it with the extracted information.
4.  **Update `cli.py`:** Add the new `scaffold-tests` command and wire it to the `TestScaffolder`.