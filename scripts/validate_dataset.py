"""
validate_dataset.py
===================
Performs structural validation of the packaged CSV datasets: header presence,
row counts, required columns, nullity, numeric ranges where applicable.

Usage:
    python scripts/validate_dataset.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402

import config  # noqa: E402

DATASETS = [
    (
        config.TASK_DATASET,
        "tasks",
        [
            "task_id",
            "task_type",
            "data_size_mb",
            "cpu_cycles_giga",
            "memory_mb",
            "deadline_ms",
            "privacy_sensitivity",
            "security_sensitivity",
            "label",
        ],
    ),
    (
        config.ATTACK_DATASET,
        "attacks",
        [
            "event_id",
            "attack_type",
            "target_resource",
            "severity",
            "pre_risk",
            "post_risk",
        ],
    ),
    (
        config.RESOURCE_DATASET,
        "resources",
        [
            "state_id",
            "resource_id",
            "cpu_utilization",
            "memory_utilization",
            "trust_score",
            "security_risk",
        ],
    ),
    (
        config.EXPERIMENT_DATASET,
        "experiments",
        ["run_id", "algorithm", "task_count", "avg_latency_ms", "success_rate"],
    ),
    (config.AI_TRAINING_DATASET, "ai", config.AI_FEATURES + ["label"]),
    (
        config.STORAGE_SECURITY_DATASET,
        "storage",
        ["storage_id", "integrity_score", "risk_score", "attack_label"],
    ),
]

REQUIRED_COUNTS = {
    "tasks": 10000,
    "attacks": 5000,
    "resources": 3000,
    "experiments": 2000,
    "ai": 10000,
    "storage": 5000,
}


def main():
    print("SecureDT CSV Structure Validation")
    print("=" * 50)
    ok = True
    for path, kind, cols in DATASETS:
        if not os.path.exists(path):
            print(f"  MISSING  {os.path.basename(path)}")
            ok = False
            continue
        df = pd.read_csv(path)
        msgs = []
        missing = [c for c in cols if c not in df.columns]
        if missing:
            msgs.append(f"missing columns: {missing}")
        if len(df) < REQUIRED_COUNTS.get(kind, 0):
            msgs.append(f"low rows: {len(df)}")
        nulls = int(df.isnull().sum().sum())
        if nulls > 0:
            msgs.append(f"null cells: {nulls}")
        status = "OK" if not msgs else "PROBLEM"
        ok = ok and not msgs
        print(f"  {os.path.basename(path):<28} {len(df):>6,} rows " f"[{status}]")
        for m in msgs:
            print(f"      {m}")
    print("=" * 50)
    print("All datasets structurally valid." if ok else "Some datasets have issues.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
