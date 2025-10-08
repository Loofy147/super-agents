# Meta-Orchestrator Architecture

This document provides a high-level overview of the `meta-orchestrator` system architecture. The system is designed to be a modular, extensible, and configurable framework for running experiments on AI agent variants.

## Core Principles

- **Modularity:** Each component (orchestrator, agent variant, scoring) is designed to be self-contained and easily replaceable.
- **Extensibility:** The system is built to be easily extended with new agent variants, orchestration strategies, and scoring metrics.
- **Configurability:** All experiment parameters, from agent selection to scoring weights, are managed through a central `config.yaml` file, eliminating hardcoded values.

## System Components

The system is composed of several key components that work together to run experiments and analyze results.

```
/
├── config.yaml                 # Central configuration for all experiments
├── meta_orchestrator/
│   ├── core/
│   │   ├── base_variant.py     # Abstract base class for all agent variants
│   │   └── interpreter.py      # Mock interpreter with stateful primitives (caching)
│   ├── experiment_hub/
│   │   ├── hub.py              # Main entry point for running experiment suites
│   │   ├── registry.py         # Decorator-based registry for discovering variants
│   │   ├── scoring.py          # Logic for scoring results and generating reports
│   │   └── variants/           # Directory for all agent variant implementations
│   ├── orchestrators/
│   │   └── mab_orchestrator.py # Contains orchestration strategies (Standard, MAB)
│   ├── code_modernizer/
│   │   └── modernizer.py       # (Experimental) Analyzes code for improvements
│   └── results/                # Output directory for all experiment runs
└── docs/                       # System documentation
```

### 1. Configuration (`config.yaml`)

This file is the single source of truth for experiment configuration. It defines:
- The **orchestrator** to use (`standard` or `mab`).
- The **experiments** to run, including which variants to test and for how many trials.
- The **scoring weights** used to calculate the final score for each variant.

### 2. Experiment Hub (`experiment_hub/`)

This is the heart of the system.
- **`hub.py`**: Reads the `config.yaml`, selects the appropriate orchestrator, and drives the experiment run. It also coordinates the analysis and saving of results.
- **`registry.py`**: Implements a simple but powerful decorator (`@register`) that allows new agent variants to be automatically discovered by the system.
- **`scoring.py`**: Contains the logic for calculating a weighted score for each trial and aggregating these scores into a final analysis. It is also responsible for generating the final `summary.md` report.
- **`variants/`**: This package contains all the different agent implementations. Each variant is a class that inherits from `AgentVariant`.

### 3. Core (`core/`)

This module contains the fundamental building blocks of the system.
- **`base_variant.py`**: Defines the `AgentVariant` abstract base class. This enforces a consistent interface for all agent implementations, ensuring they are compatible with the orchestration engine.
- **`interpreter.py`**: A mock interpreter that provides stateful services to agents, such as a cache. This allows for the testing of more complex, stateful agents.

### 4. Orchestrators (`orchestrators/`)

This module defines the different strategies for running experiments.
- **`mab_orchestrator.py`**:
    - **`StandardOrchestrator`**: The default strategy, which runs a fixed number of trials for each specified variant.
    - **`MultiArmedBanditOrchestrator`**: An advanced strategy that uses algorithms like Epsilon-Greedy or Thompson Sampling to dynamically allocate trials to the most promising variants, making the experiment process more efficient.

### 5. Code Modernizer (`code_modernizer/`)

An experimental, meta-level feature.
- **`modernizer.py`**: Contains the `CodeModernizer` class, which can inspect the project's own source code using Abstract Syntax Trees (AST) to suggest modernizations, such as converting to f-strings or adding type hints.

## Data Flow

1. The main entry point (`hub.py` or `cli.py`) loads the `config.yaml`.
2. Based on the config, an **Orchestrator** is selected.
3. The Orchestrator runs a series of trials. For each trial:
    a. It selects an **Agent Variant** from the `REGISTRY`.
    b. It calls the variant, passing a `context` dictionary which may contain the `Interpreter`.
    c. The variant runs its logic and returns a dictionary of performance metrics.
4. The results from all trials are passed to the **`scoring.py`** module.
5. `scoring.py` calculates aggregate statistics and generates a `summary.md` report.
6. The raw results (`results.json`) and the summary report are saved to a unique, timestamped directory in `results/`.