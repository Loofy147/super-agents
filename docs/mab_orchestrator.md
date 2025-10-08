# Multi-Armed Bandit (MAB) Orchestrator

The `meta-orchestrator` includes an advanced `MultiArmedBanditOrchestrator` that provides a more efficient way to run experiments compared to the `StandardOrchestrator`. This document explains the concept, the available strategies, and how to configure it.

## What is a Multi-Armed Bandit?

A Multi-Armed Bandit (MAB) is a class of algorithms that helps solve the "explore-exploit" dilemma. In the context of our system, each "arm" of the bandit is an **agent variant**.

- **Exploration:** The process of trying out different variants to gather data on how well they perform. This is necessary to avoid prematurely settling on a suboptimal variant.
- **Exploitation:** The process of using the variant that currently seems to be the best, based on the data gathered so far. This maximizes the immediate reward (or score).

The MAB orchestrator automatically balances this trade-off. Instead of running a fixed number of trials for every variant, it dynamically allocates more trials to the variants that are performing better, while still occasionally exploring other variants to ensure it doesn't miss a potentially better option. This is especially useful when you have many variants and a limited budget or time for experimentation.

## Available Strategies

The `MultiArmedBanditOrchestrator` currently supports two popular MAB strategies:

### 1. Epsilon-Greedy

This is a simple yet effective strategy.
- With a probability of `(1 - epsilon)`, it chooses the best-performing variant so far (exploitation).
- With a probability of `epsilon`, it chooses a random variant (exploration).

The `epsilon` value is configurable (typically a small number like 0.1) and controls the trade-off. A higher epsilon means more exploration.

### 2. Thompson Sampling

This is a more sophisticated, Bayesian approach. It models the performance of each variant not as a single number, but as a probability distribution.
- For each trial, it draws a random sample from each variant's performance distribution.
- It then chooses the variant whose sample was the highest.

This naturally balances exploration and exploitation. Variants with high uncertainty (i.e., fewer trials) will have wider distributions, giving them a chance to be selected even if their current mean performance is lower. As more data is collected, the distributions become narrower and the orchestrator becomes more confident in the best-performing variant.

In our implementation, we model the distribution of the variant's overall **score**, not just its success rate.

## How to Configure the MAB Orchestrator

To use the MAB orchestrator, you need to update your `config.yaml` file.

1. **Set the `orchestrator.type` to `"mab"`**.
2. **Configure the `mab_settings` section.**

### Example Configuration:

```yaml
# In config.yaml

orchestrator:
  type: "mab"  # Use the Multi-Armed Bandit orchestrator

  mab_settings:
    # The MAB strategy to use.
    # Options: "thompson_sampling" or "epsilon_greedy"
    strategy: "thompson_sampling"

    # The total number of trials the MAB is allowed to run.
    # It will automatically distribute these trials among the variants.
    total_trials: 500

    # The list of all variants that the MAB can choose from.
    variants:
      - "in_memory_probe"
      - "slower_reliable_probe"
      - "caching_agent"
      - "my_other_agent"

    # Epsilon value, only used if strategy is "epsilon_greedy".
    epsilon: 0.1

# Scoring weights are still used to calculate the score for each trial
scoring_weights:
  autonomy: 0.4
  success: 0.35
  cost: -0.15
  latency: -0.1
```

When you run the experiment hub with this configuration, the system will use the Thompson Sampling strategy to run a total of 500 trials, dynamically deciding whether to run `in_memory_probe`, `slower_reliable_probe`, or `caching_agent` for each trial. The final report will show how many times each variant was chosen and its overall performance.