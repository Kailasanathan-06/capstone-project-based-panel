"""
Data Normalizer (UnifiedEvent)
==============================
Maps every dataset into a unified schema so downstream modules (risk engine,
AI, twin, GA, analytics) see identical fields regardless of source.

Unified fields:

    event_id, timestamp, source_dataset, source_type, task_id, src, dst,
    protocol, bytes, packets, duration, latency, cpu, memory, bandwidth,
    resource_load, privacy, security, risk, attack_type, label

Original dataset-specific columns are preserved under `metadata` and never
destroyed.
"""

import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

import config  # noqa: E402
from engine.bigdata import read_chunks  # noqa: E402

UNIFIED_FIELDS = [
    "event_id",
    "timestamp",
    "source_dataset",
    "source_type",
    "task_id",
    "src",
    "dst",
    "protocol",
    "bytes",
    "packets",
    "duration",
    "latency",
    "cpu",
    "memory",
    "bandwidth",
    "resource_load",
    "privacy",
    "security",
    "risk",
    "attack_type",
    "label",
]

# Column-name maps for known schemas: (unified -> tuple of possible aliases)
FIELD_ALIASES = {
    "task_id": ("task_id", "Flow ID", "id"),
    "src": ("src", "saddr", "srcip", "ip.src", "Source IP", "Src IP"),
    "dst": ("dst", "daddr", "dstip", "ip.dst", "Destination IP", "Dst IP"),
    "protocol": ("protocol", "proto", "Protocol", "Layer 4 Protocol", "Proto"),
    "bytes": (
        "bytes",
        "sbytes",
        "Total Fwd Packets",
        "TotLen Fwd Pkts",
        "Total Length of Fwd Packets",
        "Flow Bytes/s",
    ),
    "packets": (
        "packets",
        "pkts",
        "spkts",
        "Tot Fwd Pkts",
        "Total Fwd Pkts",
        "Tot Bwd Pkts",
    ),
    "duration": ("duration", "dur", "Flow Duration", "duration_ms"),
    "latency": (
        "latency",
        "expected_latency_ms",
        "network_latency_ms",
        "Flow IAT Mean",
        "Fwd IAT Mean",
    ),
    "cpu": ("cpu", "cpu_utilization", "cpu_cycles_giga"),
    "memory": ("memory", "memory_utilization", "memory_mb"),
    "bandwidth": ("bandwidth", "Flow Bytes/s", "rate"),
    "privacy": ("privacy", "privacy_sensitivity", "privacy_level", "privacy_score"),
    "security": ("security", "security_sensitivity", "security_risk", "security_score"),
    "risk": ("risk", "risk_score", "security_risk"),
    "attack_type": (
        "attack_type",
        "attack_cat",
        "subcategory",
        "category",
        "attack_label",
        "Label",
    ),
    "label": ("label", "Label", "class", "type"),
}

SOURCE_TYPE_BY_SCHEMA = {
    "tasks_": "task",
    "ai_training": "feature",
    "attack_events": "attack_event",
    "resource_states": "resource_state",
    "storage_security": "storage_event",
    "experiment_results": "experiment_result",
}


def detect_source_type(file_name):
    low = file_name.lower()
    for key, val in SOURCE_TYPE_BY_SCHEMA.items():
        if key in low:
            return val
    if low.endswith(".log") or "conn" in low:
        return "telemetry"
    return "dataset"


def _first(df, *candidates, default=None):
    for c in candidates:
        if c in df.columns:
            return df[c]
    return None


def normalize_rows(df, file_name="dataset.csv", source="PUBLIC DATASET"):
    """Convert one DataFrame into a list of UnifiedEvent dicts."""
    low = file_name.lower()
    source_type = detect_source_type(file_name)
    n = int(df.shape[0])
    out = []
    get = _first

    task_id = get(df, "task_id", "Flow ID", "id")
    src = get(df, "src", "saddr", "srcip", "ip.src", "Source IP", "Src IP")
    dst = get(df, "dst", "daddr", "dstip", "ip.dst", "Destination IP", "Dst IP")
    proto = get(df, "protocol", "proto", "Protocol", "Layer 4 Protocol", "Proto")
    byt = get(
        df,
        "bytes",
        "sbytes",
        "TotLen Fwd Pkts",
        "Total Length of Fwd Packets",
        "Flow Bytes/s",
    )
    pkts = get(
        df, "packets", "pkts", "spkts", "Tot Fwd Pkts", "Total Fwd Pkts", "Tot Bwd Pkts"
    )
    dur = get(df, "duration", "dur", "Flow Duration")
    lat = get(
        df,
        "latency",
        "expected_latency_ms",
        "network_latency_ms",
        "Flow IAT Mean",
        "Fwd IAT Mean",
    )
    cpu = get(df, "cpu", "cpu_utilization", "cpu_cycles_giga")
    mem = get(df, "memory", "memory_utilization", "memory_mb")
    bwd = get(df, "bandwidth", "Flow Bytes/s", "rate")
    priv = get(df, "privacy", "privacy_sensitivity", "privacy_level", "privacy_score")
    sec = get(df, "security", "security_sensitivity", "security_risk", "security_score")
    risk = get(df, "risk", "risk_score", "security_risk")
    attack = get(
        df,
        "attack_type",
        "attack_cat",
        "subcategory",
        "category",
        "attack_label",
        "Label",
    )
    label = get(df, "label", "Label", "class", "type")
    timestamp = get(df, "timestamp", "ts")

    for i in range(n):
        row = df.iloc[i]
        event_id = f"evt-{uuid.uuid4().hex[:12]}"
        ts = _ts(row, timestamp)
        atk = _s(attack, i) or ""
        if atk and atk.lower() in ("benign", "normal", "safe", "0", "normal."):
            atk = ""
        lbl = _s(label, i) or ("attack" if atk else "normal")
        if str(lbl).lower() in ("benign", "normal", "safe", "0", "normal."):
            lbl = "normal"
        metadata = {c: _v(row, c) for c in df.columns}
        out.append(
            {
                "event_id": event_id,
                "timestamp": ts,
                "source_dataset": file_name,
                "source_type": source_type,
                "task_id": _s(task_id, i) if task_id is not None else event_id,
                "src": _s(src, i),
                "dst": _s(dst, i),
                "protocol": (_s(proto, i) or "").upper(),
                "bytes": _num(row, byt, i),
                "packets": _num(row, pkts, i),
                "duration": _num(row, dur, i),
                "latency": _num(row, lat, i),
                "cpu": _num(row, cpu, i),
                "memory": _num(row, mem, i),
                "bandwidth": _num(row, bwd, i),
                "resource_load": _num(row, get(df, "load", "workload"), i),
                "privacy": _norm01(_num(row, priv, i)),
                "security": _norm01(_num(row, sec, i)),
                "risk": _norm01(_num(row, risk, i)),
                "attack_type": atk,
                "label": str(lbl).lower(),
                "source": source,
                "metadata": metadata,
            }
        )
    return out


def normalize_csv(path, chunksize=100_000, source="PUBLIC DATASET", max_rows=None):
    """Streaming normalization of a CSV into UnifiedEvent rows."""
    out = []
    emitted = 0
    for df in read_chunks(path, chunksize=chunksize):
        rows = normalize_rows(df, os.path.basename(path), source)
        out.extend(rows)
        emitted += len(rows)
        if max_rows and emitted >= max_rows:
            break
    if max_rows and len(out) > max_rows:
        out = out[:max_rows]
    return out


def _v(row, c):
    try:
        v = row[c]
        if isinstance(v, float) and (v != v):  # NaN
            return None
        return v
    except (KeyError, IndexError):
        return None


def _s(col_or_row, i):
    if col_or_row is None:
        return None
    try:
        v = col_or_row.iloc[i]
    except AttributeError:
        v = col_or_row
    if v is None:
        return None
    try:
        if isinstance(v, float) and (v != v):
            return None
    except (TypeError, ValueError):
        pass
    return str(v)


def _num(row, col, i):
    if col is None:
        return 0.0
    v = _s(col, i)
    try:
        return round(float(v), 4)
    except (TypeError, ValueError):
        return 0.0


def _norm01(v):
    try:
        return round(min(1.0, max(0.0, float(v))), 4)
    except (TypeError, ValueError):
        return 0.0


def _ts(row, col):
    if col is None:
        return None
    return _v(row, col.name)


if __name__ == "__main__":
    df = pd.read_csv(config.TASK_DATASET, nrows=20)
    events = normalize_rows(df, "tasks_10000.csv", source="SYNTHETIC DATA")
    print("events:", len(events))
    print("unified columns:", list(events[0].keys())[:9])
    print("sample:", events[0]["task_id"], events[0]["label"])
