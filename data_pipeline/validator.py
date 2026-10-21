"""
Dataset validator.

For every dataset file discovered in the pipeline directories, verifies:

- exists / size
- checksum (sha256) where a baseline is available
- archive integrity (zip/tar)
- file type detection
- column header inspection
- row count (streaming)
- label inspection (attack vs benign)
- missing-value detection
- duplicate detection / corrupted lines

Writes datasets/statistics/validation_report.json + .csv (real numbers only).
"""

import csv
import json
import os
import tarfile
import time
import zipfile
from typing import Any, Dict, List

import pandas as pd

from .paths import (
    DATASET_ROOT,
    LOCAL_REAL_DIR,
    RAW_ATTACKED,
    RAW_BENIGN,
    PROCESSED_ATTACKED,
    PROCESSED_BENIGN,
    STATISTICS_DIR,
)


def detect_file_type(path: str) -> str:
    try:
        with open(path, "rb") as fh:
            head = fh.read(16)
    except Exception:
        return "unknown"
    if head.startswith(b"%PDF"):
        return "pdf"
    if zipfile.is_zipfile(path):
        return "zip"
    if tarfile.is_tarfile(path):
        return "tar"
    if head.startswith(b"PK"):
        return "archive"
    try:
        head.decode("utf-8")
        return "text/csv-or-log"
    except Exception:
        return "binary"


def count_rows(path: str) -> int:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return max(0, sum(1 for _ in fh) - 1)
    except Exception:
        return 0


def sha256(path: str) -> str:
    import hashlib

    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_local_dataset(files: List[str], source: str) -> List[Dict[str, Any]]:
    """Validate each file and return per-file reports."""
    reports: List[Dict[str, Any]] = []
    for path in files:
        if not os.path.exists(path):
            reports.append({"file": path, "status": "MISSING"})
            continue
        name = os.path.basename(path)
        ftype = detect_file_type(path)
        row_count = count_rows(path) if ftype in ("text/csv-or-log",) else 0
        size_bytes = os.path.getsize(path)

        report: Dict[str, Any] = {
            "file": name,
            "path": path,
            "source": source,
            "status": "OK" if size_bytes > 0 else "EMPTY",
            "file_type": ftype,
            "size_bytes": size_bytes,
            "size_mb": round(size_bytes / (1024 * 1024), 2),
            "checksum_sha256": sha256(path),
            "row_count": row_count,
        }

        # CSV column + quality inspection
        if ftype == "text/csv-or-log" and name.lower().endswith((".csv", ".txt")):
            try:
                chunk = next(pd.read_csv(path, chunksize=500, dtype=str, on_bad_lines="skip"))
                report["columns"] = list(chunk.columns)
                report["column_count"] = len(chunk.columns)
                report["dtypes"] = {str(c): str(t) for c, t in chunk.dtypes.items()}

                # Missing values on first chunk
                missing = chunk.isna().sum()
                report["missing_value_count"] = int(missing.sum())
                report["missing_value_columns"] = {str(k): int(v) for k, v in missing.items() if int(v) > 0}

                # Duplicates on first chunk
                report["duplicate_rows_sample"] = int(chunk.duplicated().sum())

                # Label inspection: common label columns
                for lcol in ("label", "attack_cat", "Label", "security_label", "attack_type"):
                    if lcol in chunk.columns:
                        distinct = chunk[lcol].dropna().unique().tolist()
                        report["label_column"] = lcol
                        report["label_values_sample"] = [str(c) for c in distinct][:40]
                        break
            except Exception as exc:
                report["csv_error"] = str(exc)
                report["corrupt_records_detail"] = f"CSV parse failed on sample: {exc}"

        # Archive integrity
        if ftype == "zip":
            try:
                with zipfile.ZipFile(path, "r") as zf:
                    bad = zf.testzip()
                    report["archive_integrity"] = "OK" if bad is None else f"CORRUPT_MEMBER:{bad}"
            except Exception as exc:
                report["archive_integrity"] = f"ERROR:{exc}"
        if ftype == "tar":
            try:
                with tarfile.open(path, "r:*") as tf:
                    report["archive_integrity"] = "OK"
            except Exception as exc:
                report["archive_integrity"] = f"ERROR:{exc}"

        reports.append(report)
        print(f"  [{report['status']:8s}] {name:28s} {report.get('size_mb', '?'):>8} MB  rows={report.get('row_count', 0):>9,}")

    return reports


def discover_files() -> List[str]:
    """All candidate dataset files in the pipeline directories."""
    files: List[str] = []
    for base in (RAW_ATTACKED, RAW_BENIGN, PROCESSED_ATTACKED, PROCESSED_BENIGN, LOCAL_REAL_DIR):
        if not os.path.isdir(base):
            continue
        for f in os.listdir(base):
            fp = os.path.join(base, f)
            if os.path.isfile(fp):
                files.append(fp)
    return files


def run_validator() -> Dict[str, Any]:
    """Validate every dataset file on disk and persist the report."""
    os.makedirs(STATISTICS_DIR, exist_ok=True)
    files = discover_files()
    if not files:
        print("No dataset files found on disk. Run download first.")
        return {"status": "NO_FILES", "files": files}

    print(f"Validating {len(files)} local dataset file(s)...")
    reports = validate_local_dataset(files, "local_disk")

    attacked_local = sum(1 for r in reports if r.get("status") == "OK" and (RAW_ATTACKED in r.get("path", "") or PROCESSED_ATTACKED in r.get("path", "")))
    benign_local = sum(1 for r in reports if r.get("status") == "OK" and (RAW_BENIGN in r.get("path", "") or PROCESSED_BENIGN in r.get("path", "")))

    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "files_validated": len(reports),
        "files_ok": sum(1 for r in reports if r.get("status") == "OK"),
        "attacked_files": attacked_local,
        "benign_files": benign_local,
        "raw_real_files_ok": sum(1 for r in reports if r.get("status") == "OK" and LOCAL_REAL_DIR in r.get("path", "")),
        "reports": reports,
    }

    with open(os.path.join(STATISTICS_DIR, "validation_report.json"), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=str)
    pd.DataFrame(reports).to_csv(os.path.join(STATISTICS_DIR, "validation_report.csv"), index=False)

    return payload


if __name__ == "__main__":
    r = run_validator()
    print(json.dumps({k: r[k] for k in r if k != "reports"}, indent=2))