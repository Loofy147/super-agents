import json
import time
import uuid
from typing import Dict, Any, Callable, List

# Import the centralized registry
from .registry import REGISTRY

def run_trial(variant_name: str, context: Dict) -> Dict:
    """
    Runs a single trial for a given variant.

    Args:
        variant_name: The name of the variant to run.
        context: The context or input for the trial.

    Returns:
        A dictionary with the trial results.
    """
    if variant_name not in REGISTRY:
        raise ValueError(f"Variant '{variant_name}' not found in registry.")

    start_time = time.monotonic()
    # Execute the variant function
    result = REGISTRY[variant_name](context)
    end_time = time.monotonic()

    # Enrich the result with metadata
    result.update({
        "variant": variant_name,
        "trace_id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "latency_internal_s": end_time - start_time
    })
    return result

def run_experiment(variants: List[str], trials_per_variant: int, context: Dict = None) -> List[Dict]:
    """
    Runs a full experiment across multiple variants for a set number of trials.

    Args:
        variants: A list of variant names to test.
        trials_per_variant: The number of times to run each variant.
        context: The context to pass to each trial.

    Returns:
        A list of result dictionaries for all trials.
    """
    if context is None:
        context = {}

    output_results = []
    print(f"Starting experiment: {trials_per_variant} trials for variants {variants}")
    for _ in range(trials_per_variant):
        for v_name in variants:
            try:
                trial_result = run_trial(v_name, context)
                output_results.append(trial_result)
            except Exception as e:
                print(f"ERROR running trial for variant {v_name}: {e}")

    print(f"Experiment finished. Total trials run: {len(output_results)}")
    return output_results

# --- Main execution block for demonstration ---

if __name__ == "__main__":
    # Import necessary modules
    from .scoring import analyze_results
    from ..core.interpreter import Interpreter
    # This import triggers the __init__.py in the variants package,
    # which discovers and registers all variants.
    import meta_orchestrator.experiment_hub.variants

    print(f"Registered variants: {list(REGISTRY.keys())}")

    # --- Experiment 1: Compare stateless agents ---
    print("\n--- Running Experiment 1: Stateless Probes ---")
    stateless_variants = ["in_memory_probe", "slower_reliable_probe"]
    stateless_results = run_experiment(stateless_variants, trials_per_variant=20)

    # --- Experiment 2: Test the caching agent ---
    print("\n--- Running Experiment 2: Caching Agent ---")
    caching_variant = "caching_agent"
    interpreter_instance = Interpreter()
    caching_results = []

    # Simulate running the same task multiple times to test the cache
    task_id = "repeated_task_123"
    for i in range(5):
        print(f"Running trial {i+1}/5 for task '{task_id}'...")
        context = {"interpreter": interpreter_instance, "task_id": task_id}
        caching_results.append(run_trial(caching_variant, context))

    # --- Combine, Save, and Analyze ---
    all_results = stateless_results + caching_results

    output_path = "meta_orchestrator/results/latest_run.json"
    try:
        with open(output_path, "w") as f:
            json.dump(all_results, f, indent=2)
        print(f"\nResults saved to {output_path}")
    except IOError as e:
        print(f"Error saving results: {e}")

    # Analyze and print the results summary
    if all_results:
        print("\n--- Combined Experiment Analysis Summary ---")
        analysis_summary = analyze_results(all_results)
        print(json.dumps(analysis_summary, indent=2))
    else:
        print("\nNo results to analyze.")