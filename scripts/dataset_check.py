"""
dataset_check.py
================
Prints the row count of each packaged dataset and validates required columns.

Usage:
    python scripts/dataset_check.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402

import config  # noqa: E402


def check_csv(path, required_columns, min_rows=0):
    """Return a tuple (basename, rows, ok_cols, missing_cols)."""
    if not os.path.exists(path):
        return (os.path.basename(path), 0, True, required_columns)
    df = pd.read_csv(path)
    missing = [c for c in required_columns if c not in df.columns]
    ok = len(missing) == 0 and len(df) >= min_rows
    return (os.path.basename(path), len(df), ok, missing)


def main():
    checks = [
        (
            "tasks_10000.csv",
            config.TASK_DATASET,
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
            10000,
        ),
        (
            "attack_events_5000.csv",
            config.ATTACK_DATASET,
            [
                "event_id",
                "timestamp",
                "attack_type",
                "target_resource",
                "severity",
                "pre_risk",
                "post_risk",
                "affected_tasks",
                "detection_score",
                "mitigation_action",
                "detected",
            ],
            5000,
        ),
        (
            "resource_states_3000.csv",
            config.RESOURCE_DATASET,
            [
                "state_id",
                "timestamp",
                "resource_id",
                "resource_type",
                "cpu_utilization",
                "memory_utilization",
                "network_latency_ms",
                "energy_rate",
                "trust_score",
                "security_risk",
                "availability",
                "active_tasks",
            ],
            3000,
        ),
        (
            "experiment_results_2000.csv",
            config.EXPERIMENT_DATASET,
            [
                "run_id",
                "algorithm",
                "task_count",
                "attack_condition",
                "avg_latency_ms",
                "energy_j",
                "privacy_score",
                "security_score",
                "success_rate",
                "scalability_score",
            ],
            2000,
        ),
        (
            "ai_training_10000.csv",
            config.AI_TRAINING_DATASET,
            [
                "cpu",
                "memory",
                "latency",
                "trust",
                "security_risk",
                "attack_severity",
                "privacy",
                "workload",
                "storage_integrity",
                "attack_exposure",
                "label",
            ],
            10000,
        ),
        (
            "storage_security_5000.csv",
            config.STORAGE_SECURITY_DATASET,
            [
                "storage_id",
                "storage_type",
                "integrity_score",
                "risk_score",
                "attack_label",
            ],
            5000,
        ),
    ]

    print("SecureDT Dataset Validation")
    print("=" * 46)
    all_ok = True
    for name, path, cols, min_rows in checks:
        bname, rows, ok, missing = check_csv(path, cols, min_rows)
        status = "OK" if ok else "PROBLEM"
        all_ok = all_ok and ok
        print(f"  {bname:<22} {rows:>8,} rows  [{status}]")
        if not ok:
            print(
                f"      min rows: {min_rows}, actual: {rows}, "
                f"missing cols: {missing}"
            )
    print("=" * 46)
    if all_ok:
        print("All datasets validated successfully.")
    else:
        print("One or more datasets are incomplete.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
