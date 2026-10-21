"""
Preprocessing: label encoding, numeric normalisation, train/test split.

Operates on processed/attacked/ and processed/benign/ CSVs and writes a
combined feature-ready file for the AI model.  Never modifies the
intermediate cleaned CSVs — only adds a *features* CSV alongside them.
"""

import json
import os
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, MinMaxScaler

from .paths import (
    PROCESSED_ATTACKED,
    PROCESSED_BENIGN,
    DATASET_CATALOG,
    LOCAL_REAL_DIR,
    METADATA_DIR,
)

CHUNK = 200_000

# Numeric columns that are safe to normalise directly.
SAFE_NUMERIC = {
    "duration",
    "src_bytes",
    "dst_bytes",
    "land",
    "wrong_fragment",
    "urgent",
    "hot",
    "num_failed_logins",
    "logged_in",
    "num_compromised",
    "root_shell",
    "su_attempted",
    "num_root",
    "num_file_creations",
    "num_shells",
    "num_access_files",
    "is_host_login",
    "is_guest_login",
    "count",
    "srv_count",
    "serror_rate",
    "srv_serror_rate",
    "rerror_rate",
    "srv_rerror_rate",
    "same_srv_rate",
    "diff_srv_rate",
    "srv_diff_host_rate",
    "dst_host_count",
    "dst_host_srv_count",
    "dst_host_same_srv_rate",
    "dst_host_diff_srv_rate",
    "dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate",
    "dst_host_serror_rate",
    "dst_host_srv_serror_rate",
    "dst_host_rerror_rate",
    "dst_host_srv_rerror_rate",
}

# NSL-KDD categorical columns to label-encode.
NSL_CATEGORICAL = ["protocol_type", "service", "flag"]


def _load_csv(path: str, chunksize: Optional[int] = None):
    return pd.read_csv(
        path,
        chunksize=chunksize,
        dtype=str,
        on_bad_lines="skip",
        low_memory=False,
    )


def preprocess_nsl_kdd(force: bool = False) -> Dict[str, Any]:
    """Combine cleaned attacked/benign into one feature-ready CSV and
    write train/test splits under processed/."""
    attack_csv = os.path.join(PROCESSED_ATTACKED, "nsl_kdd_attacked.csv")
    benign_csv = os.path.join(PROCESSED_BENIGN, "nsl_kdd_benign.csv")
    out_dir = PROCESSED_ATTACKED  # master feature CSV lives with attacked/

    combined_csv = os.path.join(out_dir, "nsl_kdd_features.csv")
    train_csv = os.path.join(out_dir, "nsl_kdd_train.csv")
    test_csv = os.path.join(out_dir, "nsl_kdd_test.csv")

    if not force and os.path.exists(combined_csv) and os.path.exists(train_csv):
        tc = sum(1 for _ in open(train_csv, encoding="utf-8")) - 1
        vc = sum(1 for _ in open(test_csv, encoding="utf-8")) - 1
        if tc > 0:
            return {"status": "ALREADY_PREPROCESSED", "total_rows": tc + vc, "train_rows": tc, "test_rows": vc}

    if not os.path.exists(attack_csv) or not os.path.exists(benign_csv):
        return {"status": "MISSING", "note": "Run cleaner first to produce processed/attacked and processed/benign."}

    print("Loading cleaned datasets...")
    df_attack = pd.read_csv(attack_csv, dtype=str, on_bad_lines="skip")
    df_benign = pd.read_csv(benign_csv, dtype=str, on_bad_lines="skip")

    df_all = pd.concat([df_benign, df_attack], ignore_index=True)

    # Encode categoricals
    label_encoders: Dict[str, Any] = {}
    for col in NSL_CATEGORICAL:
        if col in df_all.columns:
            le = LabelEncoder()
            df_all[col] = le.fit_transform(df_all[col].astype(str))
            label_encoders[col] = le.classes_.tolist()

    # Ensure numeric columns are actually numeric
    for col in list(SAFE_NUMERIC) + ["src_bytes", "dst_bytes"]:
        if col in df_all.columns:
            df_all[col] = pd.to_numeric(df_all[col], errors="coerce").fillna(0)

    # Add derived fields for unified schema
    if "src_bytes" in df_all.columns and "dst_bytes" in df_all.columns:
        df_all["byte_count"] = (
            pd.to_numeric(df_all["src_bytes"], errors="coerce").fillna(0)
            + pd.to_numeric(df_all["dst_bytes"], errors="coerce").fillna(0)
        )

    # Normalise numeric features using MinMaxScaler
    numeric_cols = [c for c in df_all.columns if c in SAFE_NUMERIC and c not in NSL_CATEGORICAL]
    numeric_cols = [c for c in numeric_cols if c in df_all.columns]
    if numeric_cols:
        df_all[numeric_cols] = df_all[numeric_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
        scaler = MinMaxScaler()
        df_all[numeric_cols] = pd.DataFrame(
            scaler.fit_transform(df_all[numeric_cols]),
            columns=numeric_cols,
            index=df_all.index,
        )

    # Encode security_label to binary (0=benign, 1=attacked)
    if "security_label" in df_all.columns:
        df_all["security_label_binary"] = (df_all["security_label"] != "benign").astype(int)

    # Train/test split
    feature_cols = [c for c in df_all.columns if c not in ("security_label", "attack_type")]
    X = df_all[feature_cols]
    y = df_all["security_label_binary"] if "security_label_binary" in df_all.columns else None

    if y is not None:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
    else:
        X_train, X_test = train_test_split(X, test_size=0.2, random_state=42)
        y_train = y_test = None

    # Add label column back
    X_train_out = X_train.copy()
    X_test_out = X_test.copy()
    if y_train is not None:
        X_train_out["security_label"] = y_train.map({0: "benign", 1: "attacked"})
        X_test_out["security_label"] = y_test.map({0: "benign", 1: "attacked"})

    X_train_out.to_csv(train_csv, index=False)
    X_test_out.to_csv(test_csv, index=False)
    df_all.to_csv(combined_csv, index=False)

    # Save scaler + encoder metadata
    meta = {
        "dataset": "NSL-KDD",
        "total_rows": len(df_all),
        "train_rows": len(X_train_out),
        "test_rows": len(X_test_out),
        "feature_cols": feature_cols,
        "label_encoders": label_encoders,
        "numeric_cols": numeric_cols,
        "timestamp": pd.Timestamp.utcnow().isoformat(),
    }
    os.makedirs(METADATA_DIR, exist_ok=True)
    with open(os.path.join(METADATA_DIR, "nsl_kdd_preprocessing.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, default=str)

    return {
        "status": "PREPROCESSED",
        "total_rows": len(df_all),
        "train_rows": len(X_train_out),
        "test_rows": len(X_test_out),
        "features": len(feature_cols),
    }


def run_preprocessor(force: bool = False) -> Dict[str, Any]:
    print("Preprocessing NSL-KDD...")
    r = preprocess_nsl_kdd(force=force)
    for k, v in r.items():
        print(f"  {k}: {v}")
    return {"NSL-KDD": r}