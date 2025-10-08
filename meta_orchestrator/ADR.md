# Architecture Decision Record: Meta-Orchestrator

This document records the architectural decisions for the Meta-Orchestrator project.

## 1. Modular, Package-Based Structure

**Decision:** The project is structured as a standard Python package (`meta_orchestrator`).
**Consequences:** Clear separation of concerns, enables relative imports, and simplifies testing.

## 2. Centralized Variant Registry

**Decision:** A centralized, singleton `REGISTRY` object and a `register` decorator are used for discovering and managing agent variants.
**Rationale:** This design avoids circular dependencies and provides a single source of truth for available variants, making the system highly extensible.

## 3. Decoupled Simulation and Experimentation

**Decision:** The original adaptive allocation algorithms were implemented in a separate `simulations` module against a mock environment.
**Rationale:** This allowed for rapid, low-cost testing of the core learning strategies. This simulation has now been evolved into the `MultiArmedBanditOrchestrator`.

## 4. Comprehensive, Multi-Layered Testing Strategy

**Decision:** The project includes unit, contract, and chaos tests.
**Rationale:** This multi-layered approach ensures robustness, catches both granular logic errors and integration issues, and provides a baseline for system stability.

---
*The following decisions were made during the v2.0 overhaul.*
---

## 5. Configuration-Driven Experiments via YAML

**Decision (New):** All experiment parameters, including orchestrator selection, variant lists, trial counts, and scoring weights, have been externalized from the Python code into a single `config.yaml` file.

**Rationale:** The initial implementation had hardcoded experiment setups in `hub.py`. This made it inflexible and required code changes for any adjustments. A YAML-based configuration makes the system far more flexible, allowing users to define complex experiment suites without touching the source code.

**Consequences:**
*   **Pros:**
    *   Complete separation of configuration from code.
    *   Users can easily define, enable/disable, and modify experiments.
    *   Centralizes all tunable parameters in one place.
*   **Cons:**
    *   Adds a dependency on `PyYAML`.
    *   Requires careful validation of the configuration file format.

## 6. Formal `AgentVariant` Abstract Base Class

**Decision (New):** An abstract base class, `core.base_variant.AgentVariant`, was introduced to define a formal contract for all agent implementations. All variants now inherit from this class.

**Rationale:** The original implementation relied on an informal contract where variants were simply functions. While simple, this could lead to inconsistencies. The `AgentVariant` ABC ensures all variants have a consistent interface (`run` method) and are callable, making them compatible with the registry while providing a more robust and object-oriented structure.

**Consequences:**
*   **Pros:**
    *   Enforces a clear, consistent API for all agents.
    *   Improves code clarity and maintainability.
    *   Enables static analysis and better IDE support.

## 7. Pluggable Orchestration Layer

**Decision (New):** The main experiment loop in `hub.py` was refactored into a pluggable orchestration layer. An abstract `BaseOrchestrator` was created, with two initial implementations: `StandardOrchestrator` and `MultiArmedBanditOrchestrator`.

**Rationale:** This refactoring decouples the *what* (the agents) from the *how* (the trial allocation strategy). It elevates the adaptive allocation logic from a simulation to a first-class component of the experiment engine, allowing users to choose the best strategy for their needs via the `config.yaml`.

**Consequences:**
*   **Pros:**
    *   Highly flexible; new orchestration strategies can be added easily.
    *   Promotes separation of concerns.
    *   Allows for more sophisticated experiment designs (e.g., A/B testing vs. MAB optimization).

## 8. Automated, Human-Readable Reporting

**Decision (New):** In addition to raw `results.json`, each experiment run now automatically generates a `summary.md` file. This file provides a human-readable analysis of the results, including a ranked table of variants.

**Rationale:** Raw JSON is difficult to interpret quickly. The Markdown report makes the results immediately accessible and understandable to a wider audience, including non-developers. Saving each run in a timestamped directory prevents results from being overwritten.

**Consequences:**
*   **Pros:**
    *   Greatly improves the usability and actionability of experiment results.
    *   Provides a persistent, shareable artifact for each run.
    *   Robustly archives all historical run data.

## 9. Experimental Code Modernizer Feature

**Decision (New):** An experimental `code_modernizer` module was added. It uses Python's `ast` module to analyze the project's own source code and suggest improvements (e.g., use f-strings, add type hints).

**Rationale:** This is a "cutting-edge" feature that aligns with the project's theme of meta-analysis. It provides a built-in tool for maintaining and improving code quality over time, showcasing the potential for the system to reason not just about agents, but about its own implementation.

**Consequences:**
*   **Pros:**
    *   Introduces a novel, self-improvement capability.
    *   Can help enforce coding standards and best practices automatically.
*   **Cons:**
    *   Currently based on a simple, rule-based engine.
    *   Is experimental and not part of the core experiment workflow.