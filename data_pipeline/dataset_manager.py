"""
DatasetManager — high-level orchestration.

Coordinates:
  download, validate, extract, clean, preprocess, feature-engineer,
  statistics, metadata
and (optionally) registers rows in the Django ``datasets.Dataset`` model
(MySQL) and can upload selected datasets to Google Drive.

This module is importable both by plain scripts and by Django management
commands.
"""

import json
import os
from typing import Any, Dict, List, Optional

from .paths import (
    DATASET_CATALOG,
    DATASET_ROOT,
    METADATA_DIR,
    PROCESSED_ATTACKED,
    PROCESSED_BENIGN,
    RAW_ATTACKED,
    RAW_BENIGN,
    STATISTICS_DIR,
    LOCAL_REAL_DIR,
)


class DatasetManager:
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.statistics: Dict[str, Any] = {}
        self._ready = False

    # ------------------------------------------------------------------ util
    def _log(self, msg: str) -> None:
        if self.verbose:
            print(msg)

    def fast_rows(self, path: str) -> int:
        if not os.path.exists(path):
            return 0
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                return max(0, sum(1 for _ in fh) - 1)
        except Exception:
            return 0

    # ------------------------------------------------------------------ steps
    def run_download(self) -> Dict[str, Any]:
        from .downloader import run_downloader

        self._log("=1/7 DOWNLOAD=")
        return run_downloader()

    def run_validate(self) -> Dict[str, Any]:
        from .validator import run_validator

        self._log("=2/7 VALIDATE=")
        return run_validator()

    def run_extract(self) -> Dict[str, Any]:
        from .extractor import extract_archive

        self._log("=3/7 EXTRACT=")
        results: Dict[str, Any] = {}
        for d in (RAW_ATTACKED, RAW_BENIGN):
            for entry in os.listdir(d):
                path = os.path.join(d, entry)
                if not os.path.isfile(path):
                    continue
                if path.lower().endswith((".zip", ".tar", ".gz")):
                    results[path] = extract_archive(path, d)
        return results

    def run_clean(self) -> Dict[str, Any]:
        from .cleaner import run_cleaner

        self._log("=4/7 CLEAN=")
        return run_cleaner()

    def run_preprocess(self) -> Dict[str, Any]:
        from .preprocessor import run_preprocessor

        self._log("=5/7 PREPROCESS=")
        return run_preprocessor()

    def run_feature_engineering(self) -> Dict[str, Any]:
        from .feature_engineering import run_feature_engineering

        self._log("=6/7 FEATURE ENGINEERING=")
        return run_feature_engineering()

    def run_statistics(self) -> Dict[str, Any]:
        from .statistics import compute_all_statistics

        self._log("=7/7 STATISTICS=")
        self.statistics = compute_all_statistics()
        return self.statistics

    # ------------------------------------------------------------------ full
    def run_all(self, force_clean: bool = False) -> Dict[str, Any]:
        self.run_download()
        self.run_validate()
        extra = self.run_extract()
        if extra:
            self.run_clean()  # re-run cleaner after extraction if anything new appeared
        else:
            self.run_clean()
        self.run_preprocess()
        self.run_feature_engineering()
        self.run_statistics()
        return self.statistics

    # ------------------------------------------------------------------ views
    def registry_overview(self) -> Dict[str, Any]:
        """Data for the dataset dashboard (real values only)."""
        stats = self.statistics or {}
        attacked_rows = (
            stats.get("processed", {}).get("attacked_rows", 0)
            if stats
            else self.fast_rows(os.path.join(PROCESSED_ATTACKED, "nsl_kdd_attacked.csv"))
        )
        benign_rows = (
            stats.get("processed", {}).get("benign_rows", 0)
            if stats
            else self.fast_rows(os.path.join(PROCESSED_BENIGN, "nsl_kdd_benign.csv"))
        )
        total_records = attacked_rows + benign_rows
        storage = stats.get("storage_usage") if stats else {"mb": 0.0, "gb": 0.0, "bytes": 0}
        return {
            "total_datasets": 0 + sum(1 for e in DATASET_CATALOG),
            "attacked_datasets": sum(1 for e in DATASET_CATALOG if e["type"] == "attacked"),
            "benign_datasets": sum(1 for e in DATASET_CATALOG if e["type"] == "benign"),
            "total_records": total_records,
            "processed_records": total_records,
            "storage_usage_mb": storage.get("mb", 0.0),
            "storage_usage_gb": storage.get("gb", 0.0),
            # real per-dataset rows actually on disk
            "local_real_rows": sum(self.fast_rows(os.path.join(LOCAL_REAL_DIR, f)) for f in os.listdir(LOCAL_REAL_DIR) if os.path.isfile(os.path.join(LOCAL_REAL_DIR, f)) and f.endswith((".csv", ".txt"))),
            "attacked_rows": attacked_rows,
            "benign_rows": benign_rows,
            "processed_attack_path": os.path.join(PROCESSED_ATTACKED, "nsl_kdd_attacked.csv"),
            "processed_benign_path": os.path.join(PROCESSED_BENIGN, "nsl_kdd_benign.csv"),
            "generated_at": pd_now(),
        }

    def dataset_cards(self) -> List[Dict[str, Any]]:
        """Cards shown in the dashboard, real values only."""
        cards: List[Dict[str, Any]] = []
        for entry in DATASET_CATALOG:
            rows_local = 0
            droot = LOCAL_REAL_DIR if entry["name"] == "NSL-KDD" else RAW_ATTACKED
            for f in os.listdir(droot) if os.path.isdir(droot) else []:
                fp = os.path.join(droot, f)
                if os.path.isfile(fp) and f.endswith((".csv", ".txt")):
                    rows_local += self.fast_rows(fp)
            cards.append(
                {
                    "name": entry["name"],
                    "type": entry["type"].upper(),
                    "records_expected": entry["records_expected"],
                    "records_local": rows_local,
                    "size_mb": round(
                        sum(os.path.getsize(os.path.join(droot, f)) for f in os.listdir(droot) if os.path.isfile(os.path.join(droot, f))) / (1024 * 1024),
                        2,
                    ),
                    "status": "LOCAL" if rows_local else "MANUAL_DOWNLOAD_REQUIRED",
                    "source": entry["official_url"],
                    "processing_status": "PROCESSED" if entry["name"] == "NSL-KDD" else "RAW_ONLY",
                    "drive_status": "NOT_UPLOADED",
                    "attack_types": entry.get("attack_types", []),
                    "format": entry["format"],
                }
            )
        return cards

    def write_metadata_report(self) -> str:
        payload = {
            "datasets": DATASET_CATALOG,
            "overview": self.registry_overview(),
            "cards": self.dataset_cards(),
            "statistics": self.statistics if self.statistics else None,
        }
        os.makedirs(METADATA_DIR, exist_ok=True)
        out = os.path.join(METADATA_DIR, "dataset_manager_report.json")
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, default=str)
        return out


def pd_now() -> str:
    import time

    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())