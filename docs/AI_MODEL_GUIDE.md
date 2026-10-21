# AI Model Guide

## What the model does

Predicts the **security risk** of an incoming scheduling event using labelled
synthetic task data, then attaches a level (`safe`, `trained`, `critical`) and
an explainability report (feature reasons + confidence).

## Training

```bash
python scripts/train_ai.py
```

- Algorithm: Random Forest (`scikit-learn`), tuned with `RandomizedSearchCV`.
- Training set: `datasets/ai_training_10000.csv` (10,000 labelled rows).
- Output: `models/risk_model.pkl` plus a metrics JSON report.

## Why the magic risk thresholds are stable

The task dataset generator emits risk-labelled workloads; `train_ai.py` fits
the forest on the exact same generation-pipeline features the runtime uses, so
real-time predictions align with training labels. If the model file is absent
the engine automatically falls back to a deterministic rule set (documented in
`engine/ai.py`) rather than failing.

## Optional models

| Package | Effect | Enabled |
|---|---|---|
| shap | Feature-reason list with SHAP-style importances | Auto if installed |
| xgboost | Gradient-boosted alternative used when selected | Auto if installed, configurable |

## Explaining a prediction

The `/ai-intelligence` page lets you pick a task and see: predicted level, probability
(confidence), the top contributing features, and the fallback rationale used
when the label is low-confidence. All metrics are JSON-serialisable and
exportable.

## Metrics

`scripts/train_ai.py` writes ROC-AUC, accuracy, per-class F1 and the
feature-importance table to `models/risk_metrics.json`; the System Health page
surfaces whether the model is ready and which version is loaded.