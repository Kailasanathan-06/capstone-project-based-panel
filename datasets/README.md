# Datasets — SecureDT Project

Research data collection for **Intelligent and Secure Task Scheduling for
Digital Twin-Enabled Edge–Cloud Networks**.

This directory is the single source of truth for every dataset used in the
project. It is divided into **public / real** datasets (downloaded or
documented from official sources) and **synthetic / simulated** datasets
(produced locally by `scripts/generate_dataset.py` with fixed seeds).

The pipeline **never fabricates** record counts, sizes or labels. Every number
in `metadata/`, `statistics/` and the dashboard is computed from the actual
files on disk.

## Directory layout

```
datasets/
├── raw/                       # untouched original downloads
│   ├── attacked/              #   attacked/malicious datasets (original files)
│   └── benign/                #   benign/normal datasets (original files)
├── real/                      # real public datasets imported locally (NSL-KDD)
├── processed/                 # cleaned, project-ready copies (AI/ML input)
│   ├── attacked/              #   attacked/malicious, ready for training
│   └── benign/                #   benign/normal, ready for training
├── metadata/                  # one JSON metadata record per dataset
├── statistics/                # validation / statistical reports (JSON + CSV)
├── README.md                  # this file
```

**Never modify files under `raw/`.** Raw files are the immutable originals.
All cleaning, deduplication and feature engineering writes to `processed/`.

## Dataset type definitions

| Type      | Meaning                                                              | Examples in this project |
|-----------|----------------------------------------------------------------------|--------------------------|
| ATTACKED  | Contains malicious traffic/events with attack labels + benign labels | UNSW-NB15, NSL-KDD       |
| BENIGN    | Normal / non-malicious activity only                                 | UNSW-NB15 "Normal" class, NSL-KDD "normal" class |

Mixed datasets (benign *and* attack labels in one file) are kept in
`raw/attacked/` AND split into clean `processed/attacked/` and
`processed/benign/` partitions. The split is fully documented in the metadata
file (original dataset, filtering method, original label, filtered label,
record count).

## Real datasets

| Dataset      | Type                        | Official source                                   |
|--------------|-----------------------------|---------------------------------------------------|
| UNSW-NB15    | ATTACKED (9 attack classes + Normal) | https://research.unsw.edu.au/projects/unsw-nb15-dataset |
| NSL-KDD      | ATTACKED (24 attack classes + normal) | https://www.unb.ca/cic/datasets/nsl.html          |

## Synthetic datasets

Produced locally by `scripts/generate_dataset.py` (seed 42, vectorised).
They use the same `raw/` + `processed/` separation and are always labelled
`SYNTHETIC DATA` in the UI — never presented as real data.

## Pipeline usage

```bash
python scripts/download_datasets.py      # fetch or document official downloads
python scripts/validate_datasets.py      # validate local files + write report
python manage.py download_datasets       # same, as a Django command
python manage.py validate_datasets
python manage.py preprocess_datasets     # clean + feature-engineer to processed/
python manage.py dataset_statistics      # compute statistics from real files
```

## Integrity rules

1. Do not invent download URLs — use the official source pages in `metadata/`.
2. Do not overwrite raw files.
3. The `ATTACKED` / `BENIGN` separation is preserved everywhere.
4. Every computed metric (rows, sizes, class counts) comes from the files on
   disk, never from a constant.
5. Licensing: redistribution of public datasets is only allowed under the
   terms of the source license (see each `metadata/*.json`). The deliverable
   ZIP contains metadata + download instructions rather than raw data where
   redistribution is not permitted.