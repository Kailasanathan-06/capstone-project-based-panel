"""
Dataset downloader.

Checks the official catalogue; for every dataset whose files are not yet on
disk it prints either a direct download command or MANUAL DOWNLOAD REQUIRED
with the official page URL.  Files that are already downloaded are left
unchanged.

Automated download is only attempted for datasets that are publicly
accessible without registration.  Nothing is ever fabricated.
"""

import csv
import hashlib
import json
import os
import shutil
import sys
import time
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

from .paths import (
    DATASET_CATALOG,
    DATASET_ROOT,
    LOCAL_REAL_DIR,
    RAW_ATTACKED,
    RAW_BENIGN,
    METADATA_DIR,
)


CHUNK = 1 << 16  # 64 KB


def sha256(path: str, length: int = 65536) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(length)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _safe_filename(name: str) -> str:
    return name.replace(" ", "_").replace("/", "_").replace("\\", "_")


def _write_metadata(entry: Dict[str, Any], file_path: str, status: str) -> None:
    fname = _safe_filename(entry["name"]) + ".json"
    meta = {
        "name": entry["name"],
        "type": entry["type"],
        "source": entry["official_url"],
        "download_url": entry.get("download_url"),
        "doi": entry.get("doi"),
        "format": entry["format"],
        "size": "",
        "record_count": "",
        "features": [],
        "attack_types": entry.get("attack_types", []),
        "benign_available": entry.get("benign_available", False),
        "label_key": entry.get("label_key"),
        "category_key": entry.get("category_key"),
        "benign_value": entry.get("benign_value"),
        "license": entry.get("license", ""),
        "download_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "download_status": status,
        "local_path": file_path,
        "checksum_sha256": sha256(file_path) if file_path and os.path.exists(file_path) else "",
    }
    os.makedirs(METADATA_DIR, exist_ok=True)
    with open(os.path.join(METADATA_DIR, fname), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)


def _locate_nsl_kdd_local() -> List[Dict[str, str]]:
    """Return local NSL-KDD CSVs found on disk with their paths."""
    results: List[Dict[str, str]] = []
    for csv_path in [
        os.path.join(LOCAL_REAL_DIR, "nsl_kdd_combined.csv"),
        os.path.join(LOCAL_REAL_DIR, "nsl_kdd_train.csv"),
        os.path.join(LOCAL_REAL_DIR, "nsl_kdd_test.csv"),
    ]:
        if os.path.exists(csv_path):
            results.append(
                {
                    "path": csv_path,
                    "name": os.path.basename(csv_path),
                    "size": os.path.getsize(csv_path),
                }
            )
    return results


def _fast_row_count(path: str) -> int:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return sum(1 for _ in fh) - 1
    except Exception:
        return 0


def download_nsl_kdd(force: bool = False) -> Dict[str, Any]:
    """Handle NSL-KDD: validate local presence, write metadata,
    and keep an untouched copy of the original combined file in raw/attacked/."""
    local_files = _locate_nsl_kdd_local()
    if not local_files:
        return {"status": "MISSING", "message": (
            "NSL-KDD files not found on disk. Official source: https://www.unb.ca/cic/datasets/nsl.html. "
            "Download KDDTrain+.txt and KDDTest+.txt manually and place them in datasets/real/."
        )}

    entry = next(e for e in DATASET_CATALOG if e["name"] == "NSL-KDD")
    records = 0
    for lf in local_files:
        _write_metadata(entry, lf["path"], "DOWNLOADED_LOCALLY")
        if "combined" in lf["name"]:
            records = _fast_row_count(lf["path"])

    # Keep an immutable copy of the original combined dataset in raw/attacked
    combined_src = next((lf["path"] for lf in local_files if "combined" in lf["name"]), None)
    if combined_src:
        os.makedirs(RAW_ATTACKED, exist_ok=True)
        raw_copy = os.path.join(RAW_ATTACKED, "nsl_kdd_combined.csv")
        if not os.path.exists(raw_copy):
            shutil.copy2(combined_src, raw_copy)
            print(f"  raw copy stored (unchanged): {raw_copy}")

    return {
        "status": "DOWNLOADED_LOCALLY",
        "files": local_files,
        "records_on_disk": records,
        "metadata": os.path.join(METADATA_DIR, "NSL-KDD.json"),
    }


def _print_manual_download(entry: Dict[str, Any]) -> None:
    print(f"\n{'=' * 60}")
    print(f"  MANUAL DOWNLOAD REQUIRED: {entry['name']}")
    print(f"  Type: {entry['type'].upper()}")
    print(f"  Format: {entry['format']}")
    print(f"  Official page: {entry['official_url']}")
    if entry.get("download_url"):
        print(f"  Download link (login required): {entry['download_url']}")
    if entry.get("doi"):
        print(f"  DOI: {entry['doi']}")
    print(f"  Expected records: {entry['records_expected']:,}")
    print(f"  Expected features: {entry['features']}")
    print(f"  License: {entry.get('license', 'See official page')}")
    print(f"  Target directory: {RAW_ATTACKED if entry['type'] == 'attacked' else RAW_BENIGN}")
    print(f"  After download, run: python scripts/validate_datasets.py")
    print(f"{'=' * 60}\n")


def download_unsw_nb15() -> Dict[str, Any]:
    """Attempt UNSW-NB15. Always manual (UNSW SharePoint)."""
    entry = next(e for e in DATASET_CATALOG if e["name"] == "UNSW-NB15")
    _print_manual_download(entry)
    _write_metadata(entry, "", "MANUAL_DOWNLOAD_REQUIRED")
    return {
        "status": "MANUAL_DOWNLOAD_REQUIRED",
        "official_url": entry["official_url"],
        "target_dir": RAW_ATTACKED,
        "files_needed": [
            "UNSW-NB15_1.csv",
            "UNSW-NB15_2.csv",
            "UNSW-NB15_3.csv",
            "UNSW-NB15_4.csv",
            "UNSW_NB15_training-set.csv",
            "UNSW_NB15_testing-set.csv",
        ],
    }


def download_dataset(name: str, force: bool = False) -> Dict[str, Any]:
    """Download or document a single dataset by name."""
    entry = next((e for e in DATASET_CATALOG if e["name"].lower() == name.lower()), None)
    if entry is None:
        raise KeyError(f"Unknown dataset: {name}")

    if entry["name"] == "NSL-KDD":
        return download_nsl_kdd(force=force)

    if entry["name"] == "UNSW-NB15":
        return download_unsw_nb15()

    _print_manual_download(entry)
    _write_metadata(entry, "", "MANUAL_DOWNLOAD_REQUIRED")
    return {
        "status": "MANUAL_DOWNLOAD_REQUIRED",
        "official_url": entry["official_url"],
        "target_dir": RAW_ATTACKED,
    }


def run_downloader() -> Dict[str, Any]:
    """Download/document all datasets. Returns per-dataset status dict."""
    results: Dict[str, Any] = {}
    for entry in DATASET_CATALOG:
        print(f"\n--- {entry['name']} ---")
        results[entry["name"]] = download_dataset(entry["name"])
        print(f"  Status: {results[entry['name']]['status']}")
    return results


def _extract_nsl_kdd_to_raw() -> Optional[str]:
    """Copy NSL-KDD combined file to datasets/raw/attacked/ and
    datasets/raw/benign/ for a canonical attacked/benign split."""
    combined = os.path.join(LOCAL_REAL_DIR, "nsl_kdd_combined.csv")
    if not os.path.exists(combined):
        return None
    import pandas as pd

    print("Splitting NSL-KDD into attacked/benign partitions in raw/...")
    chunks = pd.read_csv(
        combined,
        chunksize=200000,
        dtype=str,
        encoding="utf-8",
        on_bad_lines="skip",
    )
    attack_parts: List[pd.DataFrame] = []
    benign_parts: List[pd.DataFrame] = []

    for chunk in chunks:
        label_col = "label" if "label" in chunk.columns else " label"
        chunk[label_col] = chunk[label_col].astype(str).str.strip().str.rstrip(".").str.lower()
        is_normal = chunk[label_col] == "normal"
        if is_normal.any():
            benign_parts.append(chunk[is_normal].copy())
        if (~is_normal).any():
            attack_parts.append(chunk[~is_normal].copy())

    if benign_parts:
        benign_df = pd.concat(benign_parts, ignore_index=True)
        benign_out = os.path.join(RAW_BENIGN, "nsl_kdd_benign.csv")
        benign_df.to_csv(benign_out, index=False)
        print(f"  -> benign: {len(benign_df):,} rows -> {os.path.basename(benign_out)}")
    if attack_parts:
        attack_df = pd.concat(attack_parts, ignore_index=True)
        attack_out = os.path.join(RAW_ATTACKED, "nsl_kdd_attacked.csv")
        attack_df.to_csv(attack_out, index=False)
        print(f"  -> attacked: {len(attack_df):,} rows -> {os.path.basename(attack_out)}")

    return "Split completed"


if __name__ == "__main__":
    results = run_downloader()
    print("\n\nSPLIT PHASE")
    _extract_nsl_kdd_to_raw()