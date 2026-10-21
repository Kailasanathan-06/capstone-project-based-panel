# Reproducibility Guide

Every generated artifact is reproducible.

## Fixed Seeds

- `config.DATASET_SEED` (default 42) seeds all synthetic dataset generation.
- GA uses its own seeded RNG; re-running with the same config yields the same
  convergence curve.
- Big-data streaming generation accepts an explicit `seed` argument
  (`/api/datasets/generate`, `engine.bigdata.generate_tasks_streaming`).

## Generating the Datasets

```bash
python scripts/generate_dataset.py --tasks 10000
```

This writes six labelled, schema-validated CSV files under `datasets/`:

| File | Rows | Purpose |
|---|---|---|
| tasks_10000.csv | 10,000 | Workloads: type, size, cpu, memory, deadline, sensitivities, label |
| attack_events_5000.csv | 5,000 | Attack events with severity, pre/post risk, mitigation |
| resource_states_3000.csv | 3,000 | Resource telemetry: cpu, memory, trust, security risk |
| experiment_results_2000.csv | 2,000 | Algorithm runs: latency, energy, privacy, security, success |
| ai_training_10000.csv | 10,000 | Feature rows + label for the Random Forest |
| storage_security_5000.csv | 5,000 | Storage integrity/risk lab rows |

## Training the AI Model

```bash
python scripts/train_ai.py
```

Random Forest trained on `ai_training_10000.csv` → `models/risk_model.pkl`,
with the signed ROC-AUC / feature-importance report. If training is skipped,
the engine falls back to transparent rule-based analysis.

## Big-Data Generation

`/api/datasets/generate` streams up to 5,000,000 rows into a chunked CSV
(10 M max through `engine.bigdata.generate_tasks_streaming`). Row counts and
sampled aggregations are deterministic for a fixed seed. Parquet/SQLite
conversion is lazy and optional (requires pyarrow / duckdb).

## Verification

```bash
python scripts/dataset_check.py
python scripts/setup_check.py
python tests/run_all.py
```