"""
Dataset Registry & Manager
==========================
A metadata registry for every dataset the prototype knows about:

  * the six bundled SYNTHETIC datasets (generated locally, fixed seeds)
  * well-known PUBLIC research datasets that may be imported by the user

The registry never claims synthetic data is real and never auto-downloads
large public corpora. Downloads only happen on explicit user action through
the official public source (landing page / DOI). Import/validate/preview are
local operations on user-provided files.

Sources are the official/public ones:

  * CSE-CIC-IDS2018 / CIC-IDS2017  - UNB - https://www.unb.ca/cic/datasets/
  * UNSW-NB15                     - UNSW - https://research.unsw.edu.au/
  * TON_IoT                       - UNSW Sydney - https://research.unsw.edu.au/projects/toniot-datasets
  * BoT-IoT                       - UNSW - https://research.unsw.edu.au/projects/bot-iot-dataset

This module is safe offline: it only reads local paths and static metadata.
"""

import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402

# Labels allowed by the "REAL vs SIMULATED" requirement
SOURCE_PUBLIC = "PUBLIC DATASET"
SOURCE_SYNTHETIC = "SYNTHETIC DATA"
SOURCE_LIVE = "LIVE TELEMETRY"
SOURCE_SIMULATION = "SIMULATION DATA"

SYNTHETIC_DATASETS = [
    {
        "name": "tasks_10000.csv",
        "display": "Synthetic Tasks",
        "source": SOURCE_SYNTHETIC,
        "origin": "scripts/generate_dataset.py (seeded)",
        "license": "Generated locally - research use",
        "format": "CSV",
        "records": 10000,
        "features": [
            "task_id",
            "task_type",
            "data_size_mb",
            "cpu_cycles_giga",
            "memory_mb",
            "deadline_ms",
            "privacy_sensitivity",
            "security_sensitivity",
            "attack_exposure",
            "label",
        ],
        "attack_classes": [],
        "download_url": None,
        "path": config.TASK_DATASET,
        "purpose": "Workload records for scheduling experiments",
    },
    {
        "name": "attack_events_5000.csv",
        "display": "Synthetic Attack Events",
        "source": SOURCE_SYNTHETIC,
        "origin": "scripts/generate_dataset.py (seeded)",
        "license": "Generated locally - research use",
        "format": "CSV",
        "records": 5000,
        "features": [
            "event_id",
            "attack_type",
            "target_resource",
            "severity",
            "pre_risk",
            "post_risk",
            "detection_score",
            "detected",
            "mitigation_action",
        ],
        "attack_classes": [
            "DDoS",
            "Eavesdropping",
            "Tampering",
            "Data_Poisoning",
            "Credential_Abuse",
        ],
        "download_url": None,
        "path": config.ATTACK_DATASET,
        "purpose": "Attack-event telemetry for security analytics",
    },
    {
        "name": "resource_states_3000.csv",
        "display": "Synthetic Resource States",
        "source": SOURCE_SYNTHETIC,
        "origin": "scripts/generate_dataset.py (seeded)",
        "license": "Generated locally - research use",
        "format": "CSV",
        "records": 3000,
        "features": [
            "resource_id",
            "cpu_utilization",
            "memory_utilization",
            "network_latency_ms",
            "energy_rate",
            "trust_score",
            "security_risk",
            "availability",
            "active_tasks",
        ],
        "attack_classes": [],
        "download_url": None,
        "path": config.RESOURCE_DATASET,
        "purpose": "Node telemetry snapshots for the digital twin",
    },
    {
        "name": "experiment_results_2000.csv",
        "display": "Synthetic Experiment Results",
        "source": SOURCE_SYNTHETIC,
        "origin": "scripts/generate_dataset.py (seeded)",
        "license": "Generated locally - research use",
        "format": "CSV",
        "records": 2000,
        "features": [
            "run_id",
            "algorithm",
            "task_count",
            "attack_condition",
            "avg_latency_ms",
            "energy_j",
            "privacy_score",
            "security_score",
            "success_rate",
            "scalability_score",
        ],
        "attack_classes": [],
        "download_url": None,
        "path": config.EXPERIMENT_DATASET,
        "purpose": "Algorithm comparison history",
    },
    {
        "name": "ai_training_10000.csv",
        "display": "Synthetic AI Training Set",
        "source": SOURCE_SYNTHETIC,
        "origin": "scripts/generate_dataset.py (seeded)",
        "license": "Generated locally - research use",
        "format": "CSV",
        "records": 10000,
        "features": [
            "cpu",
            "memory",
            "latency",
            "trust",
            "security_risk",
            "attack_severity",
            "privacy",
            "workload",
            "storage_integrity",
            "attack_exposure",
            "label",
        ],
        "attack_classes": [],
        "download_url": None,
        "path": config.AI_TRAINING_DATASET,
        "purpose": "Feature rows + risk labels for the Random Forest",
    },
    {
        "name": "storage_security_5000.csv",
        "display": "Synthetic Storage Security",
        "source": SOURCE_SYNTHETIC,
        "origin": "scripts/generate_dataset.py (seeded)",
        "license": "Generated locally - research use",
        "format": "CSV",
        "records": 5000,
        "features": [
            "storage_id",
            "storage_type",
            "capacity",
            "used_space",
            "integrity_score",
            "access_attempts",
            "suspicious_access",
            "encryption_status",
            "privacy_level",
            "risk_score",
            "attack_label",
        ],
        "attack_classes": ["normal", "suspicious", "attacked"],
        "download_url": None,
        "path": config.STORAGE_SECURITY_DATASET,
        "purpose": "Virtual storage integrity/risk lab rows",
    },
    {
        "name": "network_flows_50000.csv",
        "display": "Synthetic Network Flows (IDS)",
        "source": SOURCE_SYNTHETIC,
        "origin": "scripts/generate_dataset.py (vectorized, seeded)",
        "license": "Generated locally - research use",
        "format": "CSV",
        "records": 50000,
        "features": [
            "flow_id",
            "src_ip",
            "dst_ip",
            "src_port",
            "dst_port",
            "protocol",
            "duration_s",
            "fwd_packets",
            "bwd_packets",
            "flow_packets_per_s",
            "flow_bytes_per_s",
            "attack_label",
            "label",
        ],
        "attack_classes": [
            "Benign",
            "DDoS",
            "PortScan",
            "BruteForce",
            "WebAttack",
            "Botnet",
        ],
        "download_url": None,
        "path": os.path.join(config.DATASET_DIR, "network_flows_50000.csv"),
        "purpose": "IDS-style network flow rows for anomaly analytics",
    },
    {
        "name": "edge_telemetry_50000.csv",
        "display": "Synthetic Edge Device Telemetry",
        "source": SOURCE_SYNTHETIC,
        "origin": "scripts/generate_dataset.py (vectorized, seeded)",
        "license": "Generated locally - research use",
        "format": "CSV",
        "records": 50000,
        "features": [
            "record_id",
            "device_id",
            "cpu_utilization",
            "memory_utilization",
            "temperature_c",
            "network_latency_ms",
            "battery_level",
            "signal_dbm",
            "status",
            "anomaly_flag",
        ],
        "attack_classes": ["NORMAL", "WARNING", "CRITICAL", "OFFLINE"],
        "download_url": None,
        "path": os.path.join(config.DATASET_DIR, "edge_telemetry_50000.csv"),
        "purpose": "IoT/edge sensor stream for telemetry monitoring",
    },
]

PUBLIC_DATASETS = [
    {
        "name": "CIC-IDS2017",
        "source": SOURCE_PUBLIC,
        "origin": "Official UNB CIC dataset - https://www.unb.ca/cic/datasets/ids-2017.html",
        "license": "See UNB CIC website for terms (research licence)",
        "format": "PCAP + CSV (CICFlowMeter features)",
        "records": 2886020,
        "features": [
            "Flow Duration",
            "Tot Fwd Pkts",
            "Tot Bwd Pkts",
            "TotLen Fwd Pkts",
            "Fwd Pkt Len Mean",
            "Flow Bytes/s",
            "Flow IAT Mean",
            "Label",
        ],
        "attack_classes": [
            "Benign",
            "Brute Force",
            "DoS",
            "Web Attack",
            "Infiltration",
            "Botnet",
            "PortScan",
            "DDoS",
        ],
        "download_url": "https://www.unb.ca/cic/datasets/ids-2017.html",
        "path": None,
        "purpose": "Real-world intrusion-detection benchmark (optional import)",
    },
    {
        "name": "CSE-CIC-IDS2018",
        "source": SOURCE_PUBLIC,
        "origin": "Official AIT/UNB dataset - https://www.unb.ca/cic/datasets/ids-2018.html",
        "license": "See UNB CIC website for terms (research licence)",
        "format": "CSV (per day, CICFlowMeter features)",
        "records": 16800000,
        "features": [
            "Dst Port",
            "Protocol",
            "Tot Fwd Pkts",
            "TotLen Fwd Pkts",
            "Fwd IAT Mean",
            "Flow Bytes/s",
            "Label",
        ],
        "attack_classes": [
            "Benign",
            "DoS",
            "DDoS",
            "Botnet",
            "Brute Force",
            "SQL Injection",
            "XSS",
            "Infiltration",
        ],
        "download_url": "https://www.unb.ca/cic/datasets/ids-2018.html",
        "path": None,
        "purpose": "Real-world intrusion-detection benchmark (optional import)",
    },
    {
        "name": "UNSW-NB15",
        "source": SOURCE_PUBLIC,
        "origin": "Official UNSW dataset - https://research.unsw.edu.au/projects/unsw-nb15-dataset",
        "license": "See UNSW website for terms (research licence)",
        "format": "CSV/ARFF",
        "records": 2576736,
        "features": [
            "dur",
            "proto",
            "spkts",
            "dpkts",
            "sbytes",
            "dbytes",
            "rate",
            "sload",
            "dload",
            "ct_state_ttl",
            "attack_cat",
            "Label",
        ],
        "attack_classes": [
            "Fuzzers",
            "Analysis",
            "Backdoors",
            "DoS",
            "Exploits",
            "Generic",
            "Reconnaissance",
            "Shellcode",
            "Worms",
        ],
        "download_url": "https://research.unsw.edu.au/projects/unsw-nb15-dataset",
        "path": None,
        "purpose": "Modern realistic network traffic mix (optional import)",
    },
    {
        "name": "TON_IoT",
        "source": SOURCE_PUBLIC,
        "origin": "Official UNSW dataset - https://research.unsw.edu.au/projects/toniot-datasets",
        "license": "See UNSW website for terms (research licence)",
        "format": "CSV",
        "records": 461043,
        "features": [
            "ts",
            "proto",
            "dir",
            "saddr",
            "sport",
            "daddr",
            "dport",
            "pkts",
            "bytes",
            "state",
            "srcip",
            "dstip",
            "Label",
        ],
        "attack_classes": [
            "normal",
            "scanning",
            "dos",
            "ddos",
            "injection",
            "xss",
            "password",
            "ransomware",
            "backdoor",
            "mitm",
            "uploading",
            "sql_injection",
        ],
        "download_url": "https://research.unsw.edu.au/projects/toniot-datasets",
        "path": None,
        "purpose": "IoT/Industry 4.0 network and telemetry benchmark (optional import)",
    },
    {
        "name": "NSL-KDD (real, local)",
        "source": SOURCE_PUBLIC,
        "origin": "Official NSL-KDD benchmark (cleaned KDD Cup '99) - "
        "https://www.unb.ca/cic/datasets/nsl.html",
        "license": "Public research benchmark - cite NSL-KDD paper",
        "format": "CSV (41 flow features + label)",
        "records": 148517,
        "features": [
            "duration",
            "protocol_type",
            "service",
            "flag",
            "src_bytes",
            "dst_bytes",
            "land",
            "wrong_fragment",
            "urgent",
            "hot",
            "num_failed_logins",
            "logged_in",
            "num_compromised",
            "root_shell",
            "su_attempted",
            "num_root",
            "num_file_creations",
            "num_shells",
            "num_access_files",
            "is_host_login",
            "is_guest_login",
            "count",
            "srv_count",
            "serror_rate",
            "srv_serror_rate",
            "rerror_rate",
            "srv_rerror_rate",
            "same_srv_rate",
            "diff_srv_rate",
            "srv_diff_host_rate",
            "dst_host_same_srv_rate",
            "dst_host_diff_srv_rate",
            "dst_host_same_src_port_rate",
            "dst_host_srv_diff_host_rate",
            "dst_host_serror_rate",
            "dst_host_srv_rerror_rate",
            "label",
        ],
        "attack_classes": [
            "normal",
            "neptune",
            "satan",
            "ipsweep",
            "portsweep",
            "smurf",
            "nmap",
            "back",
            "teardrop",
            "warezclient",
            "pod",
            "guess_passwd",
            "buffer_overflow",
            "rootkit",
        ],
        "download_url": "https://www.unb.ca/cic/datasets/nsl.html",
        "path": os.path.join(config.DATASET_DIR, "real", "nsl_kdd_combined.csv"),
        "purpose": "Real-world intrusion-detection data (imported locally)",
    },
]

LAKHS_SCALE_SETS = [
    {
        "prefix": "lakhs_tasks_",
        "display": "Lakhs Tasks",
        "features": [
            "task_id",
            "task_type",
            "data_size_mb",
            "cpu_cycles_giga",
            "memory_mb",
            "deadline_ms",
            "privacy_sensitivity",
            "security_sensitivity",
            "label",
        ],
        "purpose": "2,00,000+ task workload records",
    },
    {
        "prefix": "lakhs_attack_events_",
        "display": "Lakhs Attack Events",
        "features": [
            "event_id",
            "attack_type",
            "target_resource",
            "severity",
            "pre_risk",
            "post_risk",
            "detected",
        ],
        "purpose": "2,00,000+ attack-event telemetry rows",
    },
    {
        "prefix": "lakhs_resource_states_",
        "display": "Lakhs Resource States",
        "features": [
            "state_id",
            "resource_id",
            "cpu_utilization",
            "trust_score",
            "security_risk",
            "availability",
        ],
        "purpose": "2,00,000+ digital-twin telemetry snapshots",
    },
    {
        "prefix": "lakhs_experiment_runs_",
        "display": "Lakhs Experiments",
        "features": [
            "run_id",
            "algorithm",
            "task_count",
            "avg_latency_ms",
            "energy_j",
            "success_rate",
        ],
        "purpose": "2,00,000+ algorithm comparison runs",
    },
    {
        "prefix": "lakhs_ai_training_",
        "display": "Lakhs AI Training",
        "features": ["cpu", "memory", "latency", "trust", "security_risk", "label"],
        "purpose": "2,00,000+ AI feature/label rows",
    },
    {
        "prefix": "lakhs_storage_security_",
        "display": "Lakhs Storage Logs",
        "features": ["storage_id", "integrity_score", "risk_score", "attack_label"],
        "purpose": "2,00,000+ storage security rows",
    },
    {
        "prefix": "lakhs_network_flows_",
        "display": "Lakhs Network Flows",
        "features": [
            "flow_id",
            "protocol",
            "duration_s",
            "fwd_packets",
            "flow_bytes_per_s",
            "label",
        ],
        "purpose": "2,00,000+ IDS network flows",
    },
    {
        "prefix": "lakhs_edge_telemetry_",
        "display": "Lakhs Edge Telemetry",
        "features": [
            "record_id",
            "device_id",
            "cpu_utilization",
            "temperature_c",
            "status",
            "anomaly_flag",
        ],
        "purpose": "2,00,000+ IoT sensor readings",
    },
]

# Attack classes allowed by the "REAL vs SIMULATED" requirement

# Feature columns shared by the UnifiedEvent normalizer for public datasets.
PUBLIC_FEATURE_MAP = {
    "CIC-IDS2017": [
        "Flow Duration",
        "Tot Fwd Pkts",
        "Tot Bwd Pkts",
        "TotLen Fwd Pkts",
        "Flow Bytes/s",
        "Flow IAT Mean",
    ],
    "CSE-CIC-IDS2018": [
        "Tot Fwd Pkts",
        "TotLen Fwd Pkts",
        "Flow Bytes/s",
        "Fwd IAT Mean",
    ],
    "UNSW-NB15": ["dur", "spkts", "dpkts", "sbytes", "dbytes", "rate"],
    "TON_IoT": ["pkts", "bytes", "dport", "sport"],
    "BoT-IoT": ["pkts", "bytes", "dport", "sport"],
}


def _stat(path):
    """Return (exists, bytes, modified_iso) for a local path."""
    if not path or not os.path.exists(path):
        return False, 0, None
    try:
        mtime = datetime.fromtimestamp(os.path.getmtime(path), timezone.utc).isoformat()
    except Exception:  # noqa: BLE001
        mtime = None
    return True, os.path.getsize(path), mtime


def _fast_row_count(path):
    """Approximate row count without loading the file."""
    if not path or not os.path.exists(path):
        return 0
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            n = sum(1 for _ in fh) - 1
        return max(0, n)
    except Exception:  # noqa: BLE001
        return 0


def registry_payload():
    """Combine bundled synthetic + optional public datasets with local status."""
    rows = []
    for ds in SYNTHETIC_DATASETS:
        exists, size, updated = _stat(ds.get("path"))
        rows.append(
            _row(
                ds,
                exists,
                size,
                updated,
                _fast_row_count(ds.get("path")) if exists else 0,
            )
        )
    for ds in PUBLIC_DATASETS:
        exists, size, updated = _stat(ds.get("path"))
        rows.append(
            _row(
                ds,
                exists,
                size,
                updated,
                _fast_row_count(ds.get("path")) if exists else 0,
            )
        )
    # auto-detect lakhs-scale synthetic datasets on disk
    for spec in LAKHS_SCALE_SETS:
        for fname in sorted(os.listdir(config.DATASET_DIR)):
            if not fname.startswith(spec["prefix"]) or not fname.endswith(".csv"):
                continue
            path = os.path.join(config.DATASET_DIR, fname)
            size = os.path.getsize(path)
            updated = datetime.fromtimestamp(
                os.path.getmtime(path), timezone.utc
            ).isoformat()
            rows.append(
                {
                    "name": fname,
                    "display": spec["display"],
                    "source": SOURCE_SYNTHETIC,
                    "origin": "scripts/generate_dataset.py --lakhs (vectorized)",
                    "license": "Generated locally - research use",
                    "format": "CSV",
                    "records_expected": 0,
                    "records_local": _fast_row_count(path),
                    "features": spec["features"],
                    "attack_classes": [],
                    "download_url": None,
                    "local_path": path,
                    "exists": True,
                    "size_bytes": size,
                    "last_updated": updated,
                    "status": "LOCAL",
                    "purpose": spec["purpose"],
                }
            )
    return {
        "rows": rows,
        "total": len(rows),
        "synth_count": sum(1 for r in rows if r["source"] == SOURCE_SYNTHETIC),
        "public_count": sum(1 for r in rows if r["source"] == SOURCE_PUBLIC),
        "generated": datetime.now(timezone.utc).isoformat(),
    }


def _row(ds, exists, size, updated, rows):
    return {
        "name": ds["name"],
        "display": ds.get("display", ds["name"]),
        "source": ds["source"],
        "origin": ds.get("origin", ""),
        "license": ds.get("license", ""),
        "format": ds.get("format", ""),
        "records_expected": ds.get("records", 0),
        "records_local": rows,
        "features": ds.get("features", []),
        "attack_classes": ds.get("attack_classes", []),
        "download_url": ds.get("download_url"),
        "local_path": ds.get("path"),
        "exists": exists,
        "size_bytes": size,
        "last_updated": updated,
        "status": (
            "LOCAL"
            if exists
            else ("REFERENCE" if ds.get("download_url") else "NOT_GENERATED")
        ),
        "purpose": ds.get("purpose", ""),
    }


def find(name):
    """Return the first registry row whose name matches (case-insensitive)."""
    (name or "").lower()
    for ds in SYNTHETIC_DATASETS + PUBLIC_DATASETS:
        if (
            ds["name"].lower() == name.lower()
            or ds.get("display", "").lower() == name.lower()
        ):
            return ds
    return None


def describe_local_file(path, name=None):
    """Inspect a local CSV and return schema/quality-oriented metadata."""
    import pandas as pd

    if not os.path.exists(path):
        raise FileNotFoundError(path)
    df = pd.read_csv(path, nrows=200)
    dtypes = {c: str(t) for c, t in df.dtypes.items()}
    return {
        "name": name or os.path.basename(path),
        "columns": list(df.columns),
        "dtypes": dtypes,
        "sample_rows": min(10, int(df.shape[0])),
        "estimated_records": _fast_row_count(path),
        "size_bytes": os.path.getsize(path),
        "last_updated": datetime.fromtimestamp(
            os.path.getmtime(path), timezone.utc
        ).isoformat(),
    }


def save_index(path):
    """Persist the registry as JSON (for exports/reports)."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(registry_payload(), fh, indent=2, default=str)
    return path


if __name__ == "__main__":
    payload = registry_payload()
    print(
        f"Registry rows: {payload['total']} "
        f"(synthetic={payload['synth_count']}, "
        f"public={payload['public_count']})"
    )
    for r in payload["rows"]:
        print(f"  [{r['status']:9s}] {r['name']:32s} {r['source']}")
