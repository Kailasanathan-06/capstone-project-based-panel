# Datasets Guide

## Synthetic Datasets (included)

Produced with a fixed seed (`config.DATASET_SEED = 42`); fully offline. See
`REPRODUCIBILITY.md` for the full table.

## Public Reference Datasets (registry only)

The Dataset Manager (`/datasets`) exposes a **registry** of well-known
public Intrusion Detection / IDS datasets with official source URLs,
licenses and attack-class coverage. SecureDT **never downloads these by
default**; they are provided so reviewers can see how the platform would be
fed real-world traffic. Note: the code is licenced for educational use and
the public datasets carry their own terms.

| Dataset | Rows (approx.) | Attack classes | License |
|---|---|---|---|
| CIC-IDS2017 | 2.8M | Brute Force, DDoS, Web attacks … | Public, for research |
| CSE-CIC-IDS2018 | 16M | DDoS, DoS, Infiltration … | Public, for research |
| UNSW-NB15 | 2.5M | Fuzzers, Analysis, Backdoors … | Public, for research |
| TON_IoT | 461M | Scanning, XSS, DDoS … | Public, for research |
| BoT-IoT | 73M | DDoS, DoS, Scan, Theft … | Public, for research |

## Validation

```bash
python scripts/validate_dataset.py
python scripts/dataset_check.py
```

## Data Quality (new)

`/api/datasets/quality` runs a full quality report on any CSV in the project
dataset directory: row/column counts, missing values, duplicate rows, invalid
numeric fields, out-of-range values, label balance and a 0-100 quality score
with letter grade. `/api/datasets/clean` writes a cleaned copy; the report
can be exported as JSON/CSV via `/api/export/quality`.

## Normalisation (new)

`/api/datasets/normalize` converts task, attack and storage CSVs into a
single UnifiedEvent schema (21 fields + column metadata preserved), so the
security timeline, analytics and downstream labs read one canonical shape
regardless of source file.

## Big-Data (new)

`/api/datasets/generate` streams up to 5 M rows deterministically; the loaded
file can be previewed, described, aggregated and exported. All operations are
chunked, so 1 M+ rows stay within normal laptop memory.