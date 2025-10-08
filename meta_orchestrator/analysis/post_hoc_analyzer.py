import pandas as pd
from typing import Dict, Any, List, Optional

class PostHocAnalyzer:
    """
    Analyzes completed experiment runs to find interesting patterns and suggest
    follow-up experiments.
    """

    def __init__(self, results_df: pd.DataFrame, analysis_summary: Dict[str, Any]):
        """
        Initializes the analyzer with the data from a completed run.

        Args:
            results_df: A DataFrame containing the raw trial-level results.
            analysis_summary: A dictionary containing the aggregated analysis.
        """
        self.results_df = results_df
        self.analysis_summary = analysis_summary
        self.suggestions = []

    def run_all_analyses(self) -> List[Dict[str, Any]]:
        """
        Runs all available analysis detectors and returns a list of suggestions.
        """
        self.detect_high_variance_variants()
        # Future detectors can be added here, e.g.:
        # self.detect_performance_outliers()
        # self.detect_subgroup_specialists()
        return self.suggestions

    def detect_high_variance_variants(self, std_dev_threshold: float = 0.1):
        """
        Identifies variants with high performance variance.

        A high standard deviation in the score suggests that an agent's
        performance is unstable or highly sensitive to hidden variables.

        Args:
            std_dev_threshold: The score standard deviation above which a
                               variant is considered to have high variance.
        """
        print("Running analysis: High Variance Detector...")
        for variant, stats in self.analysis_summary.items():
            score_std_dev = stats.get("score_std_dev", 0)
            if score_std_dev > std_dev_threshold:
                suggestion = {
                    "type": "HighVariance",
                    "variant": variant,
                    "message": (
                        f"Variant '{variant}' shows high performance variance "
                        f"(Score Std Dev: {score_std_dev:.4f}). Consider running "
                        f"more trials to get a more stable performance estimate."
                    ),
                    "details": {
                        "score_std_dev": score_std_dev,
                        "trials": stats.get("trials"),
                    },
                    "proposed_action": {
                        "type": "increase_trials",
                        "variant": variant,
                        "new_trials_per_variant": stats.get("trials", 20) * 5,
                    }
                }
                self.suggestions.append(suggestion)

# Example Usage
if __name__ == '__main__':
    # Create mock data for demonstration
    mock_summary = {
        "stable_agent": {"score_std_dev": 0.02, "trials": 50},
        "unstable_agent": {"score_std_dev": 0.15, "trials": 50},
    }
    mock_df = pd.DataFrame() # Not needed for this specific detector

    analyzer = PostHocAnalyzer(mock_df, mock_summary)
    suggestions = analyzer.run_all_analyses()

    import json
    print("\n--- Analysis Suggestions ---")
    print(json.dumps(suggestions, indent=2))