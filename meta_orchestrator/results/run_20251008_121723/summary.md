# Experiment Run Summary
**Run Timestamp:** `20251008_121723`
**Orchestrator:** `standard`

## Overall Variant Ranking
Ranked by `mean_score` (higher is better).
| Rank | Variant | Mean Score (± 95% CI) | Success Rate | Avg Latency (s) | Total Cost | Trials |
|:----:|:--------|:----------------------|:--------------:|:----------------:|:------------:|:------:|
| 1 | `slower_reliable_probe` | 0.7192 (± 0.0000) | 100.00% | 0.1002 | 0.2500 | 50 |
| 2 | `collaborative_agent_team` | 0.7116 (± 0.0000) | 100.00% | 0.2813 | 0.7500 | 50 |
| 3 | `caching_agent` | 0.7097 (± 0.0006) | 100.00% | 0.0030 | 0.0129 | 50 |

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