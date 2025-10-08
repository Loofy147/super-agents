import json
from typing import Dict, List
import numpy as np
import pandas as pd
from datetime import datetime

# Conditionally import CausalAnalyzer to allow the system to run without dowhy
try:
    from ..analysis.causal_analyzer import CausalAnalyzer
except ImportError:
    CausalAnalyzer = None

def calculate_score(trial_result: Dict, weights: Dict) -> float:
    """
    Calculates a weighted score for a single experiment trial.

    Args:
        trial_result: A dictionary containing the metrics for one trial.
        weights: A dictionary with custom weights for the scoring formula.

    Returns:
        The calculated score.
    """
    autonomy = trial_result.get("autonomy", 0)
    success = trial_result.get("success", 0)
    cost = trial_result.get("cost", 0)
    latency = trial_result.get("latency_internal_s", 0)

    score = (weights.get("autonomy", 0) * autonomy +
             weights.get("success", 0) * success +
             weights.get("cost", 0) * cost +
             weights.get("latency", 0) * latency)
    return score

def analyze_results(results: List[Dict], scoring_weights: Dict) -> Dict:
    """
    Analyzes a list of experiment results, calculating aggregate statistics
    and scores for each variant.

    Args:
        results: A list of trial result dictionaries from an experiment run.
        scoring_weights: The weights used for scoring.

    Returns:
        A dictionary containing analysis for each variant.
    """
    variants = set(r['variant'] for r in results)
    analysis_summary = {}

    for variant in sorted(list(variants)):
        variant_results = [r for r in results if r['variant'] == variant]
        if not variant_results:
            continue

        scores = [calculate_score(r, scoring_weights) for r in variant_results if 'score' not in r]

        mean_score = np.mean(scores) if scores else 0
        std_dev = np.std(scores) if scores else 0

        if len(scores) > 1:
            ci_95 = 1.96 * (std_dev / np.sqrt(len(scores)))
        else:
            ci_95 = float('nan')

        analysis_summary[variant] = {
            "trials": len(variant_results),
            "mean_score": round(mean_score, 4),
            "score_std_dev": round(std_dev, 4),
            "mean_score_ci_95": round(ci_95, 4),
            "mean_latency_s": round(np.mean([r.get("latency_internal_s", 0) for r in variant_results]), 4),
            "total_cost": round(np.sum([r.get("cost", 0) for r in variant_results]), 4),
            "success_rate": round(np.mean([r.get("success", 0) for r in variant_results]), 4)
        }
    return analysis_summary

def generate_markdown_report(analysis: Dict, config: Dict, run_timestamp: str, results_df: pd.DataFrame) -> str:
    """
    Generates a human-readable Markdown report, including causal insights.
    """
    report = []
    report.append("# Experiment Run Summary")
    report.append(f"**Run Timestamp:** `{run_timestamp}`")

    orch_config = config.get('orchestrator', {})
    report.append(f"**Orchestrator:** `{orch_config.get('type', 'standard')}`")
    if orch_config.get('type') == 'mab':
        mab_settings = orch_config.get('mab_settings', {})
        report.append(f"- **Strategy:** `{mab_settings.get('strategy')}`")
        report.append(f"- **Total Trials:** `{mab_settings.get('total_trials')}`")

    report.append("\n## Overall Variant Ranking")
    header = "| Rank | Variant | Mean Score (± 95% CI) | Success Rate | Avg Latency (s) | Total Cost | Trials |"
    separator = "|:----:|:--------|:----------------------|:--------------:|:----------------:|:------------:|:------:|"
    report.append(header)
    report.append(separator)

    sorted_variants = sorted(analysis.items(), key=lambda item: item[1]['mean_score'], reverse=True)
    for i, (name, stats) in enumerate(sorted_variants):
        rank = i + 1
        score_str = f"{stats['mean_score']:.4f} (± {stats['mean_score_ci_95']:.4f})"
        success_str = f"{stats['success_rate']:.2%}"
        row = f"| {rank} | `{name}` | {score_str} | {success_str} | {stats['mean_latency_s']:.4f} | {stats['total_cost']:.4f} | {stats['trials']} |"
        report.append(row)

    # --- Causal Analysis ---
    if CausalAnalyzer:
        try:
            causal_analyzer = CausalAnalyzer(results_df, config)
            insights = causal_analyzer.run_all_analyses()
            if insights:
                report.append("\n## 🧠 Causal Insights")
                for insight in insights:
                    report.append(f"- {insight}")
        except ImportError:
            report.append("\n*Causal analysis skipped: 'dowhy' library not installed.*")
        except Exception as e:
            report.append(f"\n*Causal analysis failed: {e}*")

    # --- Configuration Details ---
    report.append("\n## Experiment Configuration")
    report.append("### Scoring Weights")
    report.append("```json")
    report.append(json.dumps(config.get('scoring_weights'), indent=2))
    report.append("```")

    return "\n".join(report)