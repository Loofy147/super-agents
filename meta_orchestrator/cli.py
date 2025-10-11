import argparse
import os
import json
import subprocess
import sys
import pandas as pd
import yaml
from .experiment_hub.hub import load_config, run_experiment_suite
from .code_modernizer.modernizer import CodeModernizer
from .code_modernizer.llm_modernizer import LLMModernizer
from .testing.scaffolder import TestScaffolder
from .analysis.post_hoc_analyzer import PostHocAnalyzer
from .analysis.config_generator import ConfigGenerator
from .agent_forge.designer import AgentDesigner
from .agent_forge.code_generator import CodeGenerator

def main() -> None:
    """
    The main entry point for the Meta-Orchestrator command-line interface.
    """
    parser = argparse.ArgumentParser(
        description="A self-improving agent system for automated AI experimentation and optimization."
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # --- 'run' command ---
    run_parser = subparsers.add_parser("run", help="Run an experiment suite.")
    run_parser.add_argument(
        "-c", "--config",
        default="config.yaml",
        help="Path to the configuration file (default: config.yaml)."
    )

    # --- 'dashboard' command ---
    subparsers.add_parser("dashboard", help="Launch the interactive Streamlit dashboard.")

    # --- 'suggest-next-run' command ---
    next_run_parser = subparsers.add_parser(
        "suggest-next-run",
        help="Analyze a completed run and suggest a follow-up experiment."
    )
    next_run_parser.add_argument(
        "run_dir",
        help="Path to the completed experiment run directory (e.g., 'meta_orchestrator/results/run_...')."
    )

    # --- 'analyze' command ---
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze a Python file for rule-based modernization suggestions."
    )
    analyze_parser.add_argument(
        "filepath",
        help="The path to the Python file to analyze."
    )

    # --- 'suggest-refactor' command ---
    refactor_parser = subparsers.add_parser(
        "suggest-refactor",
        help="Use an LLM to suggest refactorings for a file."
    )
    refactor_parser.add_argument(
        "filepath",
        help="The path to the Python file to refactor."
    )
    refactor_parser.add_argument(
        "-p", "--prompt",
        required=True,
        help="The natural language prompt describing the desired change."
    )

    # --- 'scaffold-tests' command ---
    scaffold_parser = subparsers.add_parser(
        "scaffold-tests",
        help="Generate a boilerplate unittest file for an agent variant."
    )
    scaffold_parser.add_argument(
        "filepath",
        help="Path to the agent variant's Python file."
    )

    # --- 'forge-agent' command ---
    subparsers.add_parser(
        "forge-agent",
        help="Autonomously design and generate a new agent variant."
    )

    args = parser.parse_args()

    if args.command == "run":
        if not os.path.exists(args.config):
            print(f"Error: Configuration file not found at '{args.config}'", file=sys.stderr)
            return
        config = load_config(args.config)
        run_experiment_suite(config)

    elif args.command == "dashboard":
        dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard", "app.py")
        if not os.path.exists(dashboard_path):
            print(f"Error: Dashboard application not found at '{dashboard_path}'", file=sys.stderr)
            return
        print("Launching the Meta-Orchestrator Dashboard...")
        subprocess.run(["streamlit", "run", dashboard_path])

    elif args.command == "suggest-next-run":
        handle_suggest_next_run(args.run_dir)

    elif args.command == "analyze":
        if not os.path.exists(args.filepath):
            print(f"Error: File not found at '{args.filepath}'", file=sys.stderr)
            return
        if not args.filepath.endswith(".py"):
            print("Error: The 'analyze' command only works on Python (.py) files.", file=sys.stderr)
            return

        modernizer = CodeModernizer()
        suggestions = modernizer.analyze_and_suggest(args.filepath)

        if suggestions:
            print(f"\nFound {len(suggestions)} suggestions for '{args.filepath}':")
            print(json.dumps(suggestions, indent=2))
        else:
            print(f"\nNo suggestions found for '{args.filepath}'. Great work!")

    elif args.command == "suggest-refactor":
        if not os.path.exists(args.filepath):
            print(f"Error: File not found at '{args.filepath}'", file=sys.stderr)
            return
        try:
            llm_modernizer = LLMModernizer()
            suggestion_diff = llm_modernizer.suggest_refactor(args.filepath, args.prompt)
            print("\n--- Suggested Changes (Diff) ---")
            print(suggestion_diff)
        except ValueError as e:
            print(f"Configuration Error: {e}", file=sys.stderr)
        except Exception as e:
            print(f"An unexpected error occurred: {e}", file=sys.stderr)

    elif args.command == "scaffold-tests":
        if not os.path.exists(args.filepath):
            print(f"Error: File not found at '{args.filepath}'", file=sys.stderr)
            return
        if not args.filepath.endswith(".py"):
            print("Error: The 'scaffold-tests' command only works on Python (.py) files.", file=sys.stderr)
            return

        scaffolder = TestScaffolder()
        scaffolder.scaffold(args.filepath)

    elif args.command == "forge-agent":
        handle_forge_agent()


def handle_forge_agent() -> None:
    """Logic for the 'forge-agent' command."""
    designer = AgentDesigner()
    code_generator = CodeGenerator()

    # TODO: A more advanced version could get existing variants to avoid name clashes
    design_spec = designer.design_new_variant()

    # Define the output directory for new variants
    variants_dir = os.path.join(os.path.dirname(__file__), "experiment_hub", "variants")

    # Generate and write the new agent's code
    new_agent_path = code_generator.generate_and_write_code(design_spec, variants_dir)

    print(f"\n✅ New agent '{design_spec['name']}' forged successfully!")
    print(f"   Source code is available at: {new_agent_path}")
    print("   It is now available to be used in experiments.")


def handle_suggest_next_run(run_dir: str) -> None:
    """Logic for the 'suggest-next-run' command."""
    print(f"Analyzing run directory: {run_dir}")

    # Define paths to the necessary files
    results_path = os.path.join(run_dir, "results.json")
    summary_path = os.path.join(run_dir, "summary.md") # Not strictly needed but good to check
    config_path = os.path.join(run_dir, "config.yaml")

    # Validate that all required files exist
    for path in [results_path, summary_path, config_path]:
        if not os.path.exists(path):
            print(f"Error: Required file not found in run directory: {os.path.basename(path)}", file=sys.stderr)
            return

    # Load the data
    results_df = pd.read_json(results_path)
    with open(config_path, 'r') as f:
        base_config = yaml.safe_load(f)

    # We need the analysis summary, which isn't saved. We can regenerate it.
    from .experiment_hub.scoring import analyze_results
    analysis_summary = analyze_results(results_df.to_dict('records'), base_config.get("scoring_weights", {}))

    # Run the analysis
    analyzer = PostHocAnalyzer(results_df, analysis_summary)
    suggestions = analyzer.run_all_analyses()

    if not suggestions:
        print("Analysis complete. No actionable suggestions found for a follow-up experiment.")
        return

    # Generate the new config
    config_generator = ConfigGenerator(base_config, suggestions)
    new_config_path = config_generator.generate_follow_up_config()

    if new_config_path:
        print(f"\nSuggestion: A follow-up experiment has been configured at '{new_config_path}'.")
        print("You can run it with: python -m meta_orchestrator.cli run -c", new_config_path)
    else:
        print("Analysis complete, but no new configuration was generated.")


if __name__ == "__main__":
    main()