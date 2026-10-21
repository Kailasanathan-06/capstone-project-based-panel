#!/usr/bin/env python3
"""
Validate datasets and write the validation report.

usage:
    python scripts/validate_datasets.py

Reads every file under datasets/raw/, datasets/processed/ and datasets/real/,
computes real size/checksum/row-count/dtype/label statistics and writes:

    datasets/statistics/validation_report.json
    datasets/statistics/validation_report.csv
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_pipeline.validator import run_validator


def main() -> int:
    payload = run_validator()
    print("\nVALIDATION SUMMARY")
    print(f"  Files validated: {payload['files_validated']}")
    print(f"  Files OK:        {payload['files_ok']}")
    print(f"  Attacked files:  {payload['attacked_files']}")
    print(f"  Benign files:    {payload['benign_files']}")
    print(f"  Real NSL-KDD:    {payload['raw_real_files_ok']} file(s) OK")
    print("\nReports written to datasets/statistics/.")
    return 0 if payload["files_ok"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())