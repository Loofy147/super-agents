import random
import numpy as np
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generator

from ..experiment_hub.execution import run_trial
from ..experiment_hub.scoring import calculate_score


class BaseOrchestrator(ABC):
    """Abstract base class for all orchestrators."""
    @abstractmethod
    def run(self, variants: List[str], config: Dict[str, Any], context: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """
        Run an experiment, yielding results for each trial as they complete.

        Args:
            variants: A list of variant names to test.
            config: A dictionary containing the experiment configuration.
            context: A dictionary for passing stateful objects like interpreters.

        Yields:
            A dictionary with the trial results for each completed trial.
        """
        pass


class StandardOrchestrator(BaseOrchestrator):
    """
    The default orchestrator that runs a fixed number of trials for each variant.
    """
    def run(self, variants: List[str], config: Dict[str, Any], context: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        trials_per_variant = config['trials_per_variant']
        print(f"Running {trials_per_variant} trials for each of {variants}")
        for _ in range(trials_per_variant):
            for v_name in variants:
                try:
                    trial_result = run_trial(v_name, context)
                    yield trial_result
                except Exception as e:
                    print(f"ERROR running trial for variant {v_name}: {e}")


class MultiArmedBanditOrchestrator(BaseOrchestrator):
    """
    An orchestrator that uses a Multi-Armed Bandit strategy to dynamically
    allocate trials to the best-performing variants.
    """
    def __init__(self, strategy: str = "thompson_sampling", epsilon: float = 0.1):
        if strategy not in ["epsilon_greedy", "thompson_sampling"]:
            raise ValueError("Invalid MAB strategy. Choose 'epsilon_greedy' or 'thompson_sampling'.")
        self.strategy = strategy
        self.epsilon = epsilon
        print(f"Initialized Multi-Armed Bandit Orchestrator with strategy: {self.strategy}")

    def run(self, variants: List[str], config: Dict[str, Any], context: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """
        Runs an experiment using the configured MAB strategy, yielding results.
        """
        total_trials = config.get('total_trials', 100)
        scoring_weights = config.get('scoring_weights')

        if self.strategy == "epsilon_greedy":
            performance = {v: {"score_sum": 0, "runs": 0} for v in variants}
        elif self.strategy == "thompson_sampling":
            performance = {v: {"mu": 0, "lambda": 1, "tau": 1} for v in variants}

        print(f"Running MAB experiment for {total_trials} trials...")

        for i in range(total_trials):
            chosen_variant = self._select_variant(variants, performance)

            if "caching" in chosen_variant:
                context['task_id'] = 'mab_repeated_task'

            trial_result = run_trial(chosen_variant, context)
            score = calculate_score(trial_result, scoring_weights)
            trial_result['score'] = score

            self._update_performance(chosen_variant, score, performance)

            if (i+1) % 20 == 0:
                print(f"  ... completed trial {i+1}/{total_trials}")

            yield trial_result

    def _select_variant(self, variants: List[str], performance: Dict) -> str:
        if self.strategy == "epsilon_greedy":
            if random.random() < self.epsilon:
                return random.choice(variants)
            else:
                avg_scores = {
                    v: (p["score_sum"] / p["runs"]) if p["runs"] > 0 else 0
                    for v, p in performance.items()
                }
                return max(avg_scores, key=avg_scores.get)

        elif self.strategy == "thompson_sampling":
            samples = {
                v: np.random.normal(p['mu'], 1. / np.sqrt(p['lambda'] * p['tau']))
                for v, p in performance.items()
            }
            return max(samples, key=samples.get)

    def _update_performance(self, variant: str, score: float, performance: Dict):
        if self.strategy == "epsilon_greedy":
            performance[variant]["score_sum"] += score
            performance[variant]["runs"] += 1

        elif self.strategy == "thompson_sampling":
            mu_n = performance[variant]['mu']
            lambda_n = performance[variant]['lambda']
            alpha_n = performance[variant]['tau']

            lambda_new = lambda_n + 1
            mu_new = (lambda_n * mu_n + score) / lambda_new
            alpha_new = alpha_n + 0.5
            beta_new = 1 + 0.5 * (lambda_n * (score - mu_n)**2 / (lambda_n + 1))

            performance[variant]['mu'] = mu_new
            performance[variant]['lambda'] = lambda_new
            performance[variant]['tau'] = alpha_new / beta_new