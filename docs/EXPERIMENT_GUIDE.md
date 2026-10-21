# Experiment Guide

## Running a campaign

`/experiments` runs all four schedulers (random, greedy, privacy-aware,
proposed GA) against the same workload and records per-algorithm metrics:
success rate, average latency, energy, privacy exposure and security risk.
A campaign is reproducible for a given seed and workload.

## Headless

```python
from engine.experiment import ExperimentManager
print(ExperimentManager().run())
```

Working results are appended to `datasets/experiment_results_2000.csv` in the
same schema used by the analytics page, so a campaign run shows up in
`/analytics` comparisons and in `/api/export/experiments`.

## Interpreting results

- **Success rate** dominates: a scheduler that drops deadlines is not
  competitive regardless of latency.
- **Privacy-aware and proposed GA** are expected to outperform random/greedy
  on privacy exposure and security risk at a small latency cost.
- The GA should hold or beat greedy on deadline success — see `GA_GUIDE.md`.

## PDF export

Use the **Export** menu on the experiments page (or `/api/export/report`) to
download a formatted PDF run report.