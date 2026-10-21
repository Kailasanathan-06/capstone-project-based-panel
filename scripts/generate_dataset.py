"""
Dataset Generator (fast, vectorized)
====================================
Generates deterministic synthetic datasets for the SecureDT research prototype.
All generators are vectorized with numpy/pandas so even lakhs-scale (100k+) row
sets are produced in seconds:

    tasks_XXXXX.csv        - task records (default 10000)
    attack_events.csv      - 5000 attack-event records
    resource_states.csv    - 3000 resource-state records
    experiment_runs.csv    - 2000 experiment records
    ai_training.csv        - 10000 AI feature/label rows
    storage_security.csv   - 5000 storage-security rows
    network_flows.csv      - 50000 IDS-style network flow rows
    edge_telemetry.csv     - 50000 IoT device telemetry rows

These are SYNTHETIC data generated for a research prototype. They are not
real-world measurements of any live edge/cloud infrastructure.

Usage:
    python scripts/generate_dataset.py --tasks 10000
    python scripts/generate_dataset.py --all
    python scripts/generate_dataset.py --lakhs 200000
    python scripts/generate_dataset.py --force --lakhs 200000 --all
"""

import argparse
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402

ATTACK_TYPES = [
    "DDoS",
    "Eavesdropping",
    "Tampering",
    "Data_Poisoning",
    "Credential_Abuse",
    "Brute_Force",
    "Ransomware",
    "APT",
    "MITM",
    "Supply_Chain",
]
RESOURCES = ["LOCAL", "MEC-1", "MEC-2", "MEC-3", "CLOUD"]
RESOURCE_TYPES = {
    "LOCAL": "edge",
    "MEC-1": "mec",
    "MEC-2": "mec",
    "MEC-3": "mec",
    "CLOUD": "cloud",
}
MITIGATIONS = ["none", "quarantine", "reroute", "rate_limited"]
ALGORITHMS = ["random", "greedy", "privacy_aware", "proposed_ga"]


def _timer(start, label):
    print(f"  done in {time.time() - start:.2f}s", flush=True)


def generate_tasks(n, path):
    rng = np.random.default_rng(config.DATASET_SEED)
    types = config.TASK_TYPES
    nt = len(types)
    df = pd.DataFrame(
        {
            "task_id": [f"T{10000+i:06d}" for i in range(n)],
            "timestamp": pd.date_range("2026-01-01", periods=n, freq="3ms"),
            "task_type": [types[i] for i in rng.integers(0, nt, n)],
            "data_size_mb": np.round(rng.uniform(0.2, 22.0, n), 2),
            "cpu_cycles_giga": np.round(rng.uniform(0.1, 5.0, n), 2),
            "memory_mb": np.round(rng.uniform(32, 1024, n)),
            "deadline_ms": np.round(rng.uniform(90, 900, n)),
            "privacy_sensitivity": np.round(rng.uniform(0.05, 1.0, n), 3),
            "security_sensitivity": np.round(rng.uniform(0.05, 1.0, n), 3),
            "arrival_rate": np.round(rng.uniform(1, 40, n), 2),
            "source_node": np.random.choice(["EDGE"], n),
            "preferred_resource": np.random.choice(config.PREFERRED_RESOURCES, n),
            "expected_latency_ms": np.round(rng.uniform(40, 300, n), 1),
            "expected_energy_j": np.round(rng.uniform(0.5, 6.0, n), 2),
            "attack_exposure": np.round(rng.uniform(0.0, 0.9, n), 3),
        }
    )
    label = np.select(
        [
            (df["privacy_sensitivity"] > 0.7) & (df["security_sensitivity"] > 0.6),
            (df["privacy_sensitivity"] > 0.5) | (df["security_sensitivity"] > 0.5),
        ],
        ["high_risk", "sensitive"],
        default="normal",
    )
    df["label"] = label
    df.to_csv(path, index=False)
    return len(df)


def generate_attack_events(n, path):
    """Vectorized attack-event telemetry (identical schema to the original
    loop-based generator)."""
    rng = np.random.default_rng(config.DATASET_SEED + 1)
    idx = np.arange(n)
    severity = rng.uniform(0.2, 1.0, n)
    pre_risk = rng.uniform(0.05, 0.30, n)
    post_risk = np.minimum(1.0, pre_risk + 0.4 * severity + rng.uniform(0, 0.2, n))
    detected = rng.random(n) < 0.92
    ts = pd.Timestamp("2026-01-01") + pd.to_timedelta((idx * 2.3).astype(int), unit="s")
    df = pd.DataFrame(
        {
            "event_id": idx + 1,
            "timestamp": ts,
            "attack_type": np.array([ATTACK_TYPES[i % len(ATTACK_TYPES)] for i in idx]),
            "target_resource": np.array(
                [RESOURCES[i % (len(RESOURCES) - 1)] for i in idx]
            ),
            "severity": np.round(severity, 3),
            "pre_risk": np.round(pre_risk, 3),
            "post_risk": np.round(post_risk, 3),
            "affected_tasks": rng.integers(1, 200, n),
            "detection_score": np.round(rng.uniform(0.5, 0.99, n), 3),
            "mitigation_action": np.array(
                [MITIGATIONS[i % len(MITIGATIONS)] for i in idx]
            ),
            "detected": detected,
        }
    )
    df.to_csv(path, index=False)
    return len(df)


def generate_resource_states(n, path):
    """Vectorized resource-state snapshots (schema-compatible)."""
    rng = np.random.default_rng(config.DATASET_SEED + 2)
    idx = np.arange(n)
    rid = np.array([RESOURCES[i % len(RESOURCES)] for i in idx])
    rtype = np.array([RESOURCE_TYPES[r] for r in rid])
    ts = pd.Timestamp("2026-01-01") + pd.to_timedelta((idx * 21).astype(int), unit="s")
    df = pd.DataFrame(
        {
            "state_id": idx + 1,
            "timestamp": ts,
            "resource_id": rid,
            "resource_type": rtype,
            "cpu_utilization": np.round(rng.uniform(0.1, 0.95, n), 3),
            "memory_utilization": np.round(rng.uniform(0.1, 0.9, n), 3),
            "network_latency_ms": np.round(rng.uniform(30, 300, n), 1),
            "energy_rate": np.round(rng.uniform(1.5, 5.3, n), 2),
            "trust_score": np.round(rng.uniform(0.5, 1.0, n), 3),
            "security_risk": np.round(rng.uniform(0.02, 0.6, n), 3),
            "availability": rng.random(n) < 0.96,
            "active_tasks": rng.integers(0, 40, n),
        }
    )
    df.to_csv(path, index=False)
    return len(df)


def generate_experiments(n, path):
    """Vectorized experiment-history rows (schema-compatible)."""
    rng = np.random.default_rng(config.DATASET_SEED + 3)
    idx = np.arange(n)
    task_counts = [100, 500, 1000, 5000, 10000, 20000]
    attacks = ["none", "DDoS", "Eavesdropping", "Tampering"]
    algo = np.array([ALGORITHMS[i % len(ALGORITHMS)] for i in idx])
    max_lat = np.array(
        [
            {"random": 260, "greedy": 150, "privacy_aware": 180, "proposed_ga": 120}[a]
            for a in algo
        ]
    )
    latency = rng.uniform(80, max_lat)
    is_ga = algo == "proposed_ga"
    success = np.where(is_ga, rng.uniform(0.55, 0.99, n), rng.uniform(0.5, 0.9, n))
    security = np.where(is_ga, rng.uniform(0.55, 0.99, n), rng.uniform(0.55, 0.93, n))
    df = pd.DataFrame(
        {
            "run_id": idx + 1,
            "algorithm": algo,
            "task_count": np.array([task_counts[i % len(task_counts)] for i in idx]),
            "attack_condition": np.array([attacks[i % len(attacks)] for i in idx]),
            "avg_latency_ms": np.round(latency, 2),
            "energy_j": np.round(rng.uniform(1.5, 5.0, n), 2),
            "privacy_score": np.round(rng.uniform(0.6, 0.97, n), 3),
            "security_score": np.round(security, 3),
            "success_rate": np.round(success, 3),
            "scalability_score": np.round(rng.uniform(0.5, 1.0, n), 3),
        }
    )
    df.to_csv(path, index=False)
    return len(df)


def generate_ai_training(n, path):
    """Vectorized AI feature/target rows (schema-compatible)."""
    rng = np.random.default_rng(config.DATASET_SEED + 4)
    n_ = n
    cpu = rng.uniform(0.05, 0.98, n_)
    memory = rng.uniform(0.05, 0.95, n_)
    latency = rng.uniform(30, 350, n_)
    trust = rng.uniform(0.2, 1.0, n_)
    security_risk = rng.uniform(0.02, 0.98, n_)
    attack_severity = rng.uniform(0.0, 1.0, n_)
    privacy = rng.uniform(0.0, 1.0, n_)
    workload = rng.uniform(0.05, 1.0, n_)
    storage_integrity = rng.uniform(0.3, 1.0, n_)
    attack_exposure = rng.uniform(0.0, 1.0, n_)
    score = (
        0.25 * security_risk
        + 0.2 * attack_severity
        + 0.15 * (1 - trust)
        + 0.15 * privacy
        + 0.15 * (1 - storage_integrity)
        + 0.1 * workload
    )
    label = np.where(
        score >= 0.55, "high_risk", np.where(score >= 0.3, "warning", "safe")
    )
    df = pd.DataFrame(
        {
            "cpu": np.round(cpu, 3),
            "memory": np.round(memory, 3),
            "latency": np.round(latency, 1),
            "trust": np.round(trust, 3),
            "security_risk": np.round(security_risk, 3),
            "attack_severity": np.round(attack_severity, 3),
            "privacy": np.round(privacy, 3),
            "workload": np.round(workload, 3),
            "storage_integrity": np.round(storage_integrity, 3),
            "attack_exposure": np.round(attack_exposure, 3),
            "label": label,
        }
    )
    df.to_csv(path, index=False)
    return len(df)


def generate_storage_security(n, path):
    """Vectorized storage-security rows (schema-compatible)."""
    rng = np.random.default_rng(config.DATASET_SEED + 5)
    idx = np.arange(n)
    storage_types = ["HDD", "SSD", "NVMe", "VirtualNAS"]
    integrity = rng.uniform(0.4, 1.0, n)
    risk = rng.uniform(0.02, 0.95, n)
    access = rng.uniform(0.0, 1.0, n)
    suspicious = np.minimum(access, rng.uniform(0.0, 0.8, n))
    s = 0.5 * (1 - integrity) + 0.3 * risk + 0.2 * suspicious
    attack_label = np.select(
        [s >= 0.55, s >= 0.3], ["attacked", "suspicious"], default="normal"
    )
    ts = pd.Timestamp("2026-01-01") + pd.to_timedelta((idx * 3.1).astype(int), unit="s")
    df = pd.DataFrame(
        {
            "storage_id": np.array([f"S{i % 9 + 1:03d}" for i in idx]),
            "timestamp": ts,
            "storage_type": np.array(
                [storage_types[i % len(storage_types)] for i in idx]
            ),
            "capacity": np.round(rng.uniform(100, 2000, n), 1),
            "used_space": np.round(rng.uniform(20, 1800, n), 1),
            "data_blocks": rng.integers(1, 200, n),
            "integrity_score": np.round(integrity, 3),
            "access_attempts": rng.integers(1, 500, n),
            "suspicious_access": np.round(suspicious, 3),
            "encryption_status": rng.random(n) < 0.7,
            "privacy_level": np.round(rng.uniform(0.1, 1.0, n), 3),
            "risk_score": np.round(risk, 3),
            "attack_label": attack_label,
        }
    )
    df.to_csv(path, index=False)
    return len(df)


def generate_network_flows(n, path):
    """New IDS-style network flow dataset (synthetic, realistic fields)."""
    rng = np.random.default_rng(config.DATASET_SEED + 6)
    idx = np.arange(n)
    protocols = np.array(["TCP", "UDP", "ICMP", "TCP", "TCP", "UDP"])
    prots = protocols[rng.integers(0, len(protocols), n)]
    attacks = np.array(
        [
            "Benign",
            "Benign",
            "Benign",
            "Benign",
            "DDoS",
            "PortScan",
            "BruteForce",
            "WebAttack",
            "Botnet",
        ]
    )
    atk = np.array(
        [attacks[i % len(attacks)] for i in rng.integers(0, len(attacks), n)]
    )
    dur = rng.uniform(0.01, 120.0, n)
    fwd = rng.integers(1, 5000, n)
    bwd = rng.integers(0, 3000, n)
    fwd_bytes = rng.uniform(20, 1.5e6, n)
    bwd_bytes = rng.uniform(0, 2e6, n)
    src = rng.integers(0, 2**32, n)
    dst = rng.integers(0, 2**32, n)
    tkns = rng.random(n)
    label = np.where(
        atk == "Benign", "normal", np.where(tkns < 0.5, "suspicious", "malicious")
    )
    df = pd.DataFrame(
        {
            "flow_id": [f"F{1000000 + i}" for i in idx],
            "timestamp": pd.Timestamp("2026-01-01")
            + pd.to_timedelta(rng.uniform(0, 86400, n), unit="s"),
            "src_ip": ["10.0." + str(a % 254) + "." + str(1 + a % 253) for a in src],
            "dst_ip": ["192.168." + str(b % 254) + "." + str(1 + b % 253) for b in dst],
            "src_port": rng.integers(1024, 65535, n),
            "dst_port": rng.integers(1, 65535, n),
            "protocol": prots,
            "duration_s": np.round(dur, 4),
            "fwd_packets": fwd,
            "bwd_packets": bwd,
            "fwd_bytes": np.round(fwd_bytes, 1),
            "bwd_bytes": np.round(bwd_bytes, 1),
            "flow_packets_per_s": np.round((fwd + bwd) / (dur + 1e-6), 3),
            "flow_bytes_per_s": np.round((fwd_bytes + bwd_bytes) / (dur + 1e-6), 3),
            "attack_label": atk,
            "label": label,
        }
    )
    df.to_csv(path, index=False)
    return len(df)


def generate_edge_telemetry(n, path):
    """New IoT/edge device telemetry dataset (synthetic sensor stream)."""
    rng = np.random.default_rng(config.DATASET_SEED + 7)
    idx = np.arange(n)
    devices = np.array([f"EDGE-{i % 24:02d}" for i in idx])
    status = np.array(
        [
            "NORMAL",
            "NORMAL",
            "NORMAL",
            "WARNING",
            "CRITICAL",
            "NORMAL",
            "NORMAL",
            "OFFLINE",
        ]
    )
    stats = status[rng.integers(0, len(status), n)]
    temp = rng.normal(42.0, 4.0, n)
    cpu = rng.uniform(0.05, 0.98, n)
    mem = rng.uniform(0.1, 0.95, n)
    net = rng.uniform(5, 250, n)
    batt = rng.uniform(0.1, 1.0, n)
    signal = rng.integers(-90, -30, n)
    anomalies = rng.random(n) < 0.06
    ts = pd.Timestamp("2026-01-01") + pd.to_timedelta(idx * 5, unit="s")
    df = pd.DataFrame(
        {
            "record_id": idx + 1,
            "timestamp": ts,
            "device_id": devices,
            "device_type": "edge_gateway",
            "cpu_utilization": np.round(cpu, 3),
            "memory_utilization": np.round(mem, 3),
            "temperature_c": np.round(temp, 2),
            "network_latency_ms": np.round(net, 1),
            "battery_level": np.round(batt, 3),
            "signal_dbm": signal,
            "buffer_overflow": rng.integers(0, 3, n),
            "concurrent_processes": rng.integers(5, 200, n),
            "status": stats,
            "anomaly_flag": anomalies,
        }
    )
    df.to_csv(path, index=False)
    return len(df)


DEFAULT_SETS = [
    ("attack_events", generate_attack_events, 5000, config.ATTACK_DATASET),
    ("resource_states", generate_resource_states, 3000, config.RESOURCE_DATASET),
    ("experiment_runs", generate_experiments, 2000, config.EXPERIMENT_DATASET),
    ("ai_training", generate_ai_training, 10000, config.AI_TRAINING_DATASET),
    (
        "storage_security",
        generate_storage_security,
        5000,
        config.STORAGE_SECURITY_DATASET,
    ),
]

LARGE_SETS = [
    (
        "network_flows",
        generate_network_flows,
        50000,
        os.path.join(config.DATASET_DIR, "network_flows_50000.csv"),
    ),
    (
        "edge_telemetry",
        generate_edge_telemetry,
        50000,
        os.path.join(config.DATASET_DIR, "edge_telemetry_50000.csv"),
    ),
]


def _lakhs_path(name, n):
    return os.path.join(
        config.DATASET_DIR, f"lakhs_{name}_{n:,}".replace(",", "_") + ".csv"
    )


def generate_lakhs(n):
    """Generate a full suite of lakhs-scale (>=100k) datasets of every type."""
    os.makedirs(config.DATASET_DIR, exist_ok=True)
    makers = [
        ("tasks", generate_tasks),
        ("attack_events", generate_attack_events),
        ("resource_states", generate_resource_states),
        ("experiment_runs", generate_experiments),
        ("ai_training", generate_ai_training),
        ("storage_security", generate_storage_security),
        ("network_flows", generate_network_flows),
        ("edge_telemetry", generate_edge_telemetry),
    ]
    results = {}
    for name, fn in makers:
        path = _lakhs_path(name, n)
        start = time.time()
        count = fn(n, path)
        results[name] = {
            "path": path,
            "count": count,
            "took_s": round(time.time() - start, 2),
        }
        print(
            f"  {name:18s} {count:>10,} rows -> {os.path.basename(path)} "
            f"({results[name]['took_s']}s)",
            flush=True,
        )
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Generate SecureDT synthetic datasets (vectorized)."
    )
    parser.add_argument(
        "--tasks",
        type=int,
        default=10000,
        help="Number of task records (default: 10000)",
    )
    parser.add_argument(
        "--force", action="store_true", help="Overwrite existing datasets"
    )
    parser.add_argument("--all", action="store_true", help="Generate all dataset types")
    parser.add_argument(
        "--lakhs",
        type=int,
        default=0,
        help="Generate a full lakhs-scale suite (e.g. 200000)",
    )
    args = parser.parse_args()

    os.makedirs(config.DATASET_DIR, exist_ok=True)

    if args.lakhs > 0:
        print(f"Generating lakhs-scale suite ({args.lakhs:,} rows) ...")
        results = generate_lakhs(args.lakhs)
        print("\nLakhs-scale datasets ready:")
        for name, r in results.items():
            print(f"  {r['path']}  ({r['count']:,} rows, {r['took_s']}s)")
        return

    task_path = os.path.join(config.DATASET_DIR, f"tasks_{args.tasks}.csv")
    if os.path.exists(task_path) and not args.force:
        print(f"[skip] {os.path.basename(task_path)} already exists")
    else:
        print(f"Generating dataset: {args.tasks} tasks ...")
        n = generate_tasks(args.tasks, task_path)
        print(f"  {n} tasks generated successfully.")

    default_path = config.TASK_DATASET
    if not os.path.exists(default_path):
        print("Generating default tasks_10000.csv ...")
        n = generate_tasks(10000, default_path)
        print(f"  {n} tasks generated successfully.")

    sets = DEFAULT_SETS + LARGE_SETS
    for name, fn, count, path in sets:
        if os.path.exists(path) and not args.force and not args.all:
            print(f"[skip] {name}.csv already exists")
            continue
        print(f"Generating {name} ({count:,} rows) ...")
        n = fn(count, path)
        print(f"  {n} {name} generated successfully.")

    print("\nAll datasets ready.")
    print(f"  {config.TASK_DATASET}")
    print(f"  {config.ATTACK_DATASET}")
    print(f"  {config.RESOURCE_DATASET}")
    print(f"  {config.EXPERIMENT_DATASET}")
    print(f"  {config.AI_TRAINING_DATASET}")
    print(f"  {config.STORAGE_SECURITY_DATASET}")


if __name__ == "__main__":
    main()
