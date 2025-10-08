import json
import yaml
import os
from datetime import datetime
from typing import Dict, Any, List

# Import the centralized registry and orchestrators
from .registry import REGISTRY
from ..core.interpreter import Interpreter
from .scoring import analyze_results, generate_markdown_report
from ..orchestrators.mab_orchestrator import StandardOrchestrator, MultiArmedBanditOrchestrator
from .execution import run_trial # <-- Import from new location

# This import triggers the __init__.py in the variants package,
# which discovers and registers all variants.
import meta_orchestrator.experiment_hub.variants


def load_config(config_path: str) -> Dict:
    """Loads the experiment configuration from a YAML file."""
    print(f"Loading configuration from: {config_path}")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def run_experiment_suite(config: Dict):
    """
    Selects an orchestrator and runs the experiment suite.
    """
    print(f"Registered variants: {list(REGISTRY.keys())}")

    orchestrator_config = config.get('orchestrator', {})
    orchestrator_type = orchestrator_config.get('type', 'standard')
    all_results = []
    interpreter_instance = Interpreter()

    if orchestrator_type == 'mab':
        mab_settings = orchestrator_config.get('mab_settings', {})
        orchestrator = MultiArmedBanditOrchestrator(
            strategy=mab_settings.get('strategy', 'thompson_sampling'),
            epsilon=mab_settings.get('epsilon', 0.1)
        )
        variants = mab_settings.get('variants', [])
        # Provide the interpreter to the context for MAB runs if needed
        context = {"interpreter": interpreter_instance}
        exp_config = mab_settings
        print(f"\n--- Running MAB Orchestrator with variants: {variants} ---")
        all_results = orchestrator.run(variants, exp_config, context)

    elif orchestrator_type == 'standard':
        orchestrator = StandardOrchestrator()
        experiments = orchestrator_config.get('standard_settings', {}).get('experiments', [])

        for experiment in experiments:
            if not experiment.get("enabled", False):
                print(f"\n--- Skipping Experiment: {experiment['name']} (disabled) ---")
                continue

            print(f"\n--- Running Standard Experiment: {experiment['name']} ---")
            variants = experiment["variants"]
            exp_config = experiment
            context = {}

            is_caching_test = any("caching" in v for v in variants)
            if is_caching_test:
                # For caching tests, we need a consistent task_id and interpreter
                task_id = f"repeated_task_{uuid.uuid4()}"
                context = {"interpreter": interpreter_instance, "task_id": task_id}

            all_results.extend(orchestrator.run(variants, exp_config, context))

    else:
        raise ValueError(f"Unknown orchestrator type: {orchestrator_type}")

    # --- Save, and Analyze ---
    if all_results:
        run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        scoring_weights = config.get("scoring_weights", {})

        analysis_summary = analyze_results(all_results, scoring_weights)

        save_results(all_results, analysis_summary, config, run_timestamp)

        print("\n--- Combined Experiment Analysis Summary ---")
        print(json.dumps(analysis_summary, indent=2))

        # Also print the markdown report to console for immediate feedback
        markdown_report = generate_markdown_report(analysis_summary, config, run_timestamp)
        print("\n--- Markdown Summary ---")
        print(markdown_report)
    else:
        print("\nNo results to analyze.")


def save_results(results: List[Dict], analysis: Dict, config: Dict, run_timestamp: str):
    """
    Saves the experiment results and analysis report to a timestamped directory.
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
        markdown_report = generate_markdown_report(analysis, config, run_timestamp)
        with open(report_path, "w") as f:
            f.write(markdown_report)
        print(f"Markdown summary report saved to {report_path}")
    except IOError as e:
        print(f"Error saving summary report: {e}")

if __name__ == "__main__":
    config = load_config("config.yaml")
    run_experiment_suite(config)