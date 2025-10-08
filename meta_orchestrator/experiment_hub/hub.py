import json
import yaml
import os
import uuid
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List

# Import the centralized registry and orchestrators
from .registry import REGISTRY
from ..core.interpreter import Interpreter
from .scoring import analyze_results, generate_markdown_report
from ..orchestrators.mab_orchestrator import StandardOrchestrator, MultiArmedBanditOrchestrator, BayesianOptOrchestrator
from .execution import run_trial

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
    context = {"interpreter": interpreter_instance} # General context

    if orchestrator_type == 'mab':
        settings = orchestrator_config.get('mab_settings', {})
        orchestrator = MultiArmedBanditOrchestrator(strategy=settings.get('strategy'), epsilon=settings.get('epsilon'))
        variants = settings.get('variants', [])
        print(f"\n--- Running MAB Orchestrator with variants: {variants} ---")
        all_results = list(orchestrator.run(variants, settings, context))

    elif orchestrator_type == 'standard':
        orchestrator = StandardOrchestrator()
        experiments = orchestrator_config.get('standard_settings', {}).get('experiments', [])
        for experiment in experiments:
            if not experiment.get("enabled", False): continue
            print(f"\n--- Running Standard Experiment: {experiment['name']} ---")
            variants = experiment["variants"]
            exp_context = context.copy()
            if any("caching" in v for v in variants):
                exp_context["task_id"] = f"repeated_task_{uuid.uuid4()}"
            all_results.extend(list(orchestrator.run(variants, experiment, exp_context)))

    elif orchestrator_type == 'bayesian_optimization':
        orchestrator = BayesianOptOrchestrator()
        settings = orchestrator_config.get('tuning_settings', {})
        # The 'variants' for this orchestrator is just the single tunable agent
        variants = [settings.get('variant')]
        print(f"\n--- Running Bayesian Optimization for: {variants[0]} ---")
        # The context needs a consistent task_id for comparing parameter sets
        context["task_id"] = f"hpo_task_{uuid.uuid4()}"
        all_results = list(orchestrator.run(variants, settings, context))

    else:
        raise ValueError(f"Unknown orchestrator type: {orchestrator_type}")

    # --- Save, and Analyze ---
    if all_results:
        run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        scoring_weights = config.get("scoring_weights", {})

        analysis_summary = analyze_results(all_results, scoring_weights)

        # Convert results to a DataFrame for causal analysis and reporting
        results_df = pd.DataFrame(all_results)

        save_results(all_results, analysis_summary, config, run_timestamp, results_df)

        print("\n--- Combined Experiment Analysis Summary ---")
        print(json.dumps(analysis_summary, indent=2))

        markdown_report = generate_markdown_report(analysis_summary, config, run_timestamp, results_df)
        print("\n--- Markdown Summary ---")
        print(markdown_report)
    else:
        print("\nNo results to analyze.")


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