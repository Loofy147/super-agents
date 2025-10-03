# Architecture Decision Record: Meta-Orchestrator

This document records the architectural decisions for the Meta-Orchestrator project, built to fulfill the "Meta-Orchestrator Challenge."

## 1. Modular, Package-Based Structure

**Decision:** The project is structured as a standard Python package (`meta_orchestrator`). This decision was made to leverage Python's native module system for clear organization, dependency management, and extensibility.

**Consequences:**
*   **Pros:**
    *   Clear separation of concerns (core logic, experiment hub, simulations, tests).
    *   Enables relative imports, making the codebase self-contained and portable.
    *   Simplifies testing, as components can be tested in isolation.
*   **Cons:**
    *   Requires careful management of `__init__.py` files and package paths to avoid import errors.

## 2. Centralized Variant Registry

**Decision:** A centralized, singleton `REGISTRY` object, located in its own `experiment_hub/registry.py` module, is used for discovering and managing agent variants. The `register` decorator is also part of this module.

**Rationale:** An initial implementation where the registry and register function were in `hub.py` led to circular dependencies and module scope errors when variants tried to register themselves. A central, standalone module breaks this cycle and ensures all parts of the application interact with the same registry instance.

**Consequences:**
*   **Pros:**
    *   Eliminates circular dependencies.
    *   Provides a single, reliable source of truth for available variants.
    *   Makes the system highly extensible: adding a new variant only requires creating a new file in the `variants` directory; no changes to the hub are needed.
*   **Cons:**
    *   Slightly increases the number of modules, but the clarity gained outweighs this.

## 3. Decoupled Simulation and Experimentation

**Decision:** The adaptive allocation algorithms (`epsilon-greedy`, `Thompson Sampling`) are implemented in a separate `simulations` module, distinct from the `experiment_hub`. The simulations run against a mock environment, not the live experiment variants.

**Rationale:** This separation allows for the rapid testing and comparison of allocation algorithms without the overhead (latency, cost) of running the actual agent variants. It provides a clean environment to validate the core logic of the learning strategies.

**Consequences:**
*   **Pros:**
    *   Fast and cheap to run allocation algorithm comparisons.
    *   Decouples the development of learning strategies from the development of agent implementations.
*   **Cons:**
    *   Relies on the mock environment accurately reflecting the characteristics of the real variants. The fidelity of the simulation is key.

## 4. Comprehensive, Multi-Layered Testing Strategy

**Decision:** The project includes three distinct layers of automated tests:
1.  **Unit Tests (`test_unit.py`):** Verify the correctness of individual functions and classes in isolation (e.g., `calculate_score`, `Interpreter` caching).
2.  **Contract Tests (`test_contract.py`):** Verify the end-to-end pipeline of the Experiment Hub, ensuring all components interact correctly and their data contracts are met.
3.  **Chaos Tests (`chaos.sh`):** Verify the system's basic resilience by running the experiment hub under a light CPU load.

**Rationale:** A multi-layered approach ensures robustness. Unit tests catch granular logic errors, contract tests prevent integration issues, and chaos tests provide a baseline for system stability under stress.

**Consequences:**
*   **Pros:**
    *   High confidence in the correctness and stability of the codebase.
    *   Provides a safety net for future refactoring and feature additions.
*   **Cons:**
    *   Requires more initial development time to create and maintain the tests.