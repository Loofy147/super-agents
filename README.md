# Meta-Orchestrator: A Self-Improving Agent System

The Meta-Orchestrator is a framework designed to automatically test, measure, and optimize a system of AI agents. It implements a Generative Adversarial Self-Improvement (GASI) loop, where agents are continuously challenged by purpose-built adversaries, and the system attempts to autonomously "heal" the agents that fail.

## Core Concepts

*   **Generative Adversarial Self-Improvement (GASI)**: The core loop of the system. A "champion" agent is selected and pitted against a new, adversarially-designed agent. If the champion fails, the system attempts to patch its code.
*   **Agent Forge**: A module (`agent_forge/`) that programmatically designs and generates source code for new agent variants, including specialized adversarial agents.
*   **Self-Correction / Code Healing**: When an agent fails a "hardening" trial, the `CodeHealer` module analyzes the failure and uses an LLM (simulated in the current version) to generate a code patch.
*   **Experiment Orchestration**: The `UnifiedOrchestrator` manages the entire GASI loop, from agent generation to trial execution and self-correction.

## Getting Started

### Prerequisites

*   Python 3.8+
*   `pip` for package management

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd meta-orchestrator
    ```

2.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Configuration

The entire system is controlled by the `config.yaml` file. Here you can define:
*   The type of orchestrator to use.
*   Settings for the GASI loop, such as the failure threshold for self-correction.
*   Parameters for agent design and generation.

## Usage

### Running an Experiment

To run the default GASI experiment, use the command-line interface (CLI):

```bash
python -m meta_orchestrator.cli --config config.yaml
```

Experiment results, including a summary report and raw JSON data, will be saved to a timestamped directory inside `meta_orchestrator/results/`.

### Interactive Dashboard

The project includes an interactive dashboard built with Streamlit to visualize experiment results. To run it:

```bash
streamlit run meta_orchestrator/dashboard/app.py
```
