"""
Statistics — compute real statistics from the actual files on disk.

Outputs (never fabricated):

- datasets/statistics/statistics.json       — global summary
- datasets/statistics/attack_distribution.csv  — class frequency table
- datasets/statistics/benign_summary.json   — benign data analysis

Also used by the Django dataset dashboard API.
"""

import json
import os
from typing import Any, Dict, List

import pandas as pd

from .paths import (
    DATASET_ROOT,
    METADATA_DIR,
    PROCESSED_ATTACKED,
    PROCESSED_BENIGN,
    RAW_ATTACKED,
    RAW_BENIGN,
    STATISTICS_DIR,
    LOCAL_REAL_DIR,
    DATASET_CATALOG,
)


def fast_rows(path: str) -> int:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return max(0, sum(1 for _ in fh) - 1)
    except Exception:
        return 0


def file_size_mb(path: str) -> float:
    try:
        return round(os.path.getsize(path) / (1024 * 1024), 2)
    except Exception:
        return 0.0


def _class_distribution(csv_path: str, label_col: str) -> Dict[str, int]:
    """Compute per-class counts streaming (no full load into RAM)."""
    counts: Dict[str, int] = {}
    try:
        for chunk in pd.read_csv(csv_path, chunksize=200_000, dtype=str, usecols=[label_col], on_bad_lines="skip"):
            col = chunk[label_col].astype(str).str.strip().str.lower()
            values = col.value_counts()
            for k, v in values.items():
                counts[str(k)] = counts.get(str(k), 0) + int(v)
    except Exception:
        pass
    return counts


def attack_label_distribution(processed_attack: str = os.path.join(PROCESSED_ATTACKED, "nsl_kdd_attacked.csv")) -> Dict[str, Any]:
    """Attack type / class distribution for a processed attacked CSV."""
    if not os.path.exists(processed_attack):
        return {"status": "MISSING", "path": processed_attack}

    label_col = "attack_type"
    counts = _class_distribution(processed_attack, label_col)
    total = sum(counts.values()) or 1
    rows = sorted(
        [
            {"label": k, "count": v, "percentage": round(100.0 * v / total, 2)}
            for k, v in counts.items()
        ],
        key=lambda r: -r["count"],
    )
    summary = {
        "status": "OK",
        "path": processed_attack,
        "total_records": sum(counts.values()),
        "classes": len(rows),
        "rows": rows,
    }
    # Write CSV report
    os.makedirs(STATISTICS_DIR, exist_ok=True)
    pd.DataFrame(rows).to_csv(os.path.join(STATISTICS_DIR, "attack_distribution.csv"), index=False)
    return summary


def benign_summary(processed_benign: str = os.path.join(PROCESSED_BENIGN, "nsl_kdd_benign.csv")) -> Dict[str, Any]:
    """Statistical summary of the benign dataset."""
    if not os.path.exists(processed_benign):
        return {"status": "MISSING", "path": processed_benign}

    sample = pd.read_csv(processed_benign, dtype=str, nrows=1000, on_bad_lines="skip")
    summary = {
        "status": "OK",
        "path": processed_benign,
        "total_records": fast_rows(processed_benign),
        "columns": list(sample.columns),
        "sample_rows": len(sample),
    }
    # Missing values approximation on first chunk
    chunk = pd.read_csv(processed_benign, dtype=str, chunksize=50000, on_bad_lines="skip")
    first = next(chunk, None)
    if first is not None:
        missing = first.isna().sum().to_dict()
        summary["missing_values"] = {str(k): int(v) for k, v in missing.items() if int(v) > 0}
    else:
        summary["missing_values"] = {}

    df = pd.read_csv(processed_benign, dtype=str, on_bad_lines="skip", usecols=lambda c: c != "attack_type")
    summary["duplicate_rows"] = int(df.duplicated().sum())
    summary["data_types"] = {str(c): "str" for c in sample.columns}
    summary["simulated_or_real"] = "REAL PUBLIC DATASET (NSL-KDD normal class)"
    summary["source_notes"] = "Filtered from NSL-KDD: original label 'normal' -> unified label 'benign'."

    with open(os.path.join(STATISTICS_DIR, "benign_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, default=str)
    return summary


def storage_usage() -> Dict[str, Any]:
    """Total bytes across the datasets tree."""
    total = 0
    for root, dirs, files in os.walk(DATASET_ROOT):
        if "raw" in root or "processed" in root or "real" in root:
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
    return {
        "bytes": total,
        "mb": round(total / (1024 * 1024), 2),
        "gb": round(total / (1024 * 1024 * 1024), 2),
    }


def compute_all_statistics() -> Dict[str, Any]:
    """Run every statistic and persist the reports."""
    os.makedirs(STATISTICS_DIR, exist_ok=True)

    attack_dist = attack_label_distribution()
    benign = benign_summary()

    # Per-catalog record counts for any raw/processed files present
    records: Dict[str, Any] = {}
    for entry in DATASET_CATALOG:
        records[entry["name"]] = {"expected": entry["records_expected"], "local_rows": 0, "status": "MANUAL_DOWNLOAD_REQUIRED"}

    # NSL-KDD actual
    local_files: Dict[str, int] = {}
    for f in os.listdir(LOCAL_REAL_DIR):
        fp = os.path.join(LOCAL_REAL_DIR, f)
        if os.path.isfile(fp) and (f.endswith(".csv") or f.endswith(".txt")):
            local_files[f] = fast_rows(fp)
    records["NSL-KDD"]["local_rows"] = sum(
        v for k, v in local_files.items() if "combined" in k or "train" in k or "test" in k
    )
    records["NSL-KDD"]["status"] = "LOCAL"

    # Processed counts for NSL-KDD splits
    proc_attack = fast_rows(os.path.join(PROCESSED_ATTACKED, "nsl_kdd_attacked.csv")) if os.path.exists(os.path.join(PROCESSED_ATTACKED, "nsl_kdd_attacked.csv")) else 0
    proc_benign = fast_rows(os.path.join(PROCESSED_BENIGN, "nsl_kdd_benign.csv")) if os.path.exists(os.path.join(PROCESSED_BENIGN, "nsl_kdd_benign.csv")) else 0

    result = {
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "attacked_distribution": attack_dist,
        "benign_summary": benign,
        "records": records,
        "processed": {
            "attacked_rows": proc_attack,
            "benign_rows": proc_benign,
            "total_processed_rows": proc_attack + proc_benign,
        },
        "storage_usage": storage_usage(),
    }

    with open(os.path.join(STATISTICS_DIR, "statistics.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, default=str)
    return result


if __name__ == "__main__":
    r = compute_all_statistics()
    print(json.dumps(r, indent=2, default=str)[:4000])