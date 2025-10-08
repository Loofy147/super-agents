import json
import yaml
import os
import uuid
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List

# Conditionally import ray
try:
    import ray
except ImportError:
    ray = None

from .registry import REGISTRY
from ..core.interpreter import Interpreter
from ..core.resource_manager import ResourceManager
from .scoring import analyze_results, generate_markdown_report
from ..orchestrators.unified_orchestrator import UnifiedOrchestrator
from .execution import run_trial, configure_execution_backend

# This import triggers the __init__.py in the variants package
import meta_orchestrator.experiment_hub.variants

def load_config(config_path: str) -> Dict:
    """Loads the experiment configuration from a YAML file."""
    print(f"Loading configuration from: {config_path}")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def run_experiment_suite(config: Dict):
    """
    Initializes the execution backend and runs the full experiment suite
    using the UnifiedOrchestrator.
    """
    backend_config = config.get("execution_backend", {})
    backend_type = backend_config.get("type", "local")

    if backend_type == "ray":
        if not ray:
            raise ImportError("Configuration specifies Ray backend, but 'ray' is not installed.")
        print("Initializing Ray for distributed execution...")
        ray.init(**backend_config.get("ray_settings", {}))

    try:
        configure_execution_backend(backend_type)
        print(f"Registered variants: {list(REGISTRY.keys())}")

        # Initialize core services that will be available to all agents
        interpreter_instance = Interpreter()

        # Conditionally create the ResourceManager as a Ray Actor or a local instance
        if backend_type == "ray":
            resource_manager_instance = ResourceManager.remote(config.get("resources"))
        else:
            resource_manager_instance = ResourceManager(config.get("resources"))

        base_context = {
            "interpreter": interpreter_instance,
            "resource_manager": resource_manager_instance,
        }

        # Instantiate the single, powerful orchestrator
        orchestrator = UnifiedOrchestrator(config, base_context)

        # Delegate the entire run and collect results
        all_results = list(orchestrator.run_suite())

        # --- Save, and Analyze ---
        if all_results:
            run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            scoring_weights = config.get("scoring_weights", {})
            analysis_summary = analyze_results(all_results, scoring_weights)
            results_df = pd.DataFrame(all_results)

            save_results(all_results, analysis_summary, config, run_timestamp, results_df)

            print("\n--- Combined Experiment Analysis Summary ---")
            print(json.dumps(analysis_summary, indent=2))

            markdown_report = generate_markdown_report(analysis_summary, config, run_timestamp, results_df)
            print("\n--- Markdown Summary ---")
            print(markdown_report)
        else:
            print("\nNo results to analyze.")

    finally:
        if backend_type == "ray" and ray.is_initialized():
            print("Shutting down Ray...")
            ray.shutdown()

def save_results(results: List[Dict], analysis: Dict, config: Dict, run_timestamp: str, results_df: pd.DataFrame):
    """
    Saves the experiment results, analysis report, and the config used for the
    run to a timestamped directory.
    """
    results_dir = config.get("results_dir", "meta_orchestrator/results")
    output_dir = os.path.join(results_dir, f"run_{run_timestamp}")
    os.makedirs(output_dir, exist_ok=True)

    # Save raw results JSON
    results_path = os.path.join(output_dir, "results.json")
    try:
        with open(results_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nRaw results saved to {results_path}")
    except IOError as e:
        print(f"Error saving raw results: {e}")

    # Save summary markdown report
    report_path = os.path.join(output_dir, "summary.md")
    try:
        markdown_report = generate_markdown_report(analysis, config, run_timestamp, results_df)
        with open(report_path, "w") as f:
            f.write(markdown_report)
        print(f"Markdown summary report saved to {report_path}")
    except IOError as e:
        print(f"Error saving summary report: {e}")

    # Save the configuration used for this run
    config_path = os.path.join(output_dir, "config.yaml")
    try:
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        print(f"Run configuration saved to {config_path}")
    except IOError as e:
        print(f"Error saving run configuration: {e}")

if __name__ == "__main__":
    config = load_config("config.yaml")
    run_experiment_suite(config)