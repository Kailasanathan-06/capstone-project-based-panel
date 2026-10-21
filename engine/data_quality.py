"""
Data Quality Engine
===================
Streaming validation for large CSVs:

  * missing values
  * duplicate records (detected on an identifier column when present)
  * invalid/empty identifiers
  * non-numeric values in numeric columns
  * negative / NaN / infinite numeric values
  * out-of-range probability columns (out of [0,1])
  * unknown task types / labels

Produces a DATA QUALITY SCORE (percent of valid records) and supports
[Clean] (stream invalid rows out to a new file), [Reject] (report only) and
[Export Report] (JSON + CSV detail).

Designed to stay memory-bounded on 1M+ row files.
"""

import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

import config  # noqa: E402

NUMERIC_COLUMNS = [
    "data_size_mb",
    "cpu_cycles_giga",
    "memory_mb",
    "deadline_ms",
    "arrival_rate",
    "expected_latency_ms",
    "expected_energy_j",
    "attack_exposure",
]
RANGE_COLUMNS = ["privacy_sensitivity", "security_sensitivity", "attack_exposure"]
REQUIRED_COLUMNS = ["task_id"]
KNOWN_LABELS = {"normal", "sensitive", "high_risk", "safe", "warning"}
KNOWN_TYPES = set(config.TASK_TYPES)


class QualityReport:
    def __init__(self, path, analyzer=None):
        self.path = path
        self.analyzer = analyzer or DataQuality()
        self.report = None

    def analyze(self, chunksize=100_000):
        self.report = self.analyzer.analyze_file(self.path, chunksize)
        return self.report

    def clean_path(self):
        base, ext = os.path.splitext(self.path)
        return f"{base}_clean{ext}"


class DataQuality:
    """Chunked CSV quality analysis producing a JSON-serialisable report."""

    def __init__(self, numeric_columns=None, range_columns=None):
        self.numeric_columns = list(numeric_columns or NUMERIC_COLUMNS)
        self.range_columns = list(range_columns or RANGE_COLUMNS)

    # ------------------------------------------------------------------
    def analyze_file(self, path, chunksize=100_000):
        if not os.path.exists(path):
            return {"ok": False, "error": "file not found"}
        total = valid = 0
        missing = Counter()
        duplicate = 0
        bad_id = bad_numeric = out_of_range = bad_label = bad_type = 0
        issues_by_column = Counter()
        seen_ids = set()
        had_id_column = False
        columns = None
        seen_columns = set()

        for df in read_chunks(path, chunksize=chunksize):
            if df.empty:
                continue
            total += int(df.shape[0])
            columns = [str(c) for c in df.columns]
            seen_columns.update(columns)

            id_col = "task_id" if "task_id" in df.columns else columns[0]
            id_series = df[id_col].astype(str).str.strip()
            had_id_column = had_id_column or (id_col == "task_id")

            dup_in_chunk = int(id_series.duplicated().sum())
            # cross-chunk duplicates
            if seen_ids is not None:
                first_time = ~id_series.isin(seen_ids)
                dup_in_chunk += int(id_series[~first_time].nunique())
                seen_ids.update(id_series[first_time].tolist())
            duplicate += dup_in_chunk

            bad_row = pd.Series(False, index=df.index)

            # missing values
            for c in df.columns:
                m = df[c].isna().sum()
                if m:
                    missing[c] += int(m)
                bad_row |= df[c].isna()

            # invalid identifiers
            empty_id = id_series.eq("") | id_series.eq("nan") | id_series.eq("None")
            bad_id += int(empty_id.sum())
            bad_row |= empty_id

            # numeric validity (numeric columns present in this chunk)
            present_num = [c for c in self.numeric_columns if c in df.columns]
            for c in present_num:
                series = df[c]
                if series.dtype == object:
                    numeric = pd.to_numeric(series, errors="coerce")
                    coerced_bad = numeric.isna() & series.notna()
                    bad_numeric += int(coerced_bad.sum())
                    bad_row |= coerced_bad
                    series = numeric
                else:
                    bad_row |= pd.isna(series)
                bad_neg = pd.Series(series < 0, index=df.index).fillna(False)
                bad_inf = pd.Series(np.isinf(series.fillna(0.0)), index=df.index)
                bad_row |= bad_neg | bad_inf
                bad_numeric += int((bad_neg | bad_inf).sum())

            # out-of-range probability columns
            for c in self.range_columns:
                if c in df.columns:
                    nums = pd.to_numeric(df[c], errors="coerce")
                    oor = (nums < 0.0) | (nums > 1.0)
                    oor = oor.fillna(False)
                    out_of_range += int(oor.sum())
                    bad_row |= oor

            # unexpected label / task_type categories
            if "label" in df.columns:
                unknown = (
                    ~df["label"].astype(str).str.strip().str.lower().isin(KNOWN_LABELS)
                )
                bad_label += int(unknown.sum())
                bad_row |= unknown
            if "task_type" in df.columns:
                unknown_t = ~df["task_type"].astype(str).str.strip().isin(KNOWN_TYPES)
                bad_type += int(unknown_t.sum())
                bad_row |= unknown_t

            valid += int((~bad_row).sum())

        if total == 0:
            return {"ok": False, "error": "empty dataset"}

        quality_score = round(100.0 * valid / total, 1)
        return {
            "ok": True,
            "path": path,
            "records": total,
            "valid": valid,
            "invalid": total - valid,
            "duplicates": duplicate,
            "missing_values": sum(missing.values()),
            "missing_by_column": dict(missing),
            "invalid_identifiers": bad_id,
            "invalid_numeric": bad_numeric,
            "out_of_range": out_of_range,
            "unknown_labels": bad_label,
            "unknown_types": bad_type,
            "issues": {
                "missing": dict(missing),
                "duplicate": duplicate,
                "bad_id": bad_id,
                "bad_numeric": bad_numeric,
                "out_of_range": out_of_range,
                "bad_label": bad_label,
                "bad_type": bad_type,
            },
            "quality_score": quality_score,
            "grade": grade(quality_score),
            "columns": list(columns) if columns else [],
            "has_id_column": had_id_column,
            "source": (
                "SYNTHETIC"
                if os.path.basename(path).startswith(("tasks_", "D"))
                else "UNKNOWN"
            ),
        }

    # ------------------------------------------------------------------
    def clean_file(self, path, out_path=None, chunksize=100_000):
        """Stream invalid rows to a clean file. Returns the report too."""
        out_path = out_path or _clean_sibling(path)
        if os.path.exists(out_path):
            os.remove(out_path)
        report = self.analyze_file(path, chunksize)
        if not report.get("ok"):
            return {"ok": False, "error": report.get("error", "analysis failed")}
        id_col = "task_id" if report.get("has_id_column") else report["columns"][0]
        written = 0
        for df in read_chunks(path, chunksize=chunksize):
            mask = _valid_mask(df, self, id_col)
            clean = df[mask]
            clean.to_csv(out_path, mode="a", header=written == 0, index=False)
            written += int(clean.shape[0])
        report["clean_path"] = out_path
        report["clean_records"] = written
        return report

    # ------------------------------------------------------------------
    def export_report(self, path, out_json=None, out_csv=None):
        report = self.analyze_file(path)
        out_json = out_json or os.path.join(config.DATASET_DIR, "quality_report.json")
        with open(out_json, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, default=str)
        rows = [
            {"issue": k, "count": v} for k, v in report.get("issues", {}).items() if v
        ]
        out_csv = out_csv or os.path.join(config.DATASET_DIR, "quality_issues.csv")
        pd.DataFrame(rows).to_csv(out_csv, index=False)
        return {"json": out_json, "csv": out_csv, "report": report}


def _valid_mask(df, qq, id_col):
    bad = pd.Series(False, index=df.index)
    for c in df.columns:
        bad |= df[c].isna()
    ids = df[id_col].astype(str).str.strip()
    bad |= ids.eq("") | ids.eq("nan") | ids.eq("None")
    for c in qq.numeric_columns:
        if c in df.columns:
            nums = pd.to_numeric(df[c], errors="coerce")
            bad |= nums.isna() & df[c].notna()
            bad |= (nums < 0).fillna(False) | np.isinf(nums.fillna(0.0))
    for c in qq.range_columns:
        if c in df.columns:
            nums = pd.to_numeric(df[c], errors="coerce")
            bad |= ((nums < 0.0) | (nums > 1.0)).fillna(False)
    if "label" in df.columns:
        bad |= ~df["label"].astype(str).str.strip().str.lower().isin(KNOWN_LABELS)
    if "task_type" in df.columns:
        bad |= ~df["task_type"].astype(str).str.strip().isin(KNOWN_TYPES)
    return ~bad


def grade(score):
    if score >= 99.5:
        return "EXCELLENT"
    if score >= 97:
        return "GOOD"
    if score >= 90:
        return "ACCEPTABLE"
    return "POOR"


def _clean_sibling(path):
    base, ext = os.path.splitext(path)
    return f"{base}_clean{ext}"


def read_chunks(path, chunksize=100_000):
    default = {
        "chunksize": chunksize,
        "low_memory": False,
        "encoding": "utf-8",
        "on_bad_lines": "skip",
    }
    for df in pd.read_csv(path, **default):
        yield df


if __name__ == "__main__":
    q = DataQuality()
    demo = os.path.join(config.DATASET_DIR, "tasks_10000.csv")
    rep = q.analyze_file(demo)
    print(
        f"Records: {rep['records']:,}  Valid: {rep['valid']:,}  "
        f"Score: {rep['quality_score']}% ({rep['grade']})"
    )
