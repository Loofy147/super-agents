# Production-Grade System Architecture Roadmap

This document outlines the vision and technical roadmap for evolving the `meta-orchestrator` into a production-grade, scalable, and continuously integrated system. These features focus on moving from a local, single-machine tool to a robust MLOps-style framework for professional AI agent evaluation and benchmarking.

---

## Feature 1: Real-Time Dashboard & Visualization Engine

**Concept:** Replace the static, post-experiment `summary.md` report with a live, interactive web-based dashboard. This provides immediate insights into experiment progress and allows for dynamic exploration of results.

**Objective:** To create a rich, user-friendly interface for launching, monitoring, and analyzing experiments, making the entire process more transparent and engaging.

### Proposed Implementation

1.  **Integrate a Dashboarding Library:**
    -   Add a dependency for a library like `Streamlit` or `Dash` to `pyproject.toml`. Streamlit is often faster for initial development.
    -   Create a new entry point file, `dashboard/app.py`, that will contain the dashboard code.

2.  **Redesign Data Flow for Real-Time Updates:**
    -   The current architecture saves results only at the very end of a run. To enable real-time updates, the orchestrators must be modified to yield results after each trial.
    -   A lightweight database (like `SQLite`) or a simple file-based logging mechanism could be used to stream trial-level results from the orchestrator process to the dashboard process.

3.  **Key Dashboard Components:**
    -   **Experiment Launcher:** A form at the top of the dashboard to select a `config.yaml` file and launch a new experiment run.
    -   **Live Run View:**
        -   **Score vs. Time Plot:** A line chart showing the mean score of each variant as the experiment progresses.
        -   **MAB Choice Distribution:** For MAB orchestrators, a bar chart that updates in real-time, showing how many times the bandit has chosen each variant.
        -   **Live Log Stream:** A text area that tails the `stdout` of the experiment run.
    -   **Historical Run Browser:** A sidebar allowing users to select and view the final results of any past experiment run from the `results/` directory.

4.  **Create a New CLI Command:**
    -   A new command will be added to launch the web application.
    ```bash
    python -m meta_orchestrator.cli dashboard
    ```
    -   This command will simply execute `streamlit run dashboard/app.py`.

### Actionable Next Steps

1.  **Add `streamlit` Dependency:** Add the library to the project's dependencies.
2.  **Refactor Orchestrators:** Modify the orchestrator `run` methods to be generators, `yield`ing each trial result as it completes.
3.  **Implement `dashboard/app.py`:** Build the initial dashboard layout with a historical run browser.
4.  **Implement Real-Time Updates:** Add the live monitoring components and the data streaming logic to connect the running orchestrator to the dashboard.
5.  **Update `cli.py`:** Add the new `dashboard` command.

---

## Feature 2: Scalable, Distributed Execution Backend

**Concept:** Evolve the experiment execution from a single-process, sequential operation into a distributed system capable of running thousands of trials in parallel across a cluster of machines.

**Objective:** To enable massive-scale experiments that would be prohibitively slow on a single machine, allowing for more thorough hyperparameter searches, more robust statistical results, and the testing of more complex, time-intensive agents.

### Proposed Implementation

1.  **Integrate a Distributed Computing Framework:**
    -   Add a dependency for a framework like `Ray` or `Dask` to `pyproject.toml`. Ray is particularly well-suited for this kind of workload.
    -   The core idea is to convert the `run_trial` function into a "remote task" that can be scheduled by the distributed framework.

2.  **Refactor Core Execution Logic:**
    -   **`run_trial` as a Remote Function:** Decorate the `run_trial` function with `@ray.remote`. This tells Ray that this function can be executed on any machine in the cluster.
    -   **Asynchronous Orchestrators:** The orchestrator classes will need to be updated to work asynchronously. Instead of calling `run_trial` and waiting for the result, they will call `run_trial.remote()` which immediately returns a future or object reference.
    -   The orchestrator will then use `ray.wait()` to efficiently wait for the next available result from the cluster, allowing it to process results and dispatch new trials continuously.

3.  **Configuration-Managed Backend:**
    -   The `config.yaml` file will be updated to allow the user to select and configure the execution backend.

    ```yaml
    # Example config.yaml for distributed execution
    execution_backend:
      type: "ray" # Options: "local", "ray"
      ray_settings:
        address: "auto" # or "my-ray-cluster-head:6379"
        num_cpus: 16
    ```

### Actionable Next Steps

1.  **Add `ray` Dependency:** Add the library to the project's dependencies.
2.  **Refactor `run_trial`:** Decorate the function with `@ray.remote`.
3.  **Create an `AsyncOrchestrator` Base Class:** Design a new base class or modify the existing one to handle the asynchronous dispatching and collection of trial results from Ray futures.
4.  **Update `hub.py`:** Modify the main `run_experiment_suite` function to initialize and shut down the connection to the distributed backend based on the `execution_backend` configuration.

---

## Feature 3: CI/CD Performance Guardrails

**Concept:** Integrate the experiment runner directly into the Continuous Integration/Continuous Deployment (CI/CD) pipeline to automatically benchmark every proposed code change. This provides a safety net against performance regressions.

**Objective:** To ensure that all code merged into the main branch is not only correct (passes unit tests) but also meets a high performance standard. This creates a historical record of performance over time and makes performance a shared responsibility.

### Proposed Implementation

1.  **Create a CI Workflow File:**
    -   Add a new workflow file (e.g., `.github/workflows/performance_benchmark.yml`) for a CI provider like GitHub Actions.
    -   This workflow will be configured to trigger on every pull request that modifies files within `meta_orchestrator/experiment_hub/variants/`.

2.  **Standardized Benchmark Configuration:**
    -   Create a dedicated `benchmark_config.yaml` file in the repository. This config will define a standardized, fast-running experiment that serves as the official performance benchmark for all variants.
    -   The CI job will exclusively use this config file to ensure consistent and comparable results across runs.

3.  **Automated PR Commenting:**
    -   The CI workflow will execute the `meta_orchestrator` with the benchmark config.
    -   After the run completes, the workflow will take the generated `summary.md` and post its contents as a comment on the pull request. This provides immediate, visible feedback to the developer and reviewers.

4.  **Performance Budget & Automated Checks:**
    -   To fully automate the guardrail, a "performance budget" can be implemented.
    -   The CI workflow will:
        1.  Fetch the benchmark results from the `main` branch.
        2.  Run the benchmark on the pull request branch.
        3.  Compare the `mean_score` of the modified agent from the two runs.
        4.  If the new score represents a statistically significant regression (e.g., using a t-test), the CI job will fail, blocking the merge.

### Actionable Next Steps

1.  **Create `benchmark_config.yaml`:** Define and commit the standard benchmark experiment configuration.
2.  **Write the CI Workflow (`performance_benchmark.yml`):** Implement the logic for checking out the code, running the benchmark, and posting the results to the PR. This can be done using existing GitHub Actions marketplace actions.
3.  **Implement the Performance Budget Logic:** Add a script to the repository that can be called from the CI workflow to perform the statistical comparison between the PR results and the main branch results, exiting with an error code if the budget is exceeded.