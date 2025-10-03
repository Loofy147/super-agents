from typing import Dict, List
import numpy as np

def calculate_score(trial_result: Dict, weights: Dict = None) -> float:
    """
    Calculates a weighted score for a single experiment trial.

    The score is designed to balance multiple objectives: autonomy, success,
    cost, and latency. Higher is better.

    Args:
        trial_result: A dictionary containing the metrics for one trial.
                      Expected keys: 'autonomy', 'success', 'cost', 'latency_internal_s'.
        weights: A dictionary with custom weights for the scoring formula.
                 If None, default weights are used.

    Returns:
        The calculated score.
    """
    if weights is None:
        # Default weights as specified in the challenge
        weights = {
            "autonomy": 0.4,
            "success": 0.35,
            "cost": -0.15,  # Negative because higher cost is bad
            "latency": -0.1   # Negative because higher latency is bad
        }

    # Extract metrics, providing defaults if they are missing
    autonomy = trial_result.get("autonomy", 0)
    success = trial_result.get("success", 0)
    cost = trial_result.get("cost", 0)
    # The hub records latency as 'latency_internal_s'
    latency = trial_result.get("latency_internal_s", 0)

    # Calculate the weighted score
    score = (weights["autonomy"] * autonomy +
             weights["success"] * success +
             weights["cost"] * cost +
             weights["latency"] * latency)

    return score

def analyze_results(results: List[Dict]) -> Dict:
    """
    Analyzes a list of experiment results, calculating aggregate statistics
    and scores for each variant.

    Args:
        results: A list of trial result dictionaries from an experiment run.

    Returns:
        A dictionary containing analysis for each variant, including mean scores,
        confidence intervals, and raw metrics.
    """
    variants = set(r['variant'] for r in results)
    analysis_summary = {}

    for variant in sorted(list(variants)):
        variant_results = [r for r in results if r['variant'] == variant]

        # Calculate scores for all trials of this variant
        scores = [calculate_score(r) for r in variant_results]

        # Calculate statistics
        mean_score = np.mean(scores)
        std_dev = np.std(scores)
        # Calculate 95% confidence interval for the mean score
        ci_95 = 1.96 * (std_dev / np.sqrt(len(scores)))

        # Aggregate other metrics
        mean_latency = np.mean([r.get("latency_internal_s", 0) for r in variant_results])
        total_cost = np.sum([r.get("cost", 0) for r in variant_results])
        success_rate = np.mean([r.get("success", 0) for r in variant_results])

        analysis_summary[variant] = {
            "trials": len(variant_results),
            "mean_score": round(mean_score, 4),
            "score_std_dev": round(std_dev, 4),
            "mean_score_ci_95": round(ci_95, 4),
            "mean_latency_s": round(mean_latency, 4),
            "total_cost": round(total_cost, 4),
            "success_rate": round(success_rate, 4)
        }

    return analysis_summary

# Example usage:
if __name__ == "__main__":
    # Mock results from an experiment run
    mock_experiment_results = [
        {'success': 1, 'cost': 0.001, 'autonomy': 0.8, 'latency_internal_s': 0.02, 'variant': 'in_memory_probe'},
        {'success': 1, 'cost': 0.005, 'autonomy': 0.95, 'latency_internal_s': 0.1, 'variant': 'slower_reliable_probe'},
        {'success': 0, 'cost': 0.001, 'autonomy': 0.8, 'latency_internal_s': 0.02, 'variant': 'in_memory_probe'},
        {'success': 1, 'cost': 0.005, 'autonomy': 0.95, 'latency_internal_s': 0.1, 'variant': 'slower_reliable_probe'}
    ]

    # --- Test calculate_score ---
    print("--- Testing calculate_score ---")
    score1 = calculate_score(mock_experiment_results[0])
    score2 = calculate_score(mock_experiment_results[1])
    print(f"Score for '{mock_experiment_results[0]['variant']}': {score1:.4f}")
    print(f"Score for '{mock_experiment_results[1]['variant']}': {score2:.4f}")

    # --- Test analyze_results ---
    print("\n--- Testing analyze_results ---")
    summary = analyze_results(mock_experiment_results)
    import json
    print(json.dumps(summary, indent=2))