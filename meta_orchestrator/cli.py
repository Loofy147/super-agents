import argparse
import os
import json
from .experiment_hub.hub import load_config, run_experiment_suite
from .code_modernizer.modernizer import CodeModernizer

def main():
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

    # --- 'analyze' command ---
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze a Python file for modernization suggestions."
    )
    analyze_parser.add_argument(
        "filepath",
        help="The path to the Python file to analyze."
    )

    args = parser.parse_args()

    if args.command == "run":
        if not os.path.exists(args.config):
            print(f"Error: Configuration file not found at '{args.config}'")
            return
        config = load_config(args.config)
        run_experiment_suite(config)

    elif args.command == "analyze":
        if not os.path.exists(args.filepath):
            print(f"Error: File not found at '{args.filepath}'")
            return
        if not args.filepath.endswith(".py"):
            print("Error: The 'analyze' command only works on Python (.py) files.")
            return

        modernizer = CodeModernizer()
        suggestions = modernizer.analyze_and_suggest(args.filepath)

        if suggestions:
            print(f"\nFound {len(suggestions)} suggestions for '{args.filepath}':")
            print(json.dumps(suggestions, indent=2))
        else:
            print(f"\nNo suggestions found for '{args.filepath}'. Great work!")


if __name__ == "__main__":
    main()