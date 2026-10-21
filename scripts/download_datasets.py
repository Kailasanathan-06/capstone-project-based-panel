#!/usr/bin/env python3
"""
Download datasets (or document manual downloads).

usage:
    python scripts/download_datasets.py [dataset_name ...]

If no name is given, all datasets in the catalogue are processed.
Prints MANUAL DOWNLOAD REQUIRED for sources that need a click-through.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_pipeline.downloader import download_dataset, run_downloader
from data_pipeline.paths import DATASET_CATALOG


def main() -> int:
    args = [a for a in sys.argv[1:]]
    if args:
        results = {}
        for name in args:
            print(f"\n{'=' * 60}\n{name}\n{'=' * 60}")
            try:
                results[name] = download_dataset(name)
            except KeyError as exc:
                print(f"Unknown dataset: {exc}")
                return 2
    else:
        results = run_downloader()

    print("\n\nSUMMARY")
    for name, status in results.items():
        print(f"  {name:20s} -> {status.get('status', '?')}")
    print("\nThe NSL-KDD real dataset is already present locally in datasets/real/.")
    print("For UNSW-NB15 (and other UNSW/UNB datasets) manual download is required;")
    print("see the official pages in docs/DATASET_SELECTION_REPORT.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())