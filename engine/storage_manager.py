"""
Storage Manager Engine (Phase 6)
================================
Provides the verified 3-destination storage architecture:
1. LOCAL_STORAGE: Hospital On-Premises Local Edge Storage Tier
2. MEC_STORAGE: Hospital MEC Node Micro-Datacenter Storage Tier
3. CLOUD_STORAGE: Central Hybrid/Public Cloud Tier (Local Emulator)

Enforces:
- Physical storage directories strictly outside public webroot
- Cryptographic SHA-256 verification on all replicated artifacts
- Strict privacy tier boundary preservation (LOCAL_ONLY blocked from MEC/Cloud, TRUSTED_EDGE blocked from Cloud)
- Full idempotency: skips redundant transfers if verified checksum already exists
- Comprehensive inventory export to CSV
"""

import os
import csv
import json
import shutil
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

from django.conf import settings
from django.utils import timezone as dj_timezone


# ---------------------------------------------------------------------------
# Storage Specification Definitions
# ---------------------------------------------------------------------------
STORAGE_DESTINATION_SPECS = {
    "LOCAL_STORAGE": {
        "destination_id": "LOCAL_STORAGE",
        "name": "Hospital Local Edge Storage Tier",
        "destination_type": "LOCAL",
        "relative_dir": "data_storage/local_storage",
        "is_emulator": False,
        "privacy_tier_allowed": "LOCAL_ONLY",
        "capacity_bytes": 50 * 1024 * 1024 * 1024,  # 50 GB
        "description": "On-premises high-privacy edge storage strictly bounded to local clinical devices.",
    },
    "MEC_STORAGE": {
        "destination_id": "MEC_STORAGE",
        "name": "Hospital MEC Node Micro-Datacenter Storage Tier",
        "destination_type": "MEC",
        "relative_dir": "data_storage/mec_storage",
        "is_emulator": False,
        "privacy_tier_allowed": "TRUSTED_EDGE",
        "capacity_bytes": 200 * 1024 * 1024 * 1024,  # 200 GB
        "description": "Authorized edge compute node cluster storage for trusted low-latency workloads.",
    },
    "CLOUD_STORAGE": {
        "destination_id": "CLOUD_STORAGE",
        "name": "Central Cloud Storage Repository Tier",
        "destination_type": "CLOUD",
        "relative_dir": "data_storage/cloud_storage",
        "is_emulator": True,
        "privacy_tier_allowed": "CLOUD_ALLOWED",
        "capacity_bytes": 1000 * 1024 * 1024 * 1024,  # 1 TB
        "description": "Scalable public cloud tier for de-identified general medical datasets and benchmarks.",
    },
}


def get_project_base_dir() -> Path:
    """Return the Django project root directory."""
    return Path(getattr(settings, "BASE_DIR", Path(".")))


def get_destination_absolute_path(destination_id: str) -> Path:
    """Resolve and ensure the absolute filesystem directory for a storage tier."""
    spec = STORAGE_DESTINATION_SPECS.get(destination_id.upper())
    if not spec:
        # Fallback to local storage subfolder
        p = get_project_base_dir() / "data_storage" / destination_id.lower()
    else:
        p = get_project_base_dir() / spec["relative_dir"]
    p.mkdir(parents=True, exist_ok=True)
    return p


def calculate_file_sha256(file_path: Path) -> str:
    """Calculate the cryptographic SHA-256 hex digest of a file on disk."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


# ---------------------------------------------------------------------------
# Storage Tier Initializer
# ---------------------------------------------------------------------------
def ensure_storage_destinations_initialized() -> Dict[str, Any]:
    """
    Initializes all 3 physical storage directories outside webroot and registers
    or updates their metadata in the database.
    """
    from datasets.models import StorageDestination

    destinations = {}
    for dest_id, spec in STORAGE_DESTINATION_SPECS.items():
        abs_path = get_destination_absolute_path(dest_id)

        # Verify write access by touching a verification keepfile
        keep_file = abs_path / ".storage_verified"
        if not keep_file.exists():
            with open(keep_file, "w", encoding="utf-8") as fh:
                fh.write(f"SecureDT Verified Storage Node: {dest_id}\nInitialized: {datetime.now(timezone.utc).isoformat()}\n")

        # Calculate current directory usage
        used_bytes = 0
        for entry in abs_path.rglob("*"):
            if entry.is_file():
                try:
                    used_bytes += entry.stat().st_size
                except OSError:
                    pass

        obj, _ = StorageDestination.objects.update_or_create(
            destination_id=dest_id,
            defaults={
                "name": spec["name"],
                "destination_type": spec["destination_type"],
                "base_path": str(abs_path),
                "is_active": True,
                "is_emulator": spec["is_emulator"],
                "capacity_bytes": spec["capacity_bytes"],
                "used_bytes": used_bytes,
                "privacy_tier_allowed": spec["privacy_tier_allowed"],
            },
        )
        destinations[dest_id] = obj

    return destinations


# ---------------------------------------------------------------------------
# Replication Engine
# ---------------------------------------------------------------------------
def replicate_file(
    source_path: str,
    dataset_id: str,
    target_destination_id: str,
    privacy_policy: str = "TRUSTED_EDGE",
    relative_key: Optional[str] = None,
    scenario_id: Optional[str] = None,
    source_ip: str = "127.0.0.1",
) -> Tuple[bool, str, Optional[Any]]:
    """
    Physically replicates a dataset or workload file to a destination tier.

    Enforces:
    1. Privacy tier constraints:
       - LOCAL_ONLY: strictly forbidden from replicating to MEC or CLOUD.
       - TRUSTED_EDGE: permitted to LOCAL and MEC; forbidden from CLOUD.
       - CLOUD_ALLOWED: permitted to all tiers.
       Policy violations trigger a critical SecurityAuditEvent and create/update
       a replica with status BLOCKED_BY_POLICY.
    2. Physical copy and SHA-256 cryptographic verification.
    3. Idempotent transfer: skips redundant copying if replica already verified.

    Returns:
        (success: bool, message: str, replica_obj: Optional[DatasetStorageReplica])
    """
    from datasets.models import StorageDestination, DatasetStorageReplica, WorkloadScenario
    from engine.hospital_workloads import record_security_event

    ensure_storage_destinations_initialized()
    target_dest_key = target_destination_id.upper()
    if not target_dest_key.endswith("_STORAGE"):
        target_dest_key = f"{target_dest_key}_STORAGE"

    dest = StorageDestination.objects.filter(destination_id=target_dest_key).first()
    if not dest:
        # Fallback query by destination_type
        dest = StorageDestination.objects.filter(destination_type=target_destination_id.upper()).first()

    if not dest:
        dest_dict = ensure_storage_destinations_initialized()
        dest = dest_dict.get(target_dest_key) or list(dest_dict.values())[0]

    # Evaluate Privacy Tier Boundary
    policy_upper = privacy_policy.upper()
    target_type = dest.destination_type.upper()
    violation = False
    violation_reason = ""

    if policy_upper == "LOCAL_ONLY" and target_type in ("MEC", "CLOUD"):
        violation = True
        violation_reason = (
            f"Prohibited: Dataset '{dataset_id}' with privacy policy LOCAL_ONLY "
            f"cannot be replicated to external tier '{dest.destination_id}'."
        )
    elif policy_upper == "TRUSTED_EDGE" and target_type == "CLOUD":
        violation = True
        violation_reason = (
            f"Prohibited: Dataset '{dataset_id}' with privacy policy TRUSTED_EDGE "
            f"cannot be replicated to central Cloud tier '{dest.destination_id}'."
        )

    replica_id = f"REP-{dataset_id}-{dest.destination_id}"
    scen_obj = WorkloadScenario.objects.filter(scenario_id=scenario_id).first() if scenario_id else None

    if violation:
        # Record Security Audit Event
        audit_event = record_security_event(
            event_type="PRIVACY_POLICY_VIOLATION",
            severity="CRITICAL",
            description=violation_reason,
            task_id=dataset_id,
            source_ip=source_ip,
            details={
                "dataset_id": dataset_id,
                "target_destination": dest.destination_id,
                "target_tier": dest.destination_type,
                "privacy_policy": privacy_policy,
                "scenario_id": scenario_id or "",
                "action": "physical_dataset_replication",
            },
            blocked=True,
        )

        replica, _ = DatasetStorageReplica.objects.update_or_create(
            replica_id=replica_id,
            defaults={
                "dataset_id": dataset_id,
                "scenario": scen_obj,
                "storage_destination": dest,
                "relative_key": relative_key or f"{dataset_id}/data.bin",
                "absolute_path": "",
                "file_size_bytes": 0,
                "sha256_checksum": "",
                "replication_status": "BLOCKED_BY_POLICY",
                "last_error": violation_reason,
                "is_available": False,
            },
        )
        return False, f"BLOCKED_BY_POLICY: {violation_reason}", replica

    # Verify source file presence
    src = Path(source_path)
    if not src.exists() or not src.is_file():
        return False, f"Source file does not exist on disk: {source_path}", None

    src_size = src.stat().st_size
    src_checksum = calculate_file_sha256(src)

    # Determine object key and destination path
    obj_key = relative_key or f"{dataset_id}/{src.name}"
    dest_path = Path(dest.base_path) / obj_key
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # Idempotent Check: if replica already exists with verified checksum, avoid redundant copy
    if dest_path.exists():
        existing_checksum = calculate_file_sha256(dest_path)
        if existing_checksum == src_checksum:
            replica, _ = DatasetStorageReplica.objects.update_or_create(
                replica_id=replica_id,
                defaults={
                    "dataset_id": dataset_id,
                    "scenario": scen_obj,
                    "storage_destination": dest,
                    "relative_key": obj_key,
                    "absolute_path": str(dest_path),
                    "file_size_bytes": src_size,
                    "sha256_checksum": src_checksum,
                    "replication_status": "VERIFIED",
                    "last_error": "",
                    "is_available": True,
                    "last_verified_at": dj_timezone.now(),
                },
            )
            return True, "Replica already verified and identical on target storage (idempotent).", replica

    # Mark as COPYING
    replica, _ = DatasetStorageReplica.objects.update_or_create(
        replica_id=replica_id,
        defaults={
            "dataset_id": dataset_id,
            "scenario": scen_obj,
            "storage_destination": dest,
            "relative_key": obj_key,
            "absolute_path": str(dest_path),
            "file_size_bytes": src_size,
            "sha256_checksum": src_checksum,
            "replication_status": "COPYING",
            "last_error": "",
            "is_available": False,
        },
    )

    # Atomic copy with temporary buffer
    temp_dest = dest_path.with_suffix(dest_path.suffix + ".tmp_transfer")
    try:
        shutil.copy2(src, temp_dest)
        dest_checksum = calculate_file_sha256(temp_dest)

        if dest_checksum != src_checksum:
            if temp_dest.exists():
                temp_dest.unlink()
            replica.replication_status = "FAILED"
            replica.last_error = f"Integrity error: checksum mismatch (expected {src_checksum}, got {dest_checksum})"
            replica.save()
            return False, replica.last_error, replica

        # Atomically replace final file
        if dest_path.exists():
            dest_path.unlink()
        temp_dest.replace(dest_path)

        # Mark as VERIFIED
        replica.replication_status = "VERIFIED"
        replica.sha256_checksum = dest_checksum
        replica.file_size_bytes = dest_path.stat().st_size
        replica.is_available = True
        replica.last_error = ""
        replica.last_verified_at = dj_timezone.now()
        replica.save()

        # Update destination usage
        dest.used_bytes = (dest.used_bytes or 0) + replica.file_size_bytes
        dest.save(update_fields=["used_bytes"])

        return True, "Physical dataset replica verified and stored successfully.", replica

    except Exception as exc:
        if temp_dest.exists():
            temp_dest.unlink()
        replica.replication_status = "FAILED"
        replica.last_error = f"Replication transfer error: {str(exc)}"
        replica.save()
        return False, replica.last_error, replica


# ---------------------------------------------------------------------------
# Replicas Verification Sweep
# ---------------------------------------------------------------------------
def verify_all_storage_replicas() -> Dict[str, Any]:
    """
    Performs an audit sweep of all registered replicas against files on disk.
    Verifies physical presence and cryptographic checksums.
    """
    from datasets.models import DatasetStorageReplica

    total = 0
    verified = 0
    failed = 0
    blocked = 0
    missing = 0

    for rep in DatasetStorageReplica.objects.all():
        total += 1
        if rep.replication_status == "BLOCKED_BY_POLICY":
            blocked += 1
            continue

        p = Path(rep.absolute_path)
        if not p.exists():
            rep.replication_status = "UNAVAILABLE"
            rep.is_available = False
            rep.last_error = "File missing from disk during audit sweep"
            rep.save()
            missing += 1
            continue

        chk = calculate_file_sha256(p)
        if chk == rep.sha256_checksum:
            rep.last_verified_at = dj_timezone.now()
            rep.is_available = True
            rep.save(update_fields=["last_verified_at", "is_available"])
            verified += 1
        else:
            rep.replication_status = "FAILED"
            rep.last_error = f"Integrity check failed: on-disk checksum {chk} != registered {rep.sha256_checksum}"
            rep.is_available = False
            rep.save()
            failed += 1

    return {
        "total_replicas": total,
        "verified": verified,
        "failed": failed,
        "blocked": blocked,
        "missing": missing,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Inventory Export Engine
# ---------------------------------------------------------------------------
def export_storage_inventory_csv(output_path: Optional[str] = None) -> str:
    """
    Exports a structured CSV report containing storage destinations and all replicas.
    """
    from datasets.models import StorageDestination, DatasetStorageReplica

    ensure_storage_destinations_initialized()
    base_dir = get_project_base_dir()
    out_file = Path(output_path) if output_path else (base_dir / "data_storage" / "storage_inventory_export.csv")
    out_file.parent.mkdir(parents=True, exist_ok=True)

    with open(out_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "Replica ID",
            "Dataset ID",
            "Scenario ID",
            "Destination ID",
            "Tier Type",
            "Replication Status",
            "File Size (Bytes)",
            "SHA-256 Checksum",
            "Absolute Path",
            "Is Available",
            "Last Verified At",
            "Last Error",
        ])

        for rep in DatasetStorageReplica.objects.select_related("storage_destination", "scenario").all():
            writer.writerow([
                rep.replica_id,
                rep.dataset_id,
                rep.scenario.scenario_id if rep.scenario else "",
                rep.storage_destination.destination_id if rep.storage_destination else "",
                rep.storage_destination.destination_type if rep.storage_destination else "",
                rep.replication_status,
                rep.file_size_bytes,
                rep.sha256_checksum,
                rep.absolute_path,
                rep.is_available,
                rep.last_verified_at.isoformat() if rep.last_verified_at else "",
                rep.last_error,
            ])

    return str(out_file)
