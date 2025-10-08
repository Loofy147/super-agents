import random
import numpy as np
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generator, Type
from skopt import Optimizer
from skopt.space import Real, Integer, Categorical

from ..experiment_hub.execution import run_trial
from ..experiment_hub.scoring import calculate_score
from ..core.base_tunable_variant import TunableAgentVariant
from ..experiment_hub.variants import tunable_caching_agent # To find the class

# A registry to map variant names to their tunable classes
TUNABLE_VARIANT_REGISTRY: Dict[str, Type[TunableAgentVariant]] = {
    "tunable_caching_agent": tunable_caching_agent.TunableCachingAgent,
}


class BaseOrchestrator(ABC):
    """Abstract base class for all orchestrators."""
    @abstractmethod
    def run(self, variants: List[str], config: Dict[str, Any], context: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """Run an experiment, yielding results for each trial as they complete."""
        pass


class StandardOrchestrator(BaseOrchestrator):
    """The default orchestrator that runs a fixed number of trials for each variant."""
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
    """An orchestrator that uses a Multi-Armed Bandit strategy."""
    # ... (implementation remains the same)
    def __init__(self, strategy: str = "thompson_sampling", epsilon: float = 0.1):
        if strategy not in ["epsilon_greedy", "thompson_sampling"]:
            raise ValueError("Invalid MAB strategy. Choose 'epsilon_greedy' or 'thompson_sampling'.")
        self.strategy = strategy
        self.epsilon = epsilon
        print(f"Initialized Multi-Armed Bandit Orchestrator with strategy: {self.strategy}")

    def run(self, variants: List[str], config: Dict[str, Any], context: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
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
            if random.random() < self.epsilon: return random.choice(variants)
            else: return max({v: (p["score_sum"] / p["runs"]) if p["runs"] > 0 else 0 for v, p in performance.items()}, key=lambda v: v[1])
        elif self.strategy == "thompson_sampling":
            return max({v: np.random.normal(p['mu'], 1. / np.sqrt(p['lambda'] * p['tau'])) for v, p in performance.items()}, key=lambda v: v[1])
    def _update_performance(self, variant: str, score: float, performance: Dict):
        if self.strategy == "epsilon_greedy":
            performance[variant]["score_sum"] += score
            performance[variant]["runs"] += 1
        elif self.strategy == "thompson_sampling":
            mu_n, lambda_n, alpha_n = performance[variant]['mu'], performance[variant]['lambda'], performance[variant]['tau']
            lambda_new = lambda_n + 1
            mu_new = (lambda_n * mu_n + score) / lambda_new
            alpha_new = alpha_n + 0.5
            beta_new = 1 + 0.5 * (lambda_n * (score - mu_n)**2 / (lambda_n + 1))
            performance[variant].update({'mu': mu_new, 'lambda': lambda_new, 'tau': alpha_new / beta_new})


class BayesianOptOrchestrator(BaseOrchestrator):
    """
    Uses Bayesian Optimization to find the best hyperparameters for a single
    TunableAgentVariant.
    """
    def run(self, variants: List[str], config: Dict[str, Any], context: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        variant_name = config['variant']
        if variant_name not in TUNABLE_VARIANT_REGISTRY:
            raise ValueError(f"Tunable variant '{variant_name}' not found in registry.")

        variant_class = TUNABLE_VARIANT_REGISTRY[variant_name]

        # 1. Parse the parameter space from config
        space = []
        param_names = []
        for name, details in config['parameter_space'].items():
            param_names.append(name)
            if details['type'] == 'int':
                space.append(Integer(details['range'][0], details['range'][1], name=name))
            elif details['type'] == 'float':
                space.append(Real(details['range'][0], details['range'][1], "log-uniform", name=name))
            elif details['type'] == 'categorical':
                space.append(Categorical(details['choices'], name=name))

        optimizer = Optimizer(dimensions=space, random_state=1, base_estimator="GP")

        total_trials = config.get('total_trials', 50)
        trials_per_config = config.get('trials_per_config', 5) # How many times to run each param set
        scoring_weights = config.get('scoring_weights')

        print(f"Running Bayesian Optimization for '{variant_name}' over {total_trials} configurations.")

        for i in range(total_trials):
            # 2. Ask the optimizer for the next set of parameters
            suggested_params_list = optimizer.ask()
            params_dict = {name: val for name, val in zip(param_names, suggested_params_list)}

            print(f"\n[{i+1}/{total_trials}] Testing parameters: {params_dict}")

            # 3. Instantiate the agent and run it
            try:
                agent_instance = variant_class(params=params_dict)
            except Exception as e:
                print(f"Error instantiating agent with params {params_dict}: {e}")
                optimizer.tell(suggested_params_list, 1e9) # Tell optimizer it was a very bad result
                continue

            # 4. Run trials to get a stable score
            scores = []
            for _ in range(trials_per_config):
                trial_result = agent_instance.run(context)
                score = calculate_score(trial_result, scoring_weights)
                trial_result['score'] = score
                trial_result['params'] = params_dict # Add params for analysis
                yield trial_result
                scores.append(score)

            mean_score = np.mean(scores)
            # We want to MINIMIZE the objective function, so we use negative score
            objective_value = -mean_score
            print(f"  ... Mean Score: {mean_score:.4f} (Objective: {objective_value:.4f})")

            # 5. Tell the optimizer the result
            optimizer.tell(suggested_params_list, objective_value)

        print("\nBayesian Optimization finished.")
        best_params_list = optimizer.Xi[np.argmin(optimizer.yi)]
        best_params_dict = {name: val for name, val in zip(param_names, best_params_list)}
        print(f"Best parameters found: {best_params_dict}")
        print(f"Best score: {-np.min(optimizer.yi):.4f}")