import numpy as np
import random
import json
from typing import Dict, Tuple, List, Any

# --- Mock Environment and Variants ---

# Define the "true" performance of our mock variants.
# This is the ground truth the algorithms will try to discover.
MOCK_VARIANTS = {
    "baseline": {"success_rate": 0.60, "cost": 0.002, "autonomy": 0.5, "latency": 0.05},
    "fast_unreliable": {"success_rate": 0.40, "cost": 0.001, "autonomy": 0.9, "latency": 0.01},
    "slow_expensive_best": {"success_rate": 0.95, "cost": 0.010, "autonomy": 0.9, "latency": 0.20},
}

def run_simulated_trial(variant_name: str) -> Dict[str, Any]:
    """Simulates a single run of a variant, returning its performance."""
    if variant_name not in MOCK_VARIANTS:
        raise ValueError(f"Unknown variant: {variant_name}")

    params = MOCK_VARIANTS[variant_name]

    # Simulate success based on the variant's true success rate
    success = 1 if random.random() < params["success_rate"] else 0

    return {
        "variant": variant_name,
        "success": success,
        "cost": params["cost"],
        "autonomy": params["autonomy"],
        "latency_internal_s": params["latency"]
    }

# --- Adaptive Allocation Algorithms ---

def simulate_epsilon_greedy(variants: list, budget: float, epsilon: float) -> Tuple[List[str], Dict[str, List[int]]]:
    """Simulates the epsilon-greedy strategy."""
    print(f"\n--- Running Epsilon-Greedy (epsilon={epsilon}) ---")

    # Track performance: {variant: [success_count, total_runs]}
    performance = {v: [0, 0] for v in variants}
    choices = []
    total_cost = 0

    while total_cost < budget:
        if random.random() < epsilon:
            # Exploration: choose a random variant
            chosen_variant = random.choice(variants)
        else:
            # Exploitation: choose the best-performing variant so far
            # Calculate current success rates, handling division by zero
            rates = {v: (p[0] / p[1]) if p[1] > 0 else 0 for v, p in performance.items()}
            chosen_variant = max(rates, key=rates.get)

        # Run the trial and get the result
        result = run_simulated_trial(chosen_variant)
        choices.append(chosen_variant)

        # Update performance stats and cost
        performance[chosen_variant][0] += result["success"]
        performance[chosen_variant][1] += 1
        total_cost += result["cost"]

    return choices, performance

def simulate_thompson_sampling(variants: list, budget: float) -> Tuple[List[str], Dict[str, List[int]]]:
    """Simulates the Thompson Sampling strategy using a Beta distribution."""
    print("\n--- Running Thompson Sampling ---")

    # Track performance: {variant: [alpha, beta]} where alpha=successes, beta=failures
    performance = {v: [1, 1] for v in variants} # Start with (1, 1) to avoid issues with zero
    choices = []
    total_cost = 0

    while total_cost < budget:
        # For each variant, draw a sample from its current Beta distribution
        samples = {v: np.random.beta(p[0], p[1]) for v, p in performance.items()}
        # Choose the variant with the highest sample
        chosen_variant = max(samples, key=samples.get)

        # Run the trial and get the result
        result = run_simulated_trial(chosen_variant)
        choices.append(chosen_variant)

        # Update performance stats (alpha/beta) and cost
        if result["success"] == 1:
            performance[chosen_variant][0] += 1
        else:
            performance[chosen_variant][1] += 1
        total_cost += result["cost"]

    return choices, performance

# --- Main Simulation Harness ---

if __name__ == "__main__":
    simulation_budget = 0.50  # Total cost allowed for the simulation
    variant_names = list(MOCK_VARIANTS.keys())

    # Run Epsilon-Greedy
    eg_choices, eg_perf = simulate_epsilon_greedy(variant_names, budget=simulation_budget, epsilon=0.1)

    # Run Thompson Sampling
    ts_choices, ts_perf = simulate_thompson_sampling(variant_names, budget=simulation_budget)

    # --- Analysis and Reporting ---
    def print_summary(name: str, choices: List[str], performance: Dict[str, List[int]]) -> None:
        print(f"\n--- {name} Summary ---")
        total_runs = len(choices)
        print(f"Total trials: {total_runs}")

        # Print choice distribution
        variant_names = list(performance.keys())
        choice_counts = {v: choices.count(v) for v in variant_names}
        for v, count in choice_counts.items():
            percentage = (count / total_runs) * 100 if total_runs > 0 else 0
            print(f"  - Chose '{v}': {count} times ({percentage:.1f}%)")

        # Print final success rates based on algorithm type
        print("Final learned success rates:")
        if "Epsilon-Greedy" in name:
            for v, p in performance.items():
                rate = (p[0] / p[1]) if p[1] > 0 else 0
                print(f"  - {v}: {rate:.2f} (successes={p[0]}, runs={p[1]})")
        elif "Thompson Sampling" in name:
            for v, p in performance.items():
                # For a Beta distribution, the mean is alpha / (alpha + beta)
                rate = p[0] / (p[0] + p[1])
                print(f"  - {v}: {rate:.2f} (alpha={p[0]}, beta={p[1]})")

    print_summary("Epsilon-Greedy (epsilon=0.1)", eg_choices, eg_perf)
    print_summary("Thompson Sampling", ts_choices, ts_perf)

    print("\n--- Ground Truth ---")
    for name, params in MOCK_VARIANTS.items():
        print(f"  - {name}: success_rate={params['success_rate']:.2f}, cost={params['cost']:.4f}")

    print("\nSimulation complete.")