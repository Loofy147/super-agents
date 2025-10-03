# Meta-Orchestrator Challenge

This project is a complete, runnable implementation of the "Meta-Orchestrator Challenge." It provides a self-improving agent system designed to automatically run experiments on different AI agent "variants," measure their performance across multiple dimensions (cost, latency, success, autonomy), and use statistical methods to determine the best-performing variant.

## Project Structure

The project is organized as a standard Python package for clarity and extensibility.

```
meta_orchestrator/
├── ADR.md                    # Architecture Decision Record
├── README.md                 # This file
├── core/
│   └── interpreter.py        # Mock interpreter with caching primitives
├── experiment_hub/
│   ├── hub.py                # Main script to run experiments
│   ├── registry.py           # Centralized registry for discovering variants
│   ├── scoring.py            # Logic for scoring experiment results
│   └── variants/             # Directory for different agent implementations
│       ├── caching_agent.py  # A stateful agent that uses a cache
│       └── in_memory.py      # Simple stateless agents
├── results/
│   └── latest_run.json       # Output of the last experiment run
├── simulations/
│   └── adaptive_sim.py       # Simulates Epsilon-Greedy vs. Thompson Sampling
└── tests/
    ├── test_unit.py          # Unit tests for individual components
    ├── test_contract.py      # Integration test for the experiment pipeline
    └── chaos.sh              # Chaos test to verify resilience under load
```

## How to Use

### 1. Installation

The project requires Python 3 and has one external dependency.

First, install `numpy`:
```bash
pip install numpy
```

### 2. Running Experiments

To run the main experiment hub, which executes all registered agent variants and generates a scored analysis, run the following command from the repository root:

```bash
python3 -m meta_orchestrator.experiment_hub.hub
```
The results will be printed to the console and saved in `meta_orchestrator/results/latest_run.json`.

### 3. Running Adaptive Allocation Simulations

To simulate and compare the `Epsilon-Greedy` and `Thompson Sampling` learning algorithms, run:

```bash
python3 meta_orchestrator/simulations/adaptive_sim.py
```
This script runs against a mock environment and demonstrates how the algorithms learn to prefer the optimal agent variant over time.

### 4. Running Tests

The project includes a comprehensive, multi-layered test suite.

**To run all unit and contract tests:**
```bash
python3 -m unittest discover meta_orchestrator/tests/
```

**To run the chaos test (verifies resilience under load):**
```bash
./meta_orchestrator/tests/chaos.sh
```

All tests are expected to pass on a standard system.