"""
Dataset cleaning — deduplication, invalid row removal, missing-value handling.

Only reads from raw/ and writes to processed/.  Never modifies raw files.
All operations are documented so every row in processed/ can be traced back
to its source.
"""

import csv
import os
import time
from typing import Any, Dict, List, Optional

import pandas as pd

from .paths import (
    BENIGN_LABELS,
    PROCESSED_ATTACKED,
    PROCESSED_BENIGN,
    RAW_ATTACKED,
    RAW_BENIGN,
    LOCAL_REAL_DIR,
    METADATA_DIR,
    DATASET_CATALOG,
)


CHUNK = 200_000


def _label_key_for(name: str) -> Optional[str]:
    entry = next((e for e in DATASET_CATALOG if e["name"].lower() == name.lower()), None)
    return entry["label_key"] if entry else None


def _category_key_for(name: str) -> Optional[str]:
    entry = next((e for e in DATASET_CATALOG if e["name"].lower() == name.lower()), None)
    return entry.get("category_key") if entry else None


def _benign_value_for(name: str):
    entry = next((e for e in DATASET_CATALOG if e["name"].lower() == name.lower()), None)
    return entry.get("benign_value", "normal") if entry else "normal"


def _normalise_label(val, label_key: str, category_key: str, benign_value) -> tuple:
    """Return (security_label, attack_type)."""
    v = str(val).strip().lower()
    bv = str(benign_value).strip().lower()
    if v == bv or v in ("0", "normal", "benign"):
        return ("benign", "normal")
    return ("attacked", v if v else "unknown")


def clean_nsl_kdd(force: bool = False) -> Dict[str, Any]:
    """Clean and split NSL-KDD into processed/attacked/ and processed/benign/."""
    combined = os.path.join(LOCAL_REAL_DIR, "nsl_kdd_combined.csv")
    if not os.path.exists(combined):
        return {"status": "MISSING", "path": combined}

    stats = {
        "total_rows": 0,
        "attack_rows": 0,
        "benign_rows": 0,
        "duplicates_removed": 0,
        "empty_label_rows": 0,
        "columns": [],
        "output_attack": os.path.join(PROCESSED_ATTACKED, "nsl_kdd_attacked.csv"),
        "output_benign": os.path.join(PROCESSED_BENIGN, "nsl_kdd_benign.csv"),
    }

    if not force and os.path.exists(stats["output_attack"]):
        try:
            ac = sum(1 for _ in open(stats["output_attack"], encoding="utf-8")) - 1
            bc = sum(1 for _ in open(stats["output_benign"], encoding="utf-8")) - 1
            if ac > 0 and bc > 0:
                stats["attack_rows"] = ac
                stats["benign_rows"] = bc
                stats["total_rows"] = ac + bc
                stats["status"] = "ALREADY_CLEANED"
                return stats
        except Exception:
            pass

    seen = set()
    attack_parts: List[List[Dict[str, Any]]] = []
    benign_parts: List[List[Dict[str, Any]]] = []
    current_attack: List[Dict[str, Any]] = []
    current_benign: List[Dict[str, Any]] = []

    for chunk in pd.read_csv(combined, chunksize=CHUNK, dtype=str, on_bad_lines="skip"):
        if stats["columns"] == []:
            stats["columns"] = list(chunk.columns)

        label_col = "label" if "label" in chunk.columns else " label"
        chunk[label_col] = (
            chunk[label_col]
            .astype(str)
            .str.strip()
            .str.rstrip(".")
            .str.lower()
        )
        chunk["_dup_key"] = chunk.astype(str).apply(tuple, axis=1)

        for _, row in chunk.iterrows():
            stats["total_rows"] += 1
            row_dict = row.to_dict()
            dup_key = row_dict.pop("_dup_key", None)

            if dup_key and dup_key in seen:
                stats["duplicates_removed"] += 1
                continue
            if dup_key:
                seen.add(dup_key)

            label = str(row_dict.get(label_col, "")).strip().lower()
            if label == "" or label == "nan":
                stats["empty_label_rows"] += 1
                continue

            seclbl, atype = _normalise_label(
                label,
                "label",
                "label",
                "normal",
            )
            row_dict["security_label"] = seclbl
            row_dict["attack_type"] = atype

            if seclbl == "benign":
                stats["benign_rows"] += 1
                current_benign.append(row_dict)
                if len(current_benign) >= CHUNK:
                    benign_parts.append(current_benign)
                    current_benign = []
            else:
                stats["attack_rows"] += 1
                current_attack.append(row_dict)
                if len(current_attack) >= CHUNK:
                    attack_parts.append(current_attack)
                    current_attack = []

    if current_attack:
        attack_parts.append(current_attack)
    if current_benign:
        benign_parts.append(current_benign)

    # Write output
    pd.concat([pd.DataFrame(p) for p in attack_parts], ignore_index=True).to_csv(
        stats["output_attack"], index=False
    )
    pd.concat([pd.DataFrame(p) for p in benign_parts], ignore_index=True).to_csv(
        stats["output_benign"], index=False
    )

    stats["status"] = "CLEANED"
    return stats


def clean_raw_csv(
    input_path: str,
    output_attack: str,
    output_benign: str,
    label_key: str,
    category_key: str,
    benign_value,
    force: bool = False,
) -> Dict[str, Any]:
    """Generic cleaner for any CSV with an explicit label column."""
    if not os.path.exists(input_path):
        return {"status": "MISSING", "path": input_path}

    stats = {
        "total_rows": 0,
        "attack_rows": 0,
        "benign_rows": 0,
        "duplicates_removed": 0,
        "empty_label_rows": 0,
        "columns": [],
        "output_attack": output_attack,
        "output_benign": output_benign,
    }

    if not force and os.path.exists(output_attack):
        try:
            ac = sum(1 for _ in open(output_attack, encoding="utf-8")) - 1
            bc = sum(1 for _ in open(output_benign, encoding="utf-8")) - 1
            if ac > 0 and bc > 0:
                stats["attack_rows"] = ac
                stats["benign_rows"] = bc
                stats["total_rows"] = ac + bc
                stats["status"] = "ALREADY_CLEANED"
                return stats
        except Exception:
            pass

    seen = set()
    all_attack: List[Dict[str, Any]] = []
    all_benign: List[Dict[str, Any]] = []

    for chunk in pd.read_csv(input_path, chunksize=CHUNK, dtype=str, on_bad_lines="skip"):
        if not stats["columns"]:
            stats["columns"] = list(chunk.columns)

        if label_key not in chunk.columns:
            continue

        chunk[label_key] = chunk[label_key].astype(str).str.strip().str.lower()
        chunk["_key"] = chunk.astype(str).apply(tuple, axis=1)

        for _, row in chunk.iterrows():
            stats["total_rows"] += 1
            row_dict = row.to_dict()
            dup_key = row_dict.pop("_key", None)

            if dup_key and dup_key in seen:
                stats["duplicates_removed"] += 1
                continue
            if dup_key:
                seen.add(dup_key)

            raw_label = str(row_dict.get(label_key, "")).strip().lower()
            if raw_label == "" or raw_label == "nan":
                stats["empty_label_rows"] += 1
                continue

            seclbl, atype = _normalise_label(raw_label, label_key, category_key, benign_value)
            row_dict["security_label"] = seclbl
            row_dict["attack_type"] = atype

            if seclbl == "benign":
                stats["benign_rows"] += 1
                all_benign.append(row_dict)
            else:
                stats["attack_rows"] += 1
                all_attack.append(row_dict)

    os.makedirs(os.path.dirname(output_attack), exist_ok=True)
    os.makedirs(os.path.dirname(output_benign), exist_ok=True)

    pd.DataFrame(all_attack).to_csv(output_attack, index=False)
    pd.DataFrame(all_benign).to_csv(output_benign, index=False)
    stats["status"] = "CLEANED"
    return stats


def run_cleaner(force: bool = False) -> Dict[str, Any]:
    """Clean all local datasets.  Returns per-dataset stats."""
    results: Dict[str, Any] = {}

    # NSL-KDD
    print("Cleaning NSL-KDD...")
    results["NSL-KDD"] = clean_nsl_kdd(force=force)
    for k in ("status", "total_rows", "attack_rows", "benign_rows", "duplicates_removed", "empty_label_rows"):
        print(f"  {k}: {results['NSL-KDD'].get(k, '-')}")

    return results