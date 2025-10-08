# Advanced Experimentation & Causal Analysis Roadmap

This document outlines the vision and technical roadmap for the next generation of experimentation capabilities within the `meta-orchestrator`. These features move beyond simple A/B testing of static variants and introduce concepts of auto-tuning, closed-loop learning, and deep causal analysis.

---

## Feature 1: Auto-Tuning Variants & Hyperparameter Optimization

**Concept:** Extend the orchestrator's role from simply selecting the best *static* variant to finding the optimal *internal parameters* for a single, more complex agent. This turns hyperparameter tuning into a first-class, automated experiment.

**Objective:** To enable the system to automatically optimize the performance of a configurable agent by intelligently searching its parameter space. For example, finding the ideal cache size for a `CachingAgent` or the optimal planning depth for a future `PlanningAgent`.

### Proposed Implementation

1.  **Introduce a `TunableAgentVariant` Base Class:**
    -   Create a new abstract base class, `TunableAgentVariant`, that inherits from `AgentVariant`.
    -   Its `__init__` method will accept a dictionary of parameters. The `run` method will then use these parameters to alter its behavior.
    -   This creates a clear contract for agents that are designed to be tuned.

2.  **Define a Parameter Space in `config.yaml`:**
    -   The configuration for a tuning experiment would specify the `tunable_variant` and its `parameter_space`.

    ```yaml
    # Example config.yaml for an auto-tuning experiment
    orchestrator:
      type: "bayesian_optimization"
      tuning_settings:
        variant: "tunable_caching_agent"
        total_trials: 100
        # Define the search space for the optimizer
        parameter_space:
          cache_size: { type: "int", range: [10, 1000] }
          default_ttl: { type: "float", range: [0.5, 60.0] }
          strategy: { type: "categorical", choices: ["LRU", "FIFO"] }
    ```

3.  **Implement a `BayesianOptOrchestrator`:**
    -   Create a new orchestrator that uses a Bayesian Optimization library (e.g., `scikit-optimize` or `hyperopt`).
    -   **Loop:**
        1.  The orchestrator asks the Bayesian Optimizer for the next set of promising parameters (e.g., `{'cache_size': 256, 'default_ttl': 30.0, 'strategy': 'LRU'}`).
        2.  It instantiates the `TunableAgentVariant` with these parameters.
        3.  It runs a small number of trials with this configured agent to get a stable performance score.
        4.  It reports the score back to the optimizer (`optimizer.tell(params, score)`).
        5.  The optimizer updates its internal model and the loop repeats.

4.  **Enhance Reporting:**
    -   The final `summary.md` would not just rank agents, but would report the optimal parameters found and the resulting performance score.
    -   *Example Report Section:* "Optimal parameters for `tunable_caching_agent` found after 100 trials: `{'cache_size': 312, 'default_ttl': 22.5, 'strategy': 'LRU'}` with a mean score of `0.987`."

### Actionable Next Steps

1.  **Add a Bayesian Optimization Library:** Add a dependency like `scikit-optimize` to `pyproject.toml`.
2.  **Implement `TunableAgentVariant`:** Create the base class and a `TunableCachingAgent` as a reference implementation.
3.  **Implement `BayesianOptOrchestrator`:** Build the new orchestrator to manage the optimization loop.
4.  **Update Reporting:** Modify `scoring.py` to generate the new report section for tuning results.

---

## Feature 2: Closed-Loop Experimentation & Automated Hypothesis Generation

**Concept:** Create a "meta-learning" loop where the orchestrator can analyze the results of an experiment run and automatically propose a follow-up experiment to investigate interesting findings. This moves the system from a passive tool to an active research assistant.

**Objective:** To accelerate the pace of discovery by automating the "what should we test next?" process. The system should be able to spot anomalies or promising results and generate a new, focused experiment to explore them further.

### Proposed Implementation

1.  **Introduce an `AnalysisModule`:**
    -   Create a new module, `analysis/post_hoc_analyzer.py`, responsible for deep analysis of a completed experiment run.
    -   This module would contain functions to identify specific patterns in the results data, such as:
        -   **High Variance Detector:** Finds variants whose performance is highly inconsistent (large `score_std_dev`). This suggests the agent's performance is sensitive to some hidden variable.
        -   **Outlier Detector:** Finds trials that were significant outliers from the mean performance.
        -   **Subgroup Specialist Detector:** If task metadata is available, this could find agents that excel at a specific *type* of task (e.g., `agent_A` is best for "code generation" while `agent_B` is best for "data analysis").

2.  **Implement a `ConfigGenerator`:**
    -   Based on the findings from the `AnalysisModule`, a `ConfigGenerator` would create a new `config.yaml` file for a follow-up experiment.
    -   *Example Workflow:*
        1.  `AnalysisModule` detects that `variant_C` has very high variance.
        2.  `ConfigGenerator` creates `config.follow_up_variance.yaml`.
        3.  This new config defines an experiment that runs `variant_C` for a much larger number of trials (`trials_per_variant: 500`) to get a more stable measurement of its true performance.

3.  **Create a New CLI Command:**
    -   The entire process would be exposed through a simple CLI command:
    ```bash
    python -m meta_orchestrator.cli suggest-next-run --run-dir meta_orchestrator/results/run_20251007_180600
    ```
    -   This command would execute the analysis and, if interesting findings are made, generate the new configuration file and print its location to the user.

### Actionable Next Steps

1.  **Implement the `AnalysisModule`:** Create the new module and implement the first analysis function (e.g., the `HighVarianceDetector`).
2.  **Implement the `ConfigGenerator`:** Create the logic for programmatically building and saving a valid YAML configuration file.
3.  **Update `cli.py`:** Add the new `suggest-next-run` command and wire it to the analysis and generation modules.
4.  **Expand Analysis Rules:** Continuously add more sophisticated analysis rules to the `AnalysisModule` over time.

---

## Feature 3: Causal Analysis & Insight Reporting

**Concept:** Move beyond observing correlations in data to determining causation. Instead of just noting that the `caching_agent` has lower latency, we want to prove that the lower latency is *caused by* the cache hits, while controlling for other factors.

**Objective:** To generate high-confidence, actionable insights about *why* an agent variant succeeds or fails. This provides a much deeper level of understanding than standard statistical analysis.

### Proposed Implementation

1.  **Integrate a Causal Inference Library:**
    -   Add a powerful library like `DoWhy` to the project's dependencies. This provides the core engine for modeling causal relationships and estimating their effects.

2.  **Instrument Variants for Causal Data:**
    -   To perform causal analysis, we need to explicitly log "treatments," "outcomes," and "confounders." This requires a minor change in how variants report results.
    -   *Example:* The `caching_agent` already logs `"was_cached": True/False`. This is the **treatment**. The `"latency_internal_s"` is the **outcome**. The `run_trial` function would need to ensure this data is structured correctly for the analysis module.

3.  **Create a `CausalAnalysis` Module:**
    -   This new module (`analysis/causal_analyzer.py`) would be responsible for performing the causal inference after an experiment run.
    -   **Workflow:**
        1.  **Model:** Define a causal graph for the known variables (e.g., `was_cached -> latency_internal_s`). This can be encoded programmatically.
        2.  **Identify:** Use `DoWhy` to identify the causal estimand based on the graph.
        3.  **Estimate:** Use a statistical method (e.g., linear regression, propensity score matching) to estimate the identified causal effect.
        4.  **Refute:** Run automated checks to test the robustness of the finding.

4.  **Enhance Reporting with Causal Insights:**
    -   The most important step is to translate the statistical result into a human-readable insight in the `summary.md` report.
    -   A new "Causal Insights" section would be added to the report.
    -   *Example Report Section:*
        > **Causal Insight for `caching_agent`:**
        > - We found a **causally significant** relationship between cache hits and latency.
        > - **Finding:** A cache hit (`was_cached: True`) **causes** an estimated **-0.13s reduction** in mean latency, holding other factors constant.
        > - *Confidence: High (passed 2/2 refutation tests).*

### Actionable Next Steps

1.  **Add `dowhy` Dependency:** Add the library to `pyproject.toml` and `requirements.txt`.
2.  **Implement `CausalAnalysis` Module:** Create the new module and implement the workflow for the `caching_agent` as the first use case.
3.  **Standardize Causal Logging:** Define a clear data format for how variants should log treatments and outcomes.
4.  **Update Reporting:** Modify `scoring.py` to call the `CausalAnalysis` module and append the generated insights to the `summary.md` report.