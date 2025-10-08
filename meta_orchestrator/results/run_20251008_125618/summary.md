# Experiment Run Summary
**Run Timestamp:** `20251008_125618`
**Orchestrator:** `standard`

## Overall Variant Ranking
| Rank | Variant | Mean Score (± 95% CI) | Success Rate | Avg Latency (s) | Total Cost | Trials |
|:----:|:--------|:----------------------|:--------------:|:----------------:|:------------:|:------:|
| 1 | `caching_agent` | 0.7096 (± 0.0008) | 100.00% | 0.0038 | 0.0119 | 40 |

## 🧠 Causal Insights
- **Finding for Caching Agents:** A cache hit (`was_cached=True`) **causes** an estimated **-0.1503s change** in mean latency. (p-value: 0.0400)

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