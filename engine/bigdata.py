"""
Big Data Engine
===============
Streaming / chunked helpers so the prototype can handle 100K .. 10M+ records
without loading them into browser memory (or all of memory at once):

  * streaming synthetic task generation (chunked numpy, appended to CSV)
  * chunked readers for validation / normalization / aggregation
  * deterministic sampling and fast row counting
  * optional Parquet / SQLite export when available (never required)

All data generated here is explicitly SYNTHETIC (fixed seeds) and is never
presented as a real dataset.
"""

import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

import config  # noqa: E402

MAX_GENERATION_CAP = 10_000_000  # hard cap for in-process generation

# Default API caps (the CLI can generate more)
API_GENERATION_CAP = 5_000_000

TASK_COLUMNS = [
    "task_id",
    "timestamp",
    "task_type",
    "data_size_mb",
    "cpu_cycles_giga",
    "memory_mb",
    "deadline_ms",
    "privacy_sensitivity",
    "security_sensitivity",
    "arrival_rate",
    "source_node",
    "preferred_resource",
    "expected_latency_ms",
    "expected_energy_j",
    "attack_exposure",
    "label",
]


def fast_row_count(path):
    """Count data rows of a CSV without loading it (line count - header)."""
    if not path or not os.path.exists(path):
        return 0
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return max(0, sum(1 for _ in fh) - 1)
    except Exception:  # noqa: BLE001
        return 0


def read_chunks(path, chunksize=100_000, **kw):
    """Yield pandas DataFrames chunk by chunk (memory-friendly)."""
    default = {
        "chunksize": chunksize,
        "low_memory": False,
        "encoding": "utf-8",
        "on_bad_lines": "skip",
    }
    default.update(kw)
    for df in pd.read_csv(path, **default):
        yield df


def sample(path, n=1000, seed=42):
    """Deterministic sample of up to n rows without loading everything."""
    total = fast_row_count(path)
    if total == 0:
        return pd.DataFrame()
    if total <= 100_000:
        df = pd.read_csv(path)
        if n >= total:
            return df
        return df.sample(n=n, random_state=seed)
    # large file: sample a few chunk starts, then take n rows from those chunks
    rng = np.random.default_rng(seed)
    names = None
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        names = fh.readline().strip().split(",")
    chunks = []
    want_left = n
    starts = sorted(rng.integers(1, total, size=min(40, max(4, n // 50))))
    # exclusive ~2000-row windows
    for start in starts:
        if want_left <= 0:
            break
        df = pd.read_csv(
            path,
            skiprows=range(1, int(start)),
            nrows=2000,
            names=names,
            header=0,
            on_bad_lines="skip",
        )
        if df.shape[0]:
            take = min(int(df.shape[0]), want_left)
            chunks.append(df.sample(n=take, random_state=seed))
            want_left -= take
    out = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
    return out.sample(n=min(n, len(out)), random_state=seed) if len(out) else out


def describe(path, sample_size=5000):
    """Column statistics computed on a deterministic sample."""
    if not os.path.exists(path):
        return {"error": "file not found"}
    df = sample(path, n=min(sample_size, fast_row_count(path)), seed=42)
    if df.empty:
        return {"error": "empty file"}
    numeric = df.select_dtypes(include=[np.number])
    columns = []
    for c in df.columns:
        info = {
            "name": str(c),
            "dtype": str(df[c].dtype),
            "non_null": int(df[c].notna().sum()),
            "nulls": int(df[c].isna().sum()),
        }
        if c in numeric.columns:
            info.update(
                {
                    "min": _num(numeric[c].min()),
                    "max": _num(numeric[c].max()),
                    "mean": _num(numeric[c].mean()),
                    "std": _num(numeric[c].std()),
                }
            )
        columns.append(info)
    return {
        "path": path,
        "records": fast_row_count(path),
        "columns": columns,
        "sample_size": int(df.shape[0]),
        "note": "statistics computed on a deterministic sample",
    }


def _num(v):
    try:
        if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
            return None
        return round(float(v), 4)
    except (TypeError, ValueError):
        return None


def generate_tasks_streaming(n, path, chunk=100_000, seed=42):
    """Write n synthetic task rows to `path` incrementally.

    Returns (written, took_s). Memory stays bounded: only `chunk` rows are
    built at a time.
    """
    n = int(n)
    if n < 1 or n > MAX_GENERATION_CAP:
        raise ValueError(f"n must be between 1 and {MAX_GENERATION_CAP:,}")
    rng = np.random.default_rng(seed)
    types = config.TASK_TYPES
    t0 = time.time()
    done = 0
    first = True
    while done < n:
        size = int(min(chunk, n - done))
        df = _task_chunk(rng, size, offset=done, types=types)
        df.to_csv(path, mode="w" if first else "a", header=first, index=False)
        first = False
        done += size
    return done, round(time.time() - t0, 3)


def _task_chunk(rng, size, offset, types):
    n = len(types)
    data = {
        "task_id": [f"D{offset + 10000 + i:08d}" for i in range(size)],
        "timestamp": pd.date_range("2026-01-01", periods=size, freq="1ms").strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        ),
        "task_type": [types[i] for i in rng.integers(0, n, size)],
        "data_size_mb": np.round(rng.uniform(0.2, 22.0, size), 2),
        "cpu_cycles_giga": np.round(rng.uniform(0.1, 5.0, size), 2),
        "memory_mb": np.round(rng.uniform(32, 1024, size), 0),
        "deadline_ms": np.round(rng.uniform(90, 900, size), 0),
        "privacy_sensitivity": np.round(rng.uniform(0.05, 1.0, size), 3),
        "security_sensitivity": np.round(rng.uniform(0.05, 1.0, size), 3),
        "arrival_rate": np.round(rng.uniform(1, 40, size), 2),
        "source_node": ["EDGE"] * size,
        "preferred_resource": rng.choice(config.PREFERRED_RESOURCES, size),
        "expected_latency_ms": np.round(rng.uniform(40, 300, size), 1),
        "expected_energy_j": np.round(rng.uniform(0.5, 6.0, size), 2),
        "attack_exposure": np.round(rng.uniform(0.0, 0.9, size), 3),
    }
    df = pd.DataFrame(data)
    label = np.select(
        [
            (df["privacy_sensitivity"] > 0.7) & (df["security_sensitivity"] > 0.6),
            (df["privacy_sensitivity"] > 0.5) | (df["security_sensitivity"] > 0.5),
        ],
        ["high_risk", "sensitive"],
        default="normal",
    )
    df["label"] = label
    return df


def aggregate(path, group_cols, value_cols=None, chunksize=200_000):
    """Streamed group-by/aggregation for large CSVs.

    Returns a DataFrame of group aggregates. Only group-level results are
    kept in memory, which is bounded by the number of groups.
    """
    if not os.path.exists(path):
        return pd.DataFrame()
    group_cols = [group_cols] if isinstance(group_cols, str) else group_cols
    acc = {}
    for i, df in enumerate(read_chunks(path, chunksize=chunksize)):
        for c in group_cols:
            if c not in df.columns:
                df[c] = "NA"
        g = df.groupby(group_cols, dropna=False)
        counts = g.size()
        agg = g[value_cols].mean() if value_cols else None
        for key, c in counts.items():
            k = key if isinstance(key, tuple) else (key,)
            row = acc.setdefault(k, {"count": 0})
            row["count"] += int(c)
            if agg is not None and key in agg.index:
                for vc in value_cols:
                    val = agg.loc[key, vc]
                    v = (
                        float(val)
                        if val is not None
                        and not (isinstance(val, float) and (val != val))
                        else 0.0
                    )
                    prev_count = row["count"] - int(c)
                    prev_mean = row.get(f"mean_{vc}", 0.0)
                    row[f"mean_{vc}"] = (
                        (prev_mean * prev_count + v * int(c)) / row["count"]
                        if row["count"]
                        else 0.0
                    )
    rows = []
    for k, v in sorted(acc.items(), key=lambda kv: -kv[1]["count"]):
        rec = {gc: val for gc, val in zip(group_cols, k)}
        rec.update(v)
        if value_cols:
            for vc in value_cols:
                rec[f"mean_{vc}"] = round(rec.get(f"mean_{vc}", 0.0), 4)
        rows.append(rec)
    return pd.DataFrame(rows)


def to_parquet(path):
    """Convert a CSV to Parquet when pyarrow/fastparquet is available."""
    try:
        import pyarrow  # noqa: F401

        engine = "pyarrow"
    except Exception:  # noqa: BLE001
        try:
            import fastparquet  # noqa: F401

            engine = "fastparquet"
        except Exception:  # noqa: BLE001
            return {"ok": False, "message": "pyarrow/fastparquet not installed"}
    out = os.path.splitext(path)[0] + ".parquet"
    try:
        import pandas as pd

        pd.read_csv(path).to_parquet(out, engine=engine, index=False)
        return {"ok": True, "path": out, "size_bytes": os.path.getsize(out)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "message": str(exc)}


def to_sqlite(path, table="events", chunksize=200_000):
    """Copy a CSV into a SQLite table when sqlite3 is available (stdlib)."""
    import sqlite3

    out = os.path.splitext(path)[0] + ".sqlite3"
    conn = sqlite3.connect(out)
    try:
        written = 0
        for df in read_chunks(path, chunksize=chunksize):
            df.to_sql(
                table, conn, if_exists="append" if written else "replace", index=False
            )
            written += int(df.shape[0])
        conn.commit()
        return {
            "ok": True,
            "path": out,
            "records": written,
            "size_bytes": os.path.getsize(out),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "message": str(exc)}
    finally:
        conn.close()


if __name__ == "__main__":
    out = os.path.join(config.DATASET_DIR, "_bigdata_demo.csv")
    n, t = generate_tasks_streaming(250_000, out, seed=7)
    print(f"generated {n:,} rows in {t}s")
    print("rows:", fast_row_count(out))
    print("sample shape:", sample(out, 100).shape)
    agg = aggregate(out, "label")
    print(agg.head(12).to_string(index=False))
