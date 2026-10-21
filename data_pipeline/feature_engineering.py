"""
Feature engineering — derive security-risk fields and unified-schema mappings
from preprocessed CSVs.

Derived fields (see UNIFIED_SCHEMA in paths.py):

- risk_score : computed from attack_type + feature heuristics (see below)
- flow_rate  : bytes / max(duration, 1)
- packet_count: not available in NSL-KDD (left null or derived from count)

All derivations are documented here and in docs/DATASET_SELECTION_REPORT.md.
"""

import os
from typing import Any, Dict

import numpy as np
import pandas as pd

from .paths import PROCESSED_ATTACKED, DATASET_ROOT

# Base risk scores per attack family (0..1).  See config.py ATTACK_BASE_RISK
# for project-integrated values.  These feature-engineering values are a
# conservative mapping for the NSL-KDD 4-family scheme (DoS, Probe, R2L, U2R).
ATTACK_RISK_MAP: Dict[str, float] = {
    "normal": 0.0,
    "back": 0.45,
    "neptune": 0.50,
    "smurf": 0.50,
    "teardrop": 0.40,
    "pod": 0.35,
    "land": 0.40,
    "guess_passwd": 0.60,
    "ftp_write": 0.55,
    "imap": 0.50,
    "phf": 0.50,
    "multihop": 0.45,
    "warezclient": 0.30,
    "warezmaster": 0.30,
    "spy": 0.60,
    "rootkit": 0.75,
    "buffer_overflow": 0.70,
    "loadmodule": 0.65,
    "perl": 0.60,
    "satan": 0.25,
    "ipsweep": 0.25,
    "portsweep": 0.25,
    "nmap": 0.30,
}


def _attack_type_to_risk(attack_type: str) -> float:
    return ATTACK_RISK_MAP.get(str(attack_type).strip().lower(), 0.35)


def derive_risk_scores(csv_path: str) -> Dict[str, Any]:
    """Add ``risk_score`` column to a CSV in-place and return stats."""
    if not os.path.exists(csv_path):
        return {"status": "MISSING", "path": csv_path}

    print(f"  Deriving risk scores: {os.path.basename(csv_path)}...")
    chunks: list = []
    total = 0
    for chunk in pd.read_csv(csv_path, chunksize=200_000, dtype=str, on_bad_lines="skip"):
        if "attack_type" in chunk.columns:
            chunk["risk_score"] = chunk["attack_type"].map(_attack_type_to_risk).fillna(0.35)
        else:
            chunk["risk_score"] = 0.35
        # Derive flow_rate from src_bytes / (duration + 1) where available
        if "src_bytes" in chunk.columns and "duration" in chunk.columns:
            sb = pd.to_numeric(chunk["src_bytes"], errors="coerce").fillna(0)
            dur = pd.to_numeric(chunk["duration"], errors="coerce").fillna(0)
            chunk["flow_rate"] = (sb / (dur + 1)).round(4)
        if "src_bytes" in chunk.columns and "dst_bytes" in chunk.columns:
            sb = pd.to_numeric(chunk["src_bytes"], errors="coerce").fillna(0)
            db = pd.to_numeric(chunk["dst_bytes"], errors="coerce").fillna(0)
            chunk["byte_count"] = (sb + db).astype(int)
        chunks.append(chunk)
        total += len(chunk)

    if chunks:
        pd.concat(chunks, ignore_index=True).to_csv(csv_path, index=False)

    return {"status": "DERIVED", "rows": total, "path": csv_path}


def run_feature_engineering() -> Dict[str, Any]:
    """Run feature engineering on all processed CSVs."""
    results: Dict[str, Any] = {}
    for subdir in ("attacked", "benign"):
        d = os.path.join(DATASET_ROOT, "processed", subdir)
        if not os.path.isdir(d):
            continue
        for fname in sorted(os.listdir(d)):
            if not fname.endswith(".csv") or "features" in fname:
                continue
            path = os.path.join(d, fname)
            results[fname] = derive_risk_scores(path)
    return results