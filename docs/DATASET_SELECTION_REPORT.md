# Dataset Selection Report

**Project:** Intelligent and Secure Task Scheduling for Digital Twin-Enabled Edge–Cloud Networks

**Date:** 2026-09-13

**Scope:** Selection of two clearly separated dataset types —

1. **ATTACKED / malicious** dataset (attack samples + labels, multiple categories)
2. **BENIGN / non-attacked** dataset (normal traffic, no attack labels)

---

## 1. Evaluation summary

The table below shows the datasets evaluated. All information comes from the
**official dataset pages** (linked) or the datasets' official publications —
no record counts or labels are invented.

### Candidates evaluated

| Dataset                    | Type            | Official source                                                | Format        | Records          | Attack classes            | Benign available | Cloud/Edge context |
|----------------------------|-----------------|----------------------------------------------------------------|---------------|------------------|---------------------------|------------------|--------------------|
| UNSW-NB15                  | ATTACKED (mixed) | [UNSW Canberra](https://research.unsw.edu.au/projects/unsw-nb15-dataset) | CSV/ARFF/PCAP | 2,540,044 | 9 (Generic, Exploits, Fuzzers, DoS, Reconnaissance, Analysis, Backdoors, Shellcode, Worms) | Yes (Normal class) | Edge/MEC-style network flows |
| CIC-IDS2017                | ATTACKED (mixed) | [UNB CIC](https://www.unb.ca/cic/datasets/ids-2017.html)           | CSV/PCAP      | 2,886,020 | 8+ (DoS, DDoS, Brute Force, Web Attack, Infiltration, Botnet, PortScan) | Yes (Benign) | Cloud network flows |
| CSE-CIC-IDS2018            | ATTACKED (mixed) | [UNB CIC / AIT](https://www.unb.ca/cic/datasets/ids-2018.html)     | CSV           | ±16,800,000 | 8+ (DoS, DDoS, Botnet, Brute Force, SQL Injection, XSS, Infiltration) | Yes (Benign) | Cloud network flows |
| CIC-DDoS2019               | ATTACKED        | [UNB CIC](https://www.unb.ca/cic/datasets/ddos-2019.html)          | CSV/PCAP      | ±50,000,000 | DDoS families (DrDoS, SYN, DNS, etc.) | Limited | Cloud/edge attacks |
| BoT-IoT                    | ATTACKED (mixed) | [UNSW Canberra](https://research.unsw.edu.au/projects/bot-iot-dataset) | CSV/PCAP      | 73,370,044 | 4 categories (DoS, DDoS, Recon, Theft) | Yes (Normal) | IoT / smart-home |
| TON_IoT                    | ATTACKED (mixed) | [UNSW Canberra](https://research.unsw.edu.au/projects/toniot-datasets) | CSV           | 461,043+ (Network) | 10+ (scanning, dos, ddos, injection, xss, password, ransomware, backdoor, mitm, sql_injection) | Yes (normal) | IoT / Industry 4.0 / Edge |
| NSL-KDD (imported locally) | ATTACKED (mixed) | [UNB CIC (NSL-KDD)](https://www.unb.ca/cic/datasets/nsl.html)       | CSV           | 148,517 | 22 attack subtypes in 4 categories (DoS, Probe, R2L, U2R) | Yes (normal) | Legacy network flows |

### Selection criteria applied

- Suitable for **Edge / MEC / Cloud / network security / intrusion detection**
  (all candidates satisfy this).
- **Digital Twin + task scheduling + security-risk prediction** → require
  flow/telemetry features that a scheduler can turn into an **attack
  probability / risk score**.
- **AI/ML classification + anomaly detection** → require labelled
  attack/benign samples (all candidates have labels).
- **Volume** → at least 100K records; preferred 1M+ (UNSW-NB15 = 2.54M).
- **Format** → CSV (machine-learning ready, chunkable) preferred over raw PCAP.

---

## 2. SELECTED ATTACKED DATASET — UNSW-NB15

**WHY UNSW-NB15 is the best attacked dataset for this project:**

1. **Many attack categories** — 9 attack families (Generic, Exploits, Fuzzers,
   DoS, Reconnaissance, Analysis, Backdoors, Shellcode, Worms) plus a clearly
   labelled **Normal** class. Perfect for multi-class IDS/risk classification.
2. **Benign + malicious labels in one file** — the `Label` column is binary
   (0 = normal, 1 = attack) and `attack_cat` gives the categorical class. This
   single dataset can therefore back **both** the ATTACKED and BENIGN sides of
   the project (documented split, not relabelling).
3. **Network-flow features** — 49 features (protocol, duration, packet/byte
   counts, rates, TTL statistics, TCP flags, etc.) that map directly onto the
   unified project schema (`protocol`, `duration`, `packet_count`, `byte_count`,
   `cpu_usage`-style telemetry, `security_label`, `attack_type`).
4. **Modern realistic mix** — generated in 2015 with IXIA PerfectStorm in the
   UNSW Cyber Range Lab as a hybrid of real modern normal activity and
   realistic synthetic attacks; far more representative than KDD99-era data.
5. **Sufficient volume** — **2,540,044 records** in four CSV files
   (`UNSW-NB15_1..4.csv`). Training + testing partitions are also shipped by the
   authors (`UNSW_NB15_training-set.csv` = 175,341, `UNSW_NB15_testing-set.csv`
   = 82,332).
6. **Machine-learning ready** — CSV/ARFF, no packet decoding required.

**Official source**

| Field                | Value |
|----------------------|-------|
| Official project page| https://research.unsw.edu.au/projects/unsw-nb15-dataset |
| Download            | Manual (files are hosted on the **UNSW SharePoint** link published on the official page): https://unsw-my.sharepoint.com/:f:/g/personal/z5025758_ad_unsw_edu_au/EnuQZZn3XuNBjgfcUu4DIVMBLCHyoLHqOswirpOQifr1ag |
| Alternative indexed copy | DOI **10.21227/8vf7-s525** (IEEE DataPort, training/testing zip, 11.37 MB) |
| Format             | CSV, ARFF, PCAP, BRO, Argus |
| Total records      | 2,540,044 |
| Features           | 49 (+ `attack_cat`, `Label`) |
| License            | Free use for academic research granted in perpetuity; commercial use must be agreed with the authors. Cite the 5 UNSW-NB15 papers listed on the official page. |

**Attack categories (documented class balance from the official distribution):**

| Class                           | Records (from UNSW-NB15 as shipped in the training/testing partition) |
|---------------------------------|-----------------------------------------------------------------------|
| Normal (benign)                 | 56,000 (train) + 37,000 (test) = 93,000 (partition)                  |
| Generic                         | 40,000 + 18,871                                                    |
| Exploits                        | 33,393 + 11,132                                                    |
| Fuzzers                         | 18,184 + 6,062                                                     |
| DoS                             | 12,264 + 4,089                                                     |
| Reconnaissance                  | 10,491 + 3,496                                                     |
| Analysis                        | 2,000 + 677                                                        |
| Backdoors                       | 1,746 + 583                                                        |
| Shellcode                       | 1,133 + 378                                                        |
| Worms                           | 130 + 44                                                           |

> These are the class counts published by the authors for the official
> training/testing partition. The **actual** per-file class counts are computed
> at runtime by `data_pipeline/statistics.py` and written to
> `datasets/statistics/` as soon as the raw CSVs are downloaded — see
> **Section 5 (Download status)** below.

**Why not the others?**

- **CIC-IDS2017 / CSE-CIC-IDS2018**: excellent, but 2018 is ~16.8M rows (very
  heavy to process on a laptop) and both require the UNB form to obtain the
  download link; UNSW-NB15 is smaller, richer in attack categories and ships a
  ready train/test split.
- **CIC-DDoS2019 / BoT-IoT**: enormous volume (73M+), but either attack-only
  (DDoS2019) or IoT-specific; UNSW-NB15's 2.54M records cover the edge/MEC
  network-flow scenario more directly.
- **TON_IoT**: good edge/IoT mix; retained as an alternative/backup.
- **NSL-KDD**: the only dataset already imported locally in this repo
  (`datasets/real/nsl_kdd_*`). Used here as the **first runnable real dataset**
  for the pipeline until UNSW-NB15 is manually downloaded.

---

## 3. SELECTED BENIGN DATASET — UNSW-NB15 "Normal" class

A dedicated, published *pure-normal* public traffic corpus in the same schema
as the attacked data is not practical for this project (pure-benign corpora are
either unlabelled PCAP or lack the flow features the AI scheduler needs). The
UNSW-NB15 dataset itself contains **2,218,761 clearly labelled Normal records**
(87% of the corpus, per the dataset's own literature) — a legitimate benign
corpus.

This is **not** a relabel/rename: it is an explicit, documented filter.

| Field             | Value |
|-------------------|-------|
| Original dataset  | UNSW-NB15 |
| Filtering method | Select rows where `Label == 0` and `attack_cat == "Normal"` (raw CSVs) |
| Original label    | `9` in `attack_cat` (i.e. "Normal") / `0` in `Label` |
| Filtered label    | `benign` (unified schema) |
| Expected records  | 2,218,761 (per UNSW-NB15 literature; actual count computed at runtime) |
| Features          | Same 49 UNSW-NB15 features |
| Official source   | https://research.unsw.edu.au/projects/unsw-nb15-dataset |

**Fallback/local BENIGN dataset — NSL-KDD "normal" class:**

| Field             | Value |
|-------------------|-------|
| Original dataset  | NSL-KDD (offline, already in `datasets/real/`) |
| Filtering method | `label == "normal"` |
| Original label    | `normal` |
| Filtered label    | `benign` |
| Records (local)   | computed at runtime by `scripts/validate_datasets.py` |

---

## 4. Dataset evaluation table (final selection)

| Dataset | Type | Official Source | Download Page | Direct Download | Format | Size | Records | Attack Types | Benign Samples | Features | Time Period | Network/IoT/Cloud | License / Academic Usage | Why Suitable | Preprocessing Required |
|---------|------|-----------------|---------------|-----------------|--------|------|---------|--------------|----------------|----------|-------------|-------------------|--------------------------|--------------|------------------------|
| **UNSW-NB15** | **ATTACKED** | UNSW Canberra | https://research.unsw.edu.au/projects/unsw-nb15-dataset | Manual (UNSW SharePoint link on official page); DOI 10.21227/8vf7-s525 | CSV/ARFF/PCAP | 100 GB raw; CSVs ≈ 1.3 GB total | 2,540,044 | 9 (Generic, Exploits, Fuzzers, DoS, Reconnaissance, Analysis, Backdoors, Shellcode, Worms) | Yes — Normal class (2,218,761) | 49 + attack_cat + Label | 2015, 16 h IXIA capture | Edge/MEC/cloud network flows | Free for academic research (perpetuity); commercial use requires author agreement; must cite 5 papers | Rich attack taxonomy, benign+attack labels, flow features, ML-ready CSVs, train/test split | Convert to unified schema: drop per-connection IPs, encode `proto/service/state`, normalize numeric, split Normal→benign / rest→attacked |
| **NSL-KDD** | **ATTACKED** (local) | UNB CIC (NSL-KDD) | https://www.unb.ca/cic/datasets/nsl.html | Provided with the NSL-KDD research package (see official page) | CSV | 20.9 MB (combined) | 148,517 | 22 subtypes / 4 groups (DoS, Probe, R2L, U2R) | Yes — normal class | 41 + label (+ difficulty) | KDD Cup '99 traffic, reduced 2009 | Legacy network flows | Public research benchmark; cite Tavallaee et al. 2009 | Already downloaded/validated locally; instant real-data pipeline demo | Encode categoricals, map subtypes → 4 families + normal, split |
| **TON_IoT** (alt.) | ATTACKED | UNSW Canberra | https://research.unsw.edu.au/projects/toniot-datasets | Manual (UNSW SharePoint link on official page) | CSV | ≈ 700 MB (network) | 461,043+ | 10+ | Yes — normal | 9+ flow features | 2019 | IoT / Industry 4.0 / Edge | Research licence; cite Moustafa et al. | Backup edge/IoT network option | Same as UNSW-NB15 |

---

## 5. Download status

| Dataset | Download method | Status |
|---------|-----------------|--------|
| NSL-KDD | Local files already present in `datasets/real/` (train+test+combined CSVs) | ✅ DOWNLOADED & VALIDATED |
| UNSW-NB15 | **MANUAL DOWNLOAD REQUIRED** — files are on UNSW SharePoint (click-through required; no anonymous direct link). See official page: https://research.unsw.edu.au/projects/unsw-nb15-dataset | ⏳ Awaits manual download |
| CIC-IDS2017 / IDS2018 / DDoS2019, BoT-IoT, TON_IoT | Manual via official pages | Reference only (documented) |

`scripts/download_datasets.py` prints **MANUAL DOWNLOAD REQUIRED** for every
dataset that cannot be fetched anonymously and shows the official source page,
then continues processing any files already on disk. Nothing is ever invented
as a "direct" link.

## 6. How the split remains honest

- `processed/attacked/` = only rows with a valid **attack** label.
- `processed/benign/`   = only rows whose original label is **normal/benign**.
- Rows that cannot be classified are written to an `_unknown` partition and
  are **never** relabelled benign or attacked.
- The `metadata/*.json` files record the exact filter (column, original label,
  number of rows) used for every dataset.