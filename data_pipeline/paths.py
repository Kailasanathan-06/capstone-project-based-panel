"""
Pipeline paths and dataset catalogue.

Only publicly documented, official URLs are listed here.  Any dataset that
cannot be fetched anonymously (UNSW SharePoint / research-portal forms) is
marked ``manual: True`` so the downloader prints MANUAL DOWNLOAD REQUIRED
with the official page instead of inventing a direct link.
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

DATASET_ROOT = os.path.join(PROJECT_DIR, "datasets")
RAW_ATTACKED = os.path.join(DATASET_ROOT, "raw", "attacked")
RAW_BENIGN = os.path.join(DATASET_ROOT, "raw", "benign")
PROCESSED_ATTACKED = os.path.join(DATASET_ROOT, "processed", "attacked")
PROCESSED_BENIGN = os.path.join(DATASET_ROOT, "processed", "benign")
PROCESSED_UNKNOWN = os.path.join(DATASET_ROOT, "processed", "unknown")
METADATA_DIR = os.path.join(DATASET_ROOT, "metadata")
STATISTICS_DIR = os.path.join(DATASET_ROOT, "statistics")
LOCAL_REAL_DIR = os.path.join(DATASET_ROOT, "real")

for _d in (
    RAW_ATTACKED,
    RAW_BENIGN,
    PROCESSED_ATTACKED,
    PROCESSED_BENIGN,
    PROCESSED_UNKNOWN,
    METADATA_DIR,
    STATISTICS_DIR,
):
    os.makedirs(_d, exist_ok=True)

# ---------------------------------------------------------------------------
# Unified internal schema (documented in docs/DATASET_SELECTION_REPORT.md).
# Fields that cannot be filled from a source dataset are left null or derived
# with a documented calculation (see data_pipeline/feature_engineering.py).
# ---------------------------------------------------------------------------
UNIFIED_SCHEMA = [
    "timestamp",
    "source",
    "destination",
    "protocol",
    "source_port",
    "destination_port",
    "packet_count",
    "byte_count",
    "duration",
    "flow_rate",
    "network_latency",
    "cpu_usage",
    "memory_usage",
    "task_size",
    "security_label",
    "attack_type",
    "risk_score",
]

# Labels used by the AI / scheduler.
BENIGN_LABELS = {"benign", "normal", "0", ""}
ATTACKED_LABEL = "attacked"

# ---------------------------------------------------------------------------
# Dataset catalogue.
#
# ``label_key``  - column holding the class (attack vs normal)
# ``category_key``- optional column holding the attack subtype
# ``benign_value``- value of label_key that means "normal"
# ``attacked_values`` - values of label_key that mean "attack"
# ``manual``      - True when no anonymous direct download exists
# ---------------------------------------------------------------------------
DATASET_CATALOG = [
    {
        "name": "UNSW-NB15",
        "type": "attacked",
        "official_url": "https://research.unsw.edu.au/projects/unsw-nb15-dataset",
        "download_url": "https://unsw-my.sharepoint.com/:f:/g/personal/z5025758_ad_unsw_edu_au/EnuQZZn3XuNBjgfcUu4DIVMBLCHyoLHqOswirpOQifr1ag",
        "doi": "10.21227/8vf7-s525",
        "format": "CSV",
        "records_expected": 2540044,
        "features": 49,
        "attack_types": [
            "Generic",
            "Exploits",
            "Fuzzers",
            "DoS",
            "Reconnaissance",
            "Analysis",
            "Backdoors",
            "Shellcode",
            "Worms",
        ],
        "benign_available": True,
        "label_key": "Label",
        "category_key": "attack_cat",
        "benign_value": 0,
        "manual": True,
        "license": "Free for academic research (perpetuity); commercial use requires author agreement; cite the 5 UNSW-NB15 papers.",
    },
    {
        "name": "CIC-IDS2017",
        "type": "attacked",
        "official_url": "https://www.unb.ca/cic/datasets/ids-2017.html",
        "download_url": "https://www.unb.ca/cic/datasets/ids-2017.html",
        "doi": None,
        "format": "CSV (CICFlowMeter features)",
        "records_expected": 2886020,
        "features": 80,
        "attack_types": [
            "Benign",
            "Brute Force",
            "DoS",
            "Web Attack",
            "Infiltration",
            "Botnet",
            "PortScan",
            "DDoS",
        ],
        "benign_available": True,
        "label_key": "Label",
        "category_key": "Label",
        "benign_value": "BENIGN",
        "manual": True,
        "license": "Research licence - see UNB CIC website.",
    },
    {
        "name": "CSE-CIC-IDS2018",
        "type": "attacked",
        "official_url": "https://www.unb.ca/cic/datasets/ids-2018.html",
        "download_url": "https://www.unb.ca/cic/datasets/ids-2018.html",
        "doi": None,
        "format": "CSV",
        "records_expected": 16800000,
        "features": 80,
        "attack_types": [
            "Benign",
            "DoS",
            "DDoS",
            "Botnet",
            "Brute Force",
            "SQL Injection",
            "XSS",
            "Infiltration",
        ],
        "benign_available": True,
        "label_key": "Label",
        "category_key": "Label",
        "benign_value": "Benign",
        "manual": True,
        "license": "Research licence - see UNB CIC website.",
    },
    {
        "name": "CIC-DDoS2019",
        "type": "attacked",
        "official_url": "https://www.unb.ca/cic/datasets/ddos-2019.html",
        "download_url": "https://www.unb.ca/cic/datasets/ddos-2019.html",
        "doi": None,
        "format": "CSV / PCAP",
        "records_expected": 50000000,
        "features": 80,
        "attack_types": [
            "DrDoS_UDP",
            "DrDoS_DNS",
            "DrDoS_MSSQL",
            "DrDoS_LDAP",
            "SYN",
            "UDP-Lag",
            "TFTP",
            "NetBIOS",
        ],
        "benign_available": False,
        "label_key": "Label",
        "category_key": "Label",
        "benign_value": "BENIGN",
        "manual": True,
        "license": "Research licence - see UNB CIC website.",
    },
    {
        "name": "BoT-IoT",
        "type": "attacked",
        "official_url": "https://research.unsw.edu.au/projects/bot-iot-dataset",
        "download_url": "https://research.unsw.edu.au/projects/bot-iot-dataset",
        "doi": None,
        "format": "CSV / PCAP",
        "records_expected": 73370044,
        "features": 43,
        "attack_types": ["DoS", "DDoS", "Reconnaissance", "Theft"],
        "benign_available": True,
        "label_key": "Label",
        "category_key": "category",
        "benign_value": "Normal",
        "manual": True,
        "license": "Free for academic research - see UNSW page.",
    },
    {
        "name": "TON_IoT",
        "type": "attacked",
        "official_url": "https://research.unsw.edu.au/projects/toniot-datasets",
        "download_url": "https://unsw-my.sharepoint.com/:f:/g/personal/z5025758_ad_unsw_edu_au/EvBTaetotpdGnW7rJQ8fCvYBh8063CNeY9W33MpRsarJaQ",
        "doi": None,
        "format": "CSV",
        "records_expected": 461043,
        "features": 9,
        "attack_types": [
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
            "sql_injection",
        ],
        "benign_available": True,
        "label_key": "Label",
        "category_key": "Label",
        "benign_value": "normal",
        "manual": True,
        "license": "Free for academic research - see UNSW page.",
    },
    {
        "name": "NSL-KDD",
        "type": "attacked",
        "official_url": "https://www.unb.ca/cic/datasets/nsl.html",
        "download_url": "https://www.unb.ca/cic/datasets/nsl.html",
        "doi": None,
        "format": "CSV (41 features + label)",
        "records_expected": 148517,
        "features": 41,
        "attack_types": [
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
            "normal",
        ],
        "benign_available": True,
        "label_key": "label",
        "category_key": "label",
        "benign_value": "normal",
        "manual": False,
        "local_imports": True,
        "license": "Public research benchmark - cite Tavallaee et al. 2009.",
    },
]

NSL_KDD_LOCAL_FILES = [
    os.path.join(LOCAL_REAL_DIR, "nsl_kdd_combined.csv"),
    os.path.join(LOCAL_REAL_DIR, "nsl_kdd_train.csv"),
    os.path.join(LOCAL_REAL_DIR, "nsl_kdd_test.csv"),
]


def get_catalog(name=None):
    """Return the catalogue entry (or all entries)."""
    if name is None:
        return DATASET_CATALOG
    for entry in DATASET_CATALOG:
        if entry["name"].lower() == name.lower():
            return entry
    raise KeyError(f"Unknown dataset: {name}")