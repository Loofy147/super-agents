# Experiment Run Summary
**Run Timestamp:** `20251008_133854`
**Orchestrator:** `adversarial_benchmark`

## Overall Variant Ranking
| Rank | Variant | Mean Score (± 95% CI) | Success Rate | Avg Latency (s) | Total Cost | Trials |
|:----:|:--------|:----------------------|:--------------:|:----------------:|:------------:|:------:|
| 1 | `slower_reliable_probe` | 0.7192 (± 0.0000) | 100.00% | 0.1004 | 0.0750 | 15 |
| 2 | `collaborative_agent_team` | 0.7137 (± 0.0018) | 100.00% | 0.2607 | 0.2250 | 15 |
| 3 | `caching_agent` | 0.7067 (± 0.0033) | 100.00% | 0.0301 | 0.0252 | 15 |

## Experiment Configuration
### Scoring Weights
```json
{
  "autonomy": 0.4,
  "success": 0.35,
  "cost": -0.15,
  "latency": -0.1
}
```