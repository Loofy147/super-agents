# Experiment Run Summary
**Run Timestamp:** `20251008_153843`
**Orchestrator:** `standard`

## Overall Variant Ranking
| Rank | Variant | Mean Score (± 95% CI) | Success Rate | Avg Latency (s) | Total Cost | Trials |
|:----:|:--------|:----------------------|:--------------:|:----------------:|:------------:|:------:|
| 1 | `collaborative_agent_team` | 0.7049 (± 0.0070) | 100.00% | 0.3485 | 0.0750 | 20 |

## 💰 Economic Efficiency
| Variant | Resource Denial Rate |
|:--------|:--------------------:|
| `collaborative_agent_team` | 75.00% |

*Causal analysis failed: 'was_cached'*

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