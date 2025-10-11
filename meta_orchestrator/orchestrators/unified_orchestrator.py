import os
import json
import uuid
import random
import numpy as np
from typing import List, Dict, Any, Generator, Type

# Conditionally import ray and skopt to keep the core system lightweight
try:
    import ray
    from ..experiment_hub.execution import run_trial_remote
except ImportError:
    ray = None
    run_trial_remote = None

try:
    from skopt import Optimizer
    from skopt.space import Real, Integer, Categorical
except ImportError:
    Optimizer = None
    Real = Integer = Categorical = None

from ..experiment_hub.execution import run_trial
from ..experiment_hub.scoring import calculate_score
from ..core.base_variant import AgentVariant
from ..experiment_hub.variants import tunable_caching_agent, adversarial_agents
from ..agent_forge.designer import AgentDesigner
from ..agent_forge.code_generator import CodeGenerator
from ..agent_forge.code_healer import CodeHealer

# This registry is crucial for the unified orchestrator to find tunable classes
TUNABLE_VARIANT_REGISTRY: Dict[str, Type[AgentVariant]] = {
    "tunable_caching_agent": tunable_caching_agent.TunableCachingAgent,
}


class UnifiedOrchestrator:
    """A single orchestrator for all experiment types and execution backends.

    This class reads the experiment configuration and dispatches to the
    appropriate sub-handler based on the specified orchestrator type (e.g.,
    'standard', 'mab', 'gasi_run'). It also manages the execution backend
    (e.g., 'local' or 'ray') and provides a real-time results bus for the
    dashboard.
    """

    def __init__(self, config: Dict[str, Any], context: Dict[str, Any]):
        """Initializes the UnifiedOrchestrator.

        Args:
            config: The full experiment configuration dictionary.
            context: The base context to be used for all trials.
        """
        self.config = config
        self.base_context = context
        self.orchestrator_config = self.config.get('orchestrator', {})
        self.backend_config = self.config.get("execution_backend", {})
        self.execution_backend = self.backend_config.get("type", "local")

        # Setup for the real-time results bus
        results_dir = self.config.get("results_dir", "meta_orchestrator/results")
        self.live_run_path = os.path.join(results_dir, "live_run.jsonl")
        # Clear any previous live run file
        if os.path.exists(self.live_run_path):
            os.remove(self.live_run_path)

    def _write_to_bus(self, result: Dict[str, Any]):
        """Writes a single trial result to the live run bus.

        This allows the Streamlit dashboard to tail the results of a live
        experiment. It handles serialization of numpy types.

        Args:
            result: A dictionary representing the result of a single trial.
        """
        if not self.live_run_path:
            return

        # Ensure the directory for the live run file exists
        os.makedirs(os.path.dirname(self.live_run_path), exist_ok=True)

        with open(self.live_run_path, "a") as f:
            # We need to handle non-serializable numpy types
            serializable_result = {}
            for key, value in result.items():
                if isinstance(value, (np.integer, np.int64)):
                    serializable_result[key] = int(value)
                elif isinstance(value, (np.floating, np.float64)):
                    serializable_result[key] = float(value)
                else:
                    serializable_result[key] = value
            f.write(json.dumps(serializable_result) + "\n")

    def run_suite(self) -> Generator[Dict[str, Any], None, None]:
        """Runs the full experiment suite.

        This is the main entry point for the orchestrator. It reads the
        `orchestrator.type` from the config and dispatches the execution to
        the corresponding `_run_*` method.

        Yields:
            A dictionary for each trial result as it becomes available.
        """
        orchestrator_type = self.orchestrator_config.get('type', 'standard')

        print(f"--- Starting experiment suite with UnifiedOrchestrator ---")
        print(f"Orchestration mode: '{orchestrator_type}'")
        print(f"Execution backend: '{self.execution_backend}'")

        if orchestrator_type == 'standard':
            yield from self._run_standard()
        elif orchestrator_type == 'mab':
            yield from self._run_mab()
        elif orchestrator_type == 'bayesian_optimization':
            yield from self._run_bayesian_optimization()
        elif orchestrator_type == 'adversarial_benchmark':
            yield from self._run_adversarial_benchmark()
        elif orchestrator_type == 'gasi_run':
            yield from self._run_gasi()
        else:
            raise ValueError(f"Unknown orchestrator type: '{orchestrator_type}'")

    # --- Standard Orchestration Logic ---
    def _run_standard(self) -> Generator[Dict[str, Any], None, None]:
        """Runs a standard, parallel set of experiments.

        Executes a predefined number of trials for a specified list of agent
        variants. It supports both 'local' and 'ray' execution backends.

        Yields:
            A dictionary for each trial result.
        """
        experiments = self.orchestrator_config.get('standard_settings', {}).get('experiments', [])
        for experiment in experiments:
            if not experiment.get("enabled", False): continue

            print(f"\n--- Running Standard Experiment: {experiment['name']} ---")
            variants = experiment["variants"]
            trials_per_variant = experiment['trials_per_variant']

            exp_context = self.base_context.copy()
            if any("caching" in v for v in variants):
                exp_context["task_id"] = f"repeated_task_{uuid.uuid4()}"

            if self.execution_backend == "ray":
                if not ray or not run_trial_remote: raise ImportError("Ray backend is configured, but 'ray' is not installed.")

                pending_trials = [run_trial_remote.remote(v_name, exp_context) for _ in range(trials_per_variant) for v_name in variants]
                print(f"Dispatched {len(pending_trials)} trials to Ray cluster.")

                while pending_trials:
                    ready, pending_trials = ray.wait(pending_trials)
                    for res_id in ready:
                        try:
                            result = ray.get(res_id)
                            self._write_to_bus(result)
                            yield result
                        except Exception as e:
                            print(f"ERROR retrieving result from Ray worker: {e}")
            else:
                for _ in range(trials_per_variant):
                    for v_name in variants:
                        try:
                            result = run_trial(v_name, exp_context)
                            self._write_to_bus(result)
                            yield result
                        except Exception as e:
                            print(f"ERROR running trial for variant {v_name}: {e}")

    # --- Multi-Armed Bandit Logic ---
    def _run_mab(self) -> Generator[Dict[str, Any], None, None]:
        """Runs a Multi-Armed Bandit (MAB) experiment.

        Dynamically allocates trials to the best-performing agent variants
        over time based on the chosen MAB strategy (e.g., 'thompson_sampling').

        Yields:
            A dictionary for each trial result.
        """
        settings = self.orchestrator_config.get('mab_settings', {})
        strategy = settings.get('strategy', 'thompson_sampling')
        variants = settings.get('variants', [])
        total_trials = settings.get('total_trials', 100)
        scoring_weights = self.config.get('scoring_weights')

        performance = {v: {"score_sum": 0, "runs": 0} for v in variants} if strategy == "epsilon_greedy" else {v: {"mu": 0, "lambda": 1, "tau": 1} for v in variants}
        print(f"Running MAB experiment ({strategy}) for {total_trials} trials...")

        for i in range(total_trials):
            chosen_variant = self._select_mab_variant(variants, performance, strategy)
            context = self.base_context.copy()
            if "caching" in chosen_variant: context['task_id'] = 'mab_repeated_task'

            if self.execution_backend == "ray":
                if not ray or not run_trial_remote: raise ImportError("Ray backend is configured, but 'ray' is not installed.")
                trial_result = ray.get(run_trial_remote.remote(chosen_variant, context))
            else:
                trial_result = run_trial(chosen_variant, context)

            score = calculate_score(trial_result, scoring_weights)
            trial_result['score'] = score
            self._update_mab_performance(chosen_variant, score, performance, strategy)
            if (i+1) % 20 == 0: print(f"  ... completed MAB trial {i+1}/{total_trials}")
            self._write_to_bus(trial_result)
            yield trial_result

    def _select_mab_variant(self, variants: List[str], performance: Dict, strategy: str) -> str:
        """Selects the next variant to run in a MAB experiment.

        Args:
            variants: The list of variant names to choose from.
            performance: A dictionary tracking the performance of each variant.
            strategy: The MAB strategy to use ('epsilon_greedy' or
                      'thompson_sampling').

        Returns:
            The name of the chosen variant.
        """
        if strategy == "epsilon_greedy":
            if random.random() < self.orchestrator_config['mab_settings'].get('epsilon', 0.1): return random.choice(variants)
            avg_scores = {v: (p["score_sum"] / p["runs"]) if p["runs"] > 0 else 0 for v, p in performance.items()}
            return max(avg_scores, key=avg_scores.get)
        else: # thompson_sampling
            samples = {v: np.random.normal(p['mu'], 1. / np.sqrt(p['lambda'] * p['tau'])) for v, p in performance.items()}
            return max(samples, key=samples.get)

    def _update_mab_performance(self, variant: str, score: float, performance: Dict, strategy: str):
        """Updates the performance dictionary for a variant after a MAB trial.

        Args:
            variant: The name of the variant that was run.
            score: The score achieved by the variant in the trial.
            performance: The dictionary tracking performance metrics.
            strategy: The MAB strategy being used.
        """
        if strategy == "epsilon_greedy":
            performance[variant]["score_sum"] += score
            performance[variant]["runs"] += 1
        else: # thompson_sampling
            mu_n, lambda_n, alpha_n = performance[variant].get('mu',0), performance[variant].get('lambda',1), performance[variant].get('tau',1)
            lambda_new = lambda_n + 1
            mu_new = (lambda_n * mu_n + score) / lambda_new
            alpha_new = alpha_n + 0.5
            beta_new = 1 + 0.5 * (lambda_n * (score - mu_n)**2 / (lambda_n + 1))
            performance[variant].update({'mu': mu_new, 'lambda': lambda_new, 'tau': alpha_new / beta_new})

    # --- Bayesian Optimization Logic ---
    def _run_bayesian_optimization(self) -> Generator[Dict[str, Any], None, None]:
        """Runs a Bayesian Optimization experiment for hyperparameter tuning.

        Uses a Gaussian Process model to intelligently search a parameter
        space for a tunable agent variant to find the optimal configuration.

        Yields:
            A dictionary for each trial result.
        """
        if not Optimizer: raise ImportError("scikit-optimize is required for Bayesian Optimization.")

        settings = self.orchestrator_config.get('tuning_settings', {})
        variant_name = settings['variant']
        variant_class = TUNABLE_VARIANT_REGISTRY.get(variant_name)
        if not variant_class: raise ValueError(f"Tunable variant '{variant_name}' not found.")

        space, param_names = [], []
        for name, details in settings['parameter_space'].items():
            param_names.append(name)
            if details['type'] == 'int': space.append(Integer(details['range'][0], details['range'][1], name=name))
            elif details['type'] == 'float': space.append(Real(details['range'][0], details['range'][1], "log-uniform", name=name))
            elif details['type'] == 'categorical': space.append(Categorical(details['choices'], name=name))

        optimizer = Optimizer(dimensions=space, random_state=1, base_estimator="GP")
        total_configs = settings.get('total_configs', 50)
        trials_per_config = settings.get('trials_per_config', 5)
        scoring_weights = self.config.get('scoring_weights')

        print(f"Running Bayesian Optimization for '{variant_name}' over {total_configs} configurations...")

        for i in range(total_configs):
            params_list = optimizer.ask()
            params_dict = {name: val for name, val in zip(param_names, params_list)}
            print(f"\n[{i+1}/{total_configs}] Testing parameters: {params_dict}")

            agent_instance = variant_class(params=params_dict)
            context = self.base_context.copy()
            context["task_id"] = f"hpo_task_{uuid.uuid4()}"

            if self.execution_backend == "ray":
                if not ray or not run_trial_remote: raise ImportError("Ray backend is configured, but 'ray' is not installed.")
                # Note: Ray remote tasks cannot take class instances directly as arguments if the class is not defined on the worker.
                # A more robust implementation would pass the class name and params dict. For now, we assume local testing of this feature.
                trial_refs = [run_trial_remote.remote(agent_instance, context) for _ in range(trials_per_config)]
                trial_results = ray.get(trial_refs)
            else:
                trial_results = [run_trial(agent_instance, context) for _ in range(trials_per_config)]

            scores = []
            for trial_result in trial_results:
                score = calculate_score(trial_result, scoring_weights)
                trial_result['score'] = score
                trial_result['params'] = params_dict
                scores.append(score)
                self._write_to_bus(trial_result)
                yield trial_result

            optimizer.tell(params_list, -np.mean(scores))
            print(f"  ... Mean Score: {np.mean(scores):.4f}")

        print("\nBayesian Optimization finished.")
        best_params = {name: val for name, val in zip(param_names, optimizer.Xi[np.argmin(optimizer.yi)])}
        print(f"Best parameters found: {best_params} with score {-np.min(optimizer.yi):.4f}")

    # --- Adversarial Benchmark Logic ---
    def _run_adversarial_benchmark(self) -> Generator[Dict[str, Any], None, None]:
        """Runs an adversarial benchmark.

        First, it runs an "adversary" agent to generate a challenging or
        "poisoned" context. Then, it runs one or more "target" agents
        within that same context to measure their robustness.

        Yields:
            A dictionary for each trial result of the target agents.
        """
        settings = self.orchestrator_config.get('adversarial_settings', {})
        adversary_variant = settings.get('adversary_variant')
        target_variants = settings.get('target_variants')
        trials_per_target = settings.get('trials_per_target', 10)

        if not adversary_variant or not target_variants: raise ValueError("Adversarial benchmark requires 'adversary_variant' and 'target_variants'.")

        print(f"Running Adversarial Benchmark (Adversary: '{adversary_variant}')")

        for i in range(trials_per_target):
            print(f"\n--- Adversarial Trial {i+1}/{trials_per_target} ---")
            adversarial_context = run_trial(adversary_variant, self.base_context)

            for target_variant in target_variants:
                print(f"  - Testing '{target_variant}' against poisoned context...")
                try:
                    target_result = run_trial(target_variant, adversarial_context)
                    target_result['adversary'] = adversary_variant
                    target_result['adversarial_strategy'] = adversarial_context.get('adversarial_strategy')
                    self._write_to_bus(target_result)
                    yield target_result
                except Exception as e:
                    print(f"    ERROR running target {target_variant}: {e}")

    # --- Generative Adversarial Self-Improvement (GASI) Logic ---
    def _run_gasi(self) -> Generator[Dict[str, Any], None, None]:
        """Runs the full Generative Adversarial Self-Improvement (GASI) loop.

        This complex orchestration mode involves multiple phases per generation:
        1.  **Generation**: A new "challenger" agent is forged.
        2.  **Evaluation**: The challenger is benchmarked against the current
            champion. The winner becomes the new champion.
        3.  **Adversarial**: A new "adversary" agent is forged to target the
            new champion.
        4.  **Hardening**: The champion is tested against the new adversary.
        5.  **Self-Correction**: If the champion fails hardening, the system
            attempts to generate a code patch to "heal" it.

        Yields:
            A dictionary for each trial result across all phases.
        """
        print("\n--- INITIATING GENERATIVE ADVERSARIAL SELF-IMPROVEMENT RUN ---")
        settings = self.orchestrator_config.get('gasi_settings', {})
        num_generations = settings.get('generations', 3)

        agent_designer = AgentDesigner()
        code_generator = CodeGenerator()
        variants_dir = os.path.join(os.path.dirname(__file__), "..", "experiment_hub", "variants")

        current_champion = settings.get('initial_champion', 'collaborative_agent_team')
        current_adversaries = [v for v in self.config.get('variants', []) if 'adversarial' in v]
        gasi_fitness_profiles = {} # Tracks {variant: {general_score: float, robustness_score: float}}

        for gen in range(num_generations):
            print(f"\n--- GASI Generation {gen+1}/{num_generations} ---")

            # 1. Generation Phase: Forge a new "Blue Team" agent to challenge the champion
            print("  Phase 1: Forging new challenger agent...")
            new_spec = agent_designer.design_new_variant(existing_variants=[current_champion])
            code_generator.generate_and_write_code(new_spec, variants_dir)
            challenger_name = new_spec['name'].lower()

            # We need to re-import to register the new variant
            import importlib
            import meta_orchestrator.experiment_hub.variants
            importlib.reload(meta_orchestrator.experiment_hub.variants)

            # 2. Evaluation Phase: Benchmark challenger against the champion
            print(f"  Phase 2: Benchmarking '{challenger_name}' vs. champion '{current_champion}'...")
            eval_config = {
                'trials_per_variant': 20,
                'execution_backend': self.backend_config
            }
            eval_results = list(self._run_standard_internal([challenger_name, current_champion], eval_config))
            for res in eval_results: yield res # Yield results for live view

            # Determine the new champion using a weighted fitness score
            robustness_weight = settings.get('robustness_weight', 0.3)
            general_weight = 1.0 - robustness_weight

            # Get general performance scores from the last evaluation
            champ_general_score = np.mean([r['score'] for r in eval_results if r['variant'] == current_champion])
            challenger_general_score = np.mean([r['score'] for r in eval_results if r['variant'] == challenger_name])

            # Update profiles with general scores
            gasi_fitness_profiles.setdefault(current_champion, {})['general_score'] = champ_general_score
            gasi_fitness_profiles.setdefault(challenger_name, {})['general_score'] = challenger_general_score

            # Calculate fitness for the champion, using its robustness score from the *previous* generation
            # If no robustness score exists (e.g., first generation), it defaults to its general score
            champ_robustness_score = gasi_fitness_profiles[current_champion].get('robustness_score', champ_general_score)
            champ_fitness = (general_weight * champ_general_score) + (robustness_weight * champ_robustness_score)

            # The challenger has no robustness score yet, so its fitness is just its general score
            challenger_fitness = challenger_general_score

            print(f"  - Fitness check: '{current_champion}' (Fitness: {champ_fitness:.4f}) vs. '{challenger_name}' (Fitness: {challenger_fitness:.4f})")

            if challenger_fitness > champ_fitness:
                print(f"  *** New Champion Crowned: {challenger_name} (Fitness: {challenger_fitness:.4f}) ***")
                current_champion = challenger_name
            else:
                print(f"  Champion '{current_champion}' defended its title (Fitness: {champ_fitness:.4f}).")

            # 3. Adversarial Phase: Forge a new "Red Team" agent to defeat the champion
            print(f"  Phase 3: Forging new adversary to challenge '{current_champion}'...")
            adversary_spec = agent_designer.design_adversarial_variant()
            code_generator.generate_and_write_code(adversary_spec, variants_dir)
            adversary_name = adversary_spec['name'].lower()

            # Dynamically register the new adversary
            importlib.reload(meta_orchestrator.experiment_hub.variants)
            print(f"    - Adversary '{adversary_name}' has been generated and registered.")
            current_adversaries.append(adversary_name)

            # 4. Hardening Phase: Test champion against the new adversary
            print(f"  Phase 4: Hardening phase. Pitting '{current_champion}' against new adversary '{adversary_name}'...")
            hardening_trials = settings.get('hardening_trials_per_adversary', 10)

            hardening_results = []
            for _ in range(hardening_trials):
                adversarial_context = run_trial(adversary_name, self.base_context.copy())
                champion_result = run_trial(current_champion, adversarial_context)

                score = calculate_score(champion_result, self.config.get('scoring_weights'))
                champion_result['score'] = score
                champion_result['gasi_generation'] = gen + 1
                champion_result['run_type'] = 'hardening'
                champion_result['adversary'] = adversary_name

                hardening_results.append(champion_result)
                self._write_to_bus(champion_result)
                yield champion_result

            # Calculate and store the robustness score for the current champion.
            # This score will be used to calculate its fitness in the *next* generation.
            avg_hardening_score = np.mean([r['score'] for r in hardening_results]) if hardening_results else 0.0
            gasi_fitness_profiles[current_champion]['robustness_score'] = avg_hardening_score
            print(f"    - Hardening complete. Champion's average score against '{adversary_name}': {avg_hardening_score:.4f}")
            print(f"    - Updated robustness score for '{current_champion}' to be used in next generation.")

            # 5. Self-Correction Phase: If the champion failed the hardening, attempt to heal it.
            self_correction_settings = settings.get('self_correction', {})
            if self_correction_settings.get('enabled', False) and avg_hardening_score < self_correction_settings.get('hardening_failure_threshold', 0.1):
                print(f"  Phase 5: Self-Correction. Champion '{current_champion}' failed hardening (score {avg_hardening_score:.4f}).")

                code_healer = CodeHealer()
                # Assumption: variant name is lowercased class name, file is variant_name.py
                champion_source_path = os.path.join(variants_dir, f"{current_champion}.py")

                if not os.path.exists(champion_source_path):
                    print(f"    - ERROR: Cannot find source for '{current_champion}'. Skipping self-correction.")
                    continue

                with open(champion_source_path, 'r') as f:
                    original_source_code = f.read()

                failure_analysis = {"adversary": adversary_name, "score": avg_hardening_score}
                patched_source_code = code_healer.generate_patch(original_source_code, failure_analysis)

                if patched_source_code != original_source_code:
                    print("    - Patch generated. Creating and validating new agent version...")

                    # Brittle: find original class name to create a new one
                    original_class_name = next((line.split("class ")[1].split("(")[0].strip() for line in original_source_code.splitlines() if line.strip().startswith("class ")), None)

                    if not original_class_name:
                        print("    - ERROR: Could not determine original class name. Cannot apply patch.")
                        continue

                    patched_class_name = f"{original_class_name}_patched_{gen+1}"
                    patched_variant_name = patched_class_name.lower()

                    final_patched_code = patched_source_code.replace(f"class {original_class_name}", f"class {patched_class_name}", 1)

                    with open(os.path.join(variants_dir, f"{patched_variant_name}.py"), 'w') as f:
                        f.write(final_patched_code)

                    importlib.reload(meta_orchestrator.experiment_hub.variants)
                    print(f"    - Saved and registered new variant: '{patched_variant_name}'")

                    # Validate the patched agent against the same adversary
                    validation_results = []
                    for _ in range(self_correction_settings.get('validation_trials', 5)):
                        validation_context = run_trial(adversary_name, self.base_context.copy())
                        patched_result = run_trial(patched_variant_name, validation_context)
                        score = calculate_score(patched_result, self.config.get('scoring_weights'))
                        patched_result.update({'score': score, 'gasi_generation': gen + 1, 'run_type': 'validation', 'adversary': adversary_name})
                        validation_results.append(patched_result)
                        self._write_to_bus(patched_result)
                        yield patched_result

                    avg_validation_score = np.mean([r['score'] for r in validation_results]) if validation_results else 0.0
                    print(f"    - Validation complete. Patched agent score: {avg_validation_score:.4f}")

                    if avg_validation_score > avg_hardening_score:
                        print(f"    - SUCCESS: Patched agent improved performance and will be promoted.")
                        current_champion = patched_variant_name
                        # Update the fitness profile to reflect the successful patch
                        gasi_fitness_profiles[current_champion] = {
                            'general_score': avg_validation_score, # Use validation score as new baseline
                            'robustness_score': avg_validation_score
                        }
                        print(f"    - PROMOTION: '{current_champion}' is the new champion for the next generation.")
                    else:
                        print(f"    - FAILURE: Patch did not improve performance. Original champion '{original_class_name.lower()}' is retained.")
                else:
                    print("    - Code Healer did not produce a patch.")

        print("\n--- GASI Run Concluded ---")

    def _run_standard_internal(self, variants, config) -> Generator[Dict[str, Any], None, None]:
        """Internal helper to run a standard experiment, used by GASI.

        Args:
            variants: A list of variant names to run.
            config: A dictionary with configuration for the run, like
                    'trials_per_variant'.

        Yields:
            A dictionary for each trial result.
        """
        # This is a simplified version of the main _run_standard method for internal use
        trials_per_variant = config['trials_per_variant']
        exp_context = self.base_context.copy()
        for _ in range(trials_per_variant):
            for v_name in variants:
                result = run_trial(v_name, exp_context)
                score = calculate_score(result, self.config.get('scoring_weights'))
                result['score'] = score
                self._write_to_bus(result)
                yield result