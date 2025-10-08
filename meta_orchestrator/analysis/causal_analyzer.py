import pandas as pd
from typing import Dict, Any, List, Optional

# Conditionally import dowhy to avoid errors if not installed
try:
    from dowhy import CausalModel
except ImportError:
    CausalModel = None

class CausalAnalyzer:
    """
    Performs causal analysis on experiment results to find causal insights.
    """

    def __init__(self, results_df: pd.DataFrame, config: Dict[str, Any]):
        """
        Initializes the analyzer.

        Args:
            results_df: DataFrame of raw trial-level results.
            config: The experiment configuration dictionary.
        """
        if CausalModel is None:
            raise ImportError("The 'dowhy' library is required for causal analysis. Please install it.")

        self.results_df = results_df
        self.config = config
        self.insights = []

    def run_all_analyses(self) -> List[str]:
        """
        Runs all implemented causal analyses.
        """
        self._analyze_caching_agent_latency()
        # Future causal analyses can be added here
        return self.insights

    def _analyze_caching_agent_latency(self):
        """
        Analyzes the causal effect of cache hits on the latency of caching agents.
        """
        print("Running causal analysis: Caching Agent Latency...")

        # 1. Select the relevant data
        # Find variants that have the 'was_cached' metric
        caching_variants_df = self.results_df[self.results_df['was_cached'].notna()].copy()
        if caching_variants_df.empty:
            print("  - No data found for caching agents. Skipping.")
            return

        # DoWhy expects boolean or 0/1 for treatment
        caching_variants_df['was_cached'] = caching_variants_df['was_cached'].astype(int)

        # 2. Create a causal model
        # We assume a simple causal graph: was_cached -> latency_internal_s
        try:
            model = CausalModel(
                data=caching_variants_df,
                treatment='was_cached',
                outcome='latency_internal_s',
                common_causes=[] # In this simple case, we assume no confounders
            )

            # 3. Identify the causal effect
            identified_estimand = model.identify_effect()

            # 4. Estimate the effect
            estimate = model.estimate_effect(
                identified_estimand,
                method_name="backdoor.linear_regression"
            )

            # 5. Refute the estimate to check for statistical significance
            refute_result = model.refute_estimate(
                identified_estimand,
                estimate,
                method_name="placebo_treatment_refuter",
                placebo_type="permute"
            )

            # 6. Generate a human-readable insight
            causal_effect = estimate.value
            p_value = refute_result.refutation_result["p_value"]

            if p_value < 0.05:
                insight = (
                    f"**Finding for Caching Agents:** A cache hit (`was_cached=True`) "
                    f"**causes** an estimated **{causal_effect:.4f}s change** in mean latency. "
                    f"(p-value: {p_value:.4f})"
                )
                self.insights.append(insight)
            else:
                print(f"  - Caching analysis did not yield a significant result (p-value: {p_value:.4f}).")

        except Exception as e:
            print(f"  - Causal analysis for caching agents failed: {e}")

# Example Usage
if __name__ == '__main__':
    mock_data = [
        {'variant': 'caching_agent', 'was_cached': False, 'latency_internal_s': 0.15, 'cost': 0.008},
        {'variant': 'caching_agent', 'was_cached': True, 'latency_internal_s': 0.01, 'cost': 0.0001},
        {'variant': 'caching_agent', 'was_cached': False, 'latency_internal_s': 0.16, 'cost': 0.008},
        {'variant': 'caching_agent', 'was_cached': True, 'latency_internal_s': 0.02, 'cost': 0.0001},
        {'variant': 'caching_agent', 'was_cached': False, 'latency_internal_s': 0.14, 'cost': 0.008},
        {'variant': 'caching_agent', 'was_cached': True, 'latency_internal_s': 0.015, 'cost': 0.0001},
        {'variant': 'stateless_agent', 'was_cached': None, 'latency_internal_s': 0.05, 'cost': 0.002},
    ]
    mock_df = pd.DataFrame(mock_data)
    mock_config = {}

    analyzer = CausalAnalyzer(mock_df, mock_config)
    insights = analyzer.run_all_analyses()

    print("\n--- Causal Insights ---")
    for insight_text in insights:
        print(f"- {insight_text}")