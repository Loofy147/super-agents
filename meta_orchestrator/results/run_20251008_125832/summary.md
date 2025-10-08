# Experiment Run Summary
**Run Timestamp:** `20251008_125832`
**Orchestrator:** `standard`

## Overall Variant Ranking
| Rank | Variant | Mean Score (± 95% CI) | Success Rate | Avg Latency (s) | Total Cost | Trials |
|:----:|:--------|:----------------------|:--------------:|:----------------:|:------------:|:------:|
| 1 | `slower_reliable_probe` | 0.7192 (± 0.0000) | 100.00% | 0.1003 | 0.1000 | 20 |
| 2 | `collaborative_agent_team` | 0.7116 (± 0.0000) | 100.00% | 0.2817 | 0.3000 | 20 |
| 3 | `caching_agent` | 0.7093 (± 0.0009) | 100.00% | 0.0060 | 0.0208 | 50 |
| 4 | `in_memory_probe` | 0.6678 (± 0.0000) | 100.00% | 0.0203 | 0.0200 | 20 |

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