"""
Generator for Master Suite of 11 Digital Twin Edge-Cloud ZIP Test Scenarios
=============================================================================
Builds:
- 5 Successful Scenario ZIPs (Category A)
- 3 Failed Scenario ZIPs (Category B)
- 3 Loop / Timeout Scenario ZIPs (Category C)
- 1 Master Suite ZIP containing all 11 scenarios + root README
- 1 Inventory CSV mapping all test scenarios, expected results, and checksums
"""

import os
import io
import csv
import json
import zipfile
import hashlib
from datetime import datetime, timezone
from pathlib import Path


BASE_OUTPUT_DIR = Path("test_datasets_suite")
SAMPLE_UPLOAD_DIR = Path("sample_upload_datasets")


def calc_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def create_standard_resource_definitions(
    local_cap=512, local_avail=400,
    mec_cap=2048, mec_avail=1500,
    cloud_cap=8192, cloud_avail=6000
):
    """Generates standard synthetic resource descriptions for Local, MEC, and Cloud."""
    return [
        {
            "resource_id": "LOCAL-01",
            "resource_name": "Hospital Local Workstation Storage",
            "resource_type": "local",
            "capacity_mb": local_cap,
            "available_mb": local_avail,
            "status": "online",
            "trusted": True,
            "privacy_tier_allowed": "LOCAL_ONLY",
            "dataset_inventory": ["local_vitals.csv", "local_tasks.csv"],
            "supported_tasks": ["vitals_ingestion", "bedside_telemetry", "biometric_recording"]
        },
        {
            "resource_id": "MEC-01",
            "resource_name": "Hospital MEC Edge Node Cluster",
            "resource_type": "mec",
            "capacity_mb": mec_cap,
            "available_mb": mec_avail,
            "status": "online",
            "last_heartbeat": "2026-10-23T20:00:00Z",
            "trusted": True,
            "privacy_tier_allowed": "TRUSTED_EDGE",
            "dataset_inventory": ["mec_imaging.csv", "mec_tasks.csv"],
            "supported_tasks": ["dicom_clahe_enhancement", "edge_inference", "mri_slice_filtering"]
        },
        {
            "resource_id": "CLOUD-01",
            "resource_name": "Central Cloud Storage Repository",
            "resource_type": "cloud",
            "capacity_mb": cloud_cap,
            "available_mb": cloud_avail,
            "status": "online",
            "trusted": True,
            "privacy_tier_allowed": "CLOUD_ALLOWED",
            "dataset_inventory": ["cloud_archive.csv", "cloud_tasks.csv"],
            "supported_tasks": ["cross_institution_aggregation", "long_term_cold_storage", "billing_analytics"]
        }
    ]


def build_scenario_zip(
    output_path: Path,
    manifest: dict,
    local_files: dict,
    mec_files: dict,
    cloud_files: dict,
    task_metadata: dict,
    expected_results: dict,
    readme_text: str,
    local_resource_override: dict = None,
    mec_resource_override: dict = None,
    cloud_resource_override: dict = None,
) -> int:
    """Builds a standardized scenario ZIP archive following Section 4 structure."""
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. Manifest
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        # 2. README.txt
        zf.writestr("README.txt", readme_text)

        # 3. Local Tier
        local_res = local_resource_override or (
            manifest["resources"][0] if "resources" in manifest and len(manifest["resources"]) > 0 else {}
        )
        if local_res:
            zf.writestr("local/resource.json", json.dumps(local_res, indent=2))
        for rel_name, content in local_files.items():
            zf.writestr(f"local/dataset/{rel_name}", content)

        # 4. MEC Tier
        mec_res = mec_resource_override or (
            manifest["resources"][1] if "resources" in manifest and len(manifest["resources"]) > 1 else {}
        )
        if mec_res:
            zf.writestr("mec/resource.json", json.dumps(mec_res, indent=2))
        for rel_name, content in mec_files.items():
            zf.writestr(f"mec/dataset/{rel_name}", content)

        # 5. Cloud Tier
        cloud_res = cloud_resource_override or (
            manifest["resources"][2] if "resources" in manifest and len(manifest["resources"]) > 2 else {}
        )
        if cloud_res:
            zf.writestr("cloud/resource.json", json.dumps(cloud_res, indent=2))
        for rel_name, content in cloud_files.items():
            zf.writestr(f"cloud/dataset/{rel_name}", content)

        # 6. Tasks Metadata
        zf.writestr("tasks/task_metadata.json", json.dumps(task_metadata, indent=2))
        # 7. Expected Results
        zf.writestr("expected_results/expected_result.json", json.dumps(expected_results, indent=2))

    return os.path.getsize(output_path)


def generate_all_scenarios():
    BASE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    scenario_inventory = []

    # =========================================================================
    # SUCCESS 01: Basic All Storage
    # =========================================================================
    s1_path = BASE_OUTPUT_DIR / "success_01_basic_all_storage.zip"
    s1_resources = create_standard_resource_definitions()
    s1_manifest = {
        "scenario_id": "success_01",
        "scenario_name": "Basic All Storage",
        "scenario_category": "success",
        "description": "Baseline valid test dataset containing representative workloads for Local, MEC, and Cloud resources.",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "resources": s1_resources,
        "datasets": [
            {"dataset_id": "DS-LOCAL-01", "file_name": "local_tasks.csv", "format": "CSV", "size_mb": 1, "tier": "local", "privacy_policy": "LOCAL_ONLY"},
            {"dataset_id": "DS-MEC-01", "file_name": "mec_tasks.csv", "format": "CSV", "size_mb": 10, "tier": "mec", "privacy_policy": "TRUSTED_EDGE"},
            {"dataset_id": "DS-CLOUD-01", "file_name": "cloud_tasks.csv", "format": "CSV", "size_mb": 5, "tier": "cloud", "privacy_policy": "CLOUD_ALLOWED"}
        ],
        "tasks": [
            {
                "task_id": "TASK-001",
                "dataset_id": "DS-LOCAL-01",
                "file_name": "local_tasks.csv",
                "name": "Patient Vitals Ingestion",
                "size_mb": 1,
                "task_type": "clinical_phi_ingest",
                "privacy_policy": "LOCAL_ONLY",
                "deadline_seconds": 15,
                "required_memory_mb": 64,
                "required_storage_mb": 1,
                "dependency_ids": [],
                "source_resource": "LOCAL-01"
            },
            {
                "task_id": "TASK-002",
                "dataset_id": "DS-MEC-01",
                "file_name": "mec_tasks.csv",
                "name": "Chest X-Ray Preprocessing",
                "size_mb": 10,
                "task_type": "image_processing",
                "privacy_policy": "TRUSTED_EDGE",
                "deadline_seconds": 30,
                "required_memory_mb": 256,
                "required_storage_mb": 10,
                "dependency_ids": [],
                "source_resource": "MEC-01"
            },
            {
                "task_id": "TASK-003",
                "dataset_id": "DS-CLOUD-01",
                "file_name": "cloud_tasks.csv",
                "name": "Appointment Scheduling Sync",
                "size_mb": 5,
                "task_type": "data_aggregation",
                "privacy_policy": "CLOUD_ALLOWED",
                "deadline_seconds": 60,
                "required_memory_mb": 128,
                "required_storage_mb": 5,
                "dependency_ids": [],
                "source_resource": "CLOUD-01"
            }
        ],
        "expected_outcome": "analysis_success",
        "test_constraints": ["Valid format across all 3 tiers", "Policy adherence"]
    }
    s1_local = {"local_tasks.csv": "patient_id,heart_rate,bp_systolic,bp_diastolic,spo2\nP01,72,120,80,98\nP02,80,130,85,97\nP03,68,115,75,99\n"}
    s1_mec = {"mec_tasks.csv": "image_id,modality,resolution,slice_count,bit_depth\nIMG01,XRAY,224x224,1,16\nIMG02,CT,512x512,128,16\nIMG03,MRI,256x256,64,16\n"}
    s1_cloud = {"cloud_tasks.csv": "appointment_id,patient_id,slot_time,room_id,status\nAPT01,P01,09:00,OR-1,CONFIRMED\nAPT02,P02,10:30,OR-2,COMPLETED\n"}
    s1_tasks = {"tasks": s1_manifest["tasks"]}
    s1_expected = {
        "validation_result": "VALID",
        "analysis_status": "COMPLETED",
        "expected_eligible_resources": {
            "TASK-001": ["LOCAL-01"],
            "TASK-002": ["LOCAL-01", "MEC-01"],
            "TASK-003": ["LOCAL-01", "MEC-01", "CLOUD-01"]
        },
        "allocations": [
            {"task_id": "TASK-001", "allocated_resource": "LOCAL-01", "status": "ASSIGNED"},
            {"task_id": "TASK-002", "allocated_resource": "MEC-01", "status": "ASSIGNED"},
            {"task_id": "TASK-003", "allocated_resource": "CLOUD-01", "status": "ASSIGNED"}
        ]
    }
    s1_readme = (
        "Scenario success_01_basic_all_storage\n"
        "Tests standard baseline dataset upload containing valid files for Local, MEC, and Cloud resources."
    )
    sz = build_scenario_zip(s1_path, s1_manifest, s1_local, s1_mec, s1_cloud, s1_tasks, s1_expected, s1_readme)
    scenario_inventory.append({
        "filename": s1_path.name,
        "category": "SUCCESS",
        "purpose": "Valid data for Local, MEC, and Cloud",
        "expected": "Analysis succeeds (all 3 tasks assigned)",
        "size": sz
    })

    # =========================================================================
    # SUCCESS 02: Mixed File Formats
    # =========================================================================
    s2_path = BASE_OUTPUT_DIR / "success_02_mixed_file_formats.zip"
    s2_manifest = {
        "scenario_id": "success_02",
        "scenario_name": "Mixed File Formats",
        "scenario_category": "success",
        "description": "Verifies validation and feature extraction on supported CSV, JSON, and structured TXT clinical datasets.",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "resources": create_standard_resource_definitions(),
        "datasets": [
            {"dataset_id": "DS-CSV-01", "file_name": "vitals.csv", "format": "CSV", "size_mb": 1, "tier": "local", "privacy_policy": "LOCAL_ONLY"},
            {"dataset_id": "DS-JSON-01", "file_name": "lab_results.json", "format": "JSON", "size_mb": 2, "tier": "mec", "privacy_policy": "TRUSTED_EDGE"},
            {"dataset_id": "DS-TXT-01", "file_name": "clinical_notes.txt", "format": "TXT", "size_mb": 1, "tier": "cloud", "privacy_policy": "CLOUD_ALLOWED"}
        ],
        "tasks": [
            {
                "task_id": "TASK-FMT-01",
                "dataset_id": "DS-CSV-01",
                "file_name": "vitals.csv",
                "name": "Parse Tabular Vitals",
                "format": "CSV",
                "size_mb": 1,
                "task_type": "tabular_etl",
                "privacy_policy": "LOCAL_ONLY",
                "deadline_seconds": 20,
                "required_memory_mb": 64,
                "required_storage_mb": 1,
                "dependency_ids": [],
                "source_resource": "LOCAL-01"
            },
            {
                "task_id": "TASK-FMT-02",
                "dataset_id": "DS-JSON-01",
                "file_name": "lab_results.json",
                "name": "Parse Lab JSON Stream",
                "format": "JSON",
                "size_mb": 2,
                "task_type": "json_parsing",
                "privacy_policy": "TRUSTED_EDGE",
                "deadline_seconds": 25,
                "required_memory_mb": 128,
                "required_storage_mb": 2,
                "dependency_ids": [],
                "source_resource": "MEC-01"
            },
            {
                "task_id": "TASK-FMT-03",
                "dataset_id": "DS-TXT-01",
                "file_name": "clinical_notes.txt",
                "name": "Extract Notes Entities",
                "format": "TXT",
                "size_mb": 1,
                "task_type": "text_nlp",
                "privacy_policy": "CLOUD_ALLOWED",
                "deadline_seconds": 45,
                "required_memory_mb": 128,
                "required_storage_mb": 1,
                "dependency_ids": [],
                "source_resource": "CLOUD-01"
            }
        ],
        "expected_outcome": "analysis_success",
        "test_constraints": ["Supported CSV, JSON, TXT files analyzed"]
    }
    s2_local = {"vitals.csv": "patient,hr,spo2,temp_c\n101,75,98,36.8\n102,82,96,37.1\n103,69,99,36.6\n"}
    s2_mec = {"lab_results.json": json.dumps({"glucose_mg_dl": 95, "creatinine_mg_dl": 0.9, "status": "normal", "analytes": ["WBC", "RBC", "PLT"]}, indent=2)}
    s2_cloud = {"clinical_notes.txt": "De-identified clinical consultation note: Patient reports complete recovery post outpatient laparoscopic surgery. Follow-up scheduled in 6 weeks."}
    s2_expected = {
        "validation_result": "VALID",
        "formats_recognized": ["CSV", "JSON", "TXT"],
        "analysis_status": "COMPLETED",
        "allocations": [
            {"task_id": "TASK-FMT-01", "allocated_resource": "LOCAL-01", "status": "ASSIGNED"},
            {"task_id": "TASK-FMT-02", "allocated_resource": "MEC-01", "status": "ASSIGNED"},
            {"task_id": "TASK-FMT-03", "allocated_resource": "CLOUD-01", "status": "ASSIGNED"}
        ]
    }
    sz = build_scenario_zip(s2_path, s2_manifest, s2_local, s2_mec, s2_cloud, {"tasks": s2_manifest["tasks"]}, s2_expected, "Scenario success_02 tests multi-format parsing.")
    scenario_inventory.append({
        "filename": s2_path.name,
        "category": "SUCCESS",
        "purpose": "Valid supported CSV, JSON, and TXT samples",
        "expected": "All formats recognized and analyzed",
        "size": sz
    })

    # =========================================================================
    # SUCCESS 03: Capacity-Aware Allocation
    # =========================================================================
    s3_path = BASE_OUTPUT_DIR / "success_03_capacity_aware.zip"
    s3_resources = create_standard_resource_definitions(local_cap=50, local_avail=15, mec_cap=200, mec_avail=100, cloud_cap=2000, cloud_avail=1800)
    s3_manifest = {
        "scenario_id": "success_03",
        "scenario_name": "Capacity Aware Allocation",
        "scenario_category": "success",
        "description": "Demonstrates capacity-based eligibility routing where dataset sizes match available headroom on each tier.",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "resources": s3_resources,
        "datasets": [
            {"dataset_id": "DS-CAP-01", "file_name": "small_vitals.csv", "format": "CSV", "size_mb": 10, "tier": "local", "privacy_policy": "LOCAL_ONLY"},
            {"dataset_id": "DS-CAP-02", "file_name": "medium_scan_meta.csv", "format": "CSV", "size_mb": 75, "tier": "mec", "privacy_policy": "TRUSTED_EDGE"},
            {"dataset_id": "DS-CAP-03", "file_name": "large_archive_meta.csv", "format": "CSV", "size_mb": 500, "tier": "cloud", "privacy_policy": "CLOUD_ALLOWED"}
        ],
        "tasks": [
            {
                "task_id": "TASK-CAP-01",
                "dataset_id": "DS-CAP-01",
                "file_name": "small_vitals.csv",
                "name": "Small Local Task",
                "size_mb": 10,
                "task_type": "telemetry",
                "privacy_policy": "LOCAL_ONLY",
                "deadline_seconds": 30,
                "required_memory_mb": 64,
                "required_storage_mb": 10,
                "dependency_ids": [],
                "source_resource": "LOCAL-01"
            },
            {
                "task_id": "TASK-CAP-02",
                "dataset_id": "DS-CAP-02",
                "file_name": "medium_scan_meta.csv",
                "name": "Medium Edge Task",
                "size_mb": 75,
                "task_type": "imaging_metadata",
                "privacy_policy": "TRUSTED_EDGE",
                "deadline_seconds": 60,
                "required_memory_mb": 256,
                "required_storage_mb": 75,
                "dependency_ids": [],
                "source_resource": "MEC-01"
            },
            {
                "task_id": "TASK-CAP-03",
                "dataset_id": "DS-CAP-03",
                "file_name": "large_archive_meta.csv",
                "name": "Large Cloud Archive",
                "size_mb": 500,
                "task_type": "longitudinal_archive",
                "privacy_policy": "CLOUD_ALLOWED",
                "deadline_seconds": 120,
                "required_memory_mb": 512,
                "required_storage_mb": 500,
                "dependency_ids": [],
                "source_resource": "CLOUD-01"
            }
        ],
        "expected_outcome": "analysis_success",
        "test_constraints": ["Allocations respect tier storage capacities"]
    }
    s3_local = {"small_vitals.csv": "patient,status\nP1,OK\n" * 100}
    s3_mec = {"medium_scan_meta.csv": "scan_id,bytes\nS1,75MB\n" * 200}
    s3_cloud = {"large_archive_meta.csv": "archive_id,records\nARC1,500MB\n" * 500}
    s3_expected = {
        "validation_result": "VALID",
        "analysis_status": "COMPLETED",
        "allocations": [
            {"task_id": "TASK-CAP-01", "destination": "LOCAL-01", "status": "ASSIGNED", "reason": "Fits in 15MB local headroom"},
            {"task_id": "TASK-CAP-02", "destination": "MEC-01", "status": "ASSIGNED", "reason": "Fits in 100MB MEC headroom (too large for Local 15MB)"},
            {"task_id": "TASK-CAP-03", "destination": "CLOUD-01", "status": "ASSIGNED", "reason": "Fits in 1800MB Cloud headroom (too large for Edge 100MB)"}
        ]
    }
    sz = build_scenario_zip(s3_path, s3_manifest, s3_local, s3_mec, s3_cloud, {"tasks": s3_manifest["tasks"]}, s3_expected, "Scenario success_03 tests capacity headroom evaluation.")
    scenario_inventory.append({
        "filename": s3_path.name,
        "category": "SUCCESS",
        "purpose": "Different dataset sizes and resource capacities",
        "expected": "Eligible assignments respect capacity headroom",
        "size": sz
    })

    # =========================================================================
    # SUCCESS 04: Privacy-Aware Policy Boundary
    # =========================================================================
    s4_path = BASE_OUTPUT_DIR / "success_04_privacy_aware.zip"
    s4_manifest = {
        "scenario_id": "success_04",
        "scenario_name": "Privacy Aware Policy Enforcement",
        "scenario_category": "success",
        "description": "Verifies that strict HIPAA privacy constraints (LOCAL_ONLY, TRUSTED_EDGE, CLOUD_ALLOWED) govern tier eligibility.",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "resources": create_standard_resource_definitions(),
        "datasets": [
            {"dataset_id": "DS-PRV-01", "file_name": "confidential_ehr.csv", "format": "CSV", "size_mb": 1, "tier": "local", "privacy_policy": "LOCAL_ONLY"},
            {"dataset_id": "DS-PRV-02", "file_name": "pathology.json", "format": "JSON", "size_mb": 2, "tier": "mec", "privacy_policy": "TRUSTED_EDGE"},
            {"dataset_id": "DS-PRV-03", "file_name": "public_stats.json", "format": "JSON", "size_mb": 1, "tier": "cloud", "privacy_policy": "CLOUD_ALLOWED"}
        ],
        "tasks": [
            {
                "task_id": "TASK-PRV-01",
                "dataset_id": "DS-PRV-01",
                "file_name": "confidential_ehr.csv",
                "name": "Confidential EHR Biometrics",
                "size_mb": 1,
                "task_type": "biometric_ehr",
                "privacy_policy": "LOCAL_ONLY",
                "deadline_seconds": 15,
                "required_memory_mb": 64,
                "required_storage_mb": 1,
                "dependency_ids": [],
                "source_resource": "LOCAL-01",
                "eligible": ["LOCAL-01"],
                "ineligible": ["MEC-01", "CLOUD-01"]
            },
            {
                "task_id": "TASK-PRV-02",
                "dataset_id": "DS-PRV-02",
                "file_name": "pathology.json",
                "name": "Pathology Telemetry",
                "size_mb": 2,
                "task_type": "pathology_diagnostic",
                "privacy_policy": "TRUSTED_EDGE",
                "deadline_seconds": 30,
                "required_memory_mb": 128,
                "required_storage_mb": 2,
                "dependency_ids": [],
                "source_resource": "MEC-01",
                "eligible": ["LOCAL-01", "MEC-01"],
                "ineligible": ["CLOUD-01"]
            },
            {
                "task_id": "TASK-PRV-03",
                "dataset_id": "DS-PRV-03",
                "file_name": "public_stats.json",
                "name": "Public De-Identified Statistics",
                "size_mb": 1,
                "task_type": "statistical_summary",
                "privacy_policy": "CLOUD_ALLOWED",
                "deadline_seconds": 45,
                "required_memory_mb": 64,
                "required_storage_mb": 1,
                "dependency_ids": [],
                "source_resource": "CLOUD-01",
                "eligible": ["LOCAL-01", "MEC-01", "CLOUD-01"],
                "ineligible": []
            }
        ],
        "expected_outcome": "analysis_success",
        "test_constraints": ["Policy-permitted destinations only"]
    }
    s4_local = {"confidential_ehr.csv": "patient_uuid,ssn_masked,phi_level\nUUID-1,***-**-1234,TIER_1_STRICT\nUUID-2,***-**-5678,TIER_1_STRICT\n"}
    s4_mec = {"pathology.json": json.dumps({"tissue_sample": "SPEC-99", "edge_inference_model": "histopathology_v2", "stain": "H&E"})}
    s4_cloud = {"public_stats.json": json.dumps({"annual_cases": 12450, "average_stay_days": 3.8, "readmission_rate_pct": 4.2})}
    s4_expected = {
        "validation_result": "VALID",
        "analysis_status": "COMPLETED",
        "policy_evaluations": {
            "TASK-PRV-01": {"eligible_destinations": ["LOCAL-01"], "blocked_destinations": ["MEC-01", "CLOUD-01"]},
            "TASK-PRV-02": {"eligible_destinations": ["LOCAL-01", "MEC-01"], "blocked_destinations": ["CLOUD-01"]},
            "TASK-PRV-03": {"eligible_destinations": ["LOCAL-01", "MEC-01", "CLOUD-01"], "blocked_destinations": []}
        },
        "allocations": [
            {"task_id": "TASK-PRV-01", "allocated_resource": "LOCAL-01", "status": "ASSIGNED"},
            {"task_id": "TASK-PRV-02", "allocated_resource": "MEC-01", "status": "ASSIGNED"},
            {"task_id": "TASK-PRV-03", "allocated_resource": "CLOUD-01", "status": "ASSIGNED"}
        ]
    }
    sz = build_scenario_zip(s4_path, s4_manifest, s4_local, s4_mec, s4_cloud, {"tasks": s4_manifest["tasks"]}, s4_expected, "Scenario success_04 tests HIPAA policy boundaries.")
    scenario_inventory.append({
        "filename": s4_path.name,
        "category": "SUCCESS",
        "purpose": "Different privacy policies across datasets",
        "expected": "Only policy-permitted destinations are eligible",
        "size": sz
    })

    # =========================================================================
    # SUCCESS 05: Multi-Task GA Scheduling
    # =========================================================================
    s5_path = BASE_OUTPUT_DIR / "success_05_multi_task_scheduling.zip"
    s5_tasks_list = [
        {"task_id": "TASK-M-01", "dataset_id": "DS-M-01", "file_name": "triage.csv", "name": "Triage Biometrics", "size_mb": 2, "task_type": "vitals", "privacy_policy": "LOCAL_ONLY", "deadline_seconds": 10, "required_memory_mb": 64, "required_storage_mb": 2, "dependency_ids": [], "source_resource": "LOCAL-01"},
        {"task_id": "TASK-M-02", "dataset_id": "DS-M-02", "file_name": "xray_batch.csv", "name": "Chest X-Ray CLAHE", "size_mb": 12, "task_type": "imaging", "privacy_policy": "TRUSTED_EDGE", "deadline_seconds": 25, "required_memory_mb": 256, "required_storage_mb": 12, "dependency_ids": [], "source_resource": "MEC-01"},
        {"task_id": "TASK-M-03", "dataset_id": "DS-M-03", "file_name": "mri_batch.csv", "name": "MRI Denoising", "size_mb": 18, "task_type": "imaging", "privacy_policy": "TRUSTED_EDGE", "deadline_seconds": 35, "required_memory_mb": 512, "required_storage_mb": 18, "dependency_ids": [], "source_resource": "MEC-01"},
        {"task_id": "TASK-M-04", "dataset_id": "DS-M-04", "file_name": "lab_batch.csv", "name": "Lab Analyte Grading", "size_mb": 4, "task_type": "lab_data", "privacy_policy": "TRUSTED_EDGE", "deadline_seconds": 20, "required_memory_mb": 128, "required_storage_mb": 4, "dependency_ids": [], "source_resource": "MEC-01"},
        {"task_id": "TASK-M-05", "dataset_id": "DS-M-05", "file_name": "billing_batch.csv", "name": "Billing Audit Aggregation", "size_mb": 8, "task_type": "admin_audit", "privacy_policy": "CLOUD_ALLOWED", "deadline_seconds": 60, "required_memory_mb": 128, "required_storage_mb": 8, "dependency_ids": [], "source_resource": "CLOUD-01"},
        {"task_id": "TASK-M-06", "dataset_id": "DS-M-06", "file_name": "schedule_matrix.csv", "name": "Appointment Matrix Optimization", "size_mb": 6, "task_type": "coordination", "privacy_policy": "CLOUD_ALLOWED", "deadline_seconds": 50, "required_memory_mb": 128, "required_storage_mb": 6, "dependency_ids": [], "source_resource": "CLOUD-01"}
    ]
    s5_manifest = {
        "scenario_id": "success_05",
        "scenario_name": "Multi-Task GA Scheduling Batch",
        "scenario_category": "success",
        "description": "Six heterogeneous clinical workloads evaluated by Genetic Algorithm for balanced latency and energy optimization.",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "resources": create_standard_resource_definitions(),
        "datasets": [
            {"dataset_id": t["dataset_id"], "file_name": t["file_name"], "format": "CSV", "size_mb": t["size_mb"], "tier": "local" if "LOCAL" in t["source_resource"] else ("mec" if "MEC" in t["source_resource"] else "cloud"), "privacy_policy": t["privacy_policy"]}
            for t in s5_tasks_list
        ],
        "tasks": s5_tasks_list,
        "expected_outcome": "analysis_success",
        "test_constraints": ["Traceable GA scheduling decisions", "Zero constraint violations"]
    }
    s5_local = {"triage.csv": "patient,score\nP10,2\nP11,0\n"}
    s5_mec = {
        "xray_batch.csv": "img_id,type\nI1,XRAY\n",
        "mri_batch.csv": "mri_id,field_tesla\nM1,3.0\n",
        "lab_batch.csv": "analyte,val\nCRP,4.2\n"
    }
    s5_cloud = {
        "billing_batch.csv": "batch,records\nB1,150\nB2,200\n",
        "schedule_matrix.csv": "dept,slots\nCardio,12\nNeuro,8\n"
    }
    s5_expected = {
        "validation_result": "VALID",
        "total_tasks": 6,
        "scheduler_algorithm": "Genetic Algorithm",
        "unassigned_count": 0,
        "allocations": [
            {"task_id": "TASK-M-01", "allocated_resource": "LOCAL-01", "status": "ASSIGNED"},
            {"task_id": "TASK-M-02", "allocated_resource": "MEC-01", "status": "ASSIGNED"},
            {"task_id": "TASK-M-03", "allocated_resource": "MEC-01", "status": "ASSIGNED"},
            {"task_id": "TASK-M-04", "allocated_resource": "MEC-01", "status": "ASSIGNED"},
            {"task_id": "TASK-M-05", "allocated_resource": "CLOUD-01", "status": "ASSIGNED"},
            {"task_id": "TASK-M-06", "allocated_resource": "CLOUD-01", "status": "ASSIGNED"}
        ]
    }
    sz = build_scenario_zip(s5_path, s5_manifest, s5_local, s5_mec, s5_cloud, {"tasks": s5_tasks_list}, s5_expected, "Scenario success_05 tests GA batch optimization.")
    scenario_inventory.append({
        "filename": s5_path.name,
        "category": "SUCCESS",
        "purpose": "Several independent tasks across three resources",
        "expected": "Scheduler produces traceable decisions (6/6 assigned)",
        "size": sz
    })

    # =========================================================================
    # FAILED 01: Corrupt Truncated Archive
    # =========================================================================
    f1_path = BASE_OUTPUT_DIR / "failed_01_corrupt_archive.zip"
    corrupt_bytes = b"PK\x03\x04\x14\x00\x00\x00\x08\x00" + b"\xde\xad\xbe\xef" * 20 + b"TRUNCATED_NON_TERMINATED_ZIP_HEADER"
    with open(f1_path, "wb") as fh:
        fh.write(corrupt_bytes)

    f1_readme_path = BASE_OUTPUT_DIR / "README_failed_01_corrupt_archive.txt"
    with open(f1_readme_path, "w", encoding="utf-8") as fh:
        fh.write(
            "TEST PURPOSE: failed_01_corrupt_archive.zip\n"
            "===========================================\n"
            "This file is intentionally truncated to test ZIP integrity and defensive archive parsing.\n"
            "EXPECTED RESULT:\n"
            "The upload validation service detects the corrupted headers via zipfile.testzip() or invalid header check,\n"
            "rejects the archive gracefully, logs an audit event, and avoids server crashing.\n"
        )
    scenario_inventory.append({
        "filename": f1_path.name,
        "category": "FAILED",
        "purpose": "Invalid or truncated ZIP archive",
        "expected": "Archive validation fails safely",
        "size": len(corrupt_bytes)
    })

    # =========================================================================
    # FAILED 02: Invalid Manifest Structure
    # =========================================================================
    f2_path = BASE_OUTPUT_DIR / "failed_02_invalid_manifest.zip"
    f2_manifest = {
        "description": "Intentionally malformed manifest missing required fields (scenario_id, resources, tasks).",
        "corrupted_key_without_schema": True
    }
    f2_expected = {
        "validation_result": "MANIFEST_INVALID",
        "expected_error": "Missing mandatory field 'scenario_id' and 'resources' in manifest.json",
        "status": "REJECTED_INVALID_MANIFEST"
    }
    dummy_local_res = {"resource_id": "LOCAL-01", "status": "online"}
    dummy_mec_res = {"resource_id": "MEC-01", "status": "online"}
    dummy_cloud_res = {"resource_id": "CLOUD-01", "status": "online"}

    sz = build_scenario_zip(
        f2_path,
        f2_manifest,
        {"local_tasks.csv": "patient,val\n1,10\n"},
        {"mec_tasks.csv": "scan,val\nS1,20\n"},
        {"cloud_tasks.csv": "report,val\nR1,30\n"},
        {"invalid_task_list": None},
        f2_expected,
        "Scenario failed_02 tests manifest schema rejection.",
        local_resource_override=dummy_local_res,
        mec_resource_override=dummy_mec_res,
        cloud_resource_override=dummy_cloud_res,
    )
    scenario_inventory.append({
        "filename": f2_path.name,
        "category": "FAILED",
        "purpose": "Missing required fields or invalid manifest structure",
        "expected": "Manifest validation fails with clear error",
        "size": sz
    })

    # =========================================================================
    # FAILED 03: Capacity or Policy Violation (Unassigned / Rejected)
    # =========================================================================
    f3_path = BASE_OUTPUT_DIR / "failed_03_capacity_or_policy_violation.zip"
    f3_resources = create_standard_resource_definitions(local_cap=50, local_avail=10, mec_cap=200, mec_avail=150, cloud_cap=5000, cloud_avail=4000)
    f3_manifest = {
        "scenario_id": "failed_03",
        "scenario_name": "Capacity & Policy Constraint Violation",
        "scenario_category": "failed",
        "description": "Task has LOCAL_ONLY policy (ineligible for MEC/Cloud) and requires 300MB, exceeding Local available capacity (10MB). Must remain unassigned.",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "resources": f3_resources,
        "datasets": [
            {"dataset_id": "DS-GENOMICS-01", "file_name": "oversized_genomics.csv", "format": "CSV", "size_mb": 300, "tier": "local", "privacy_policy": "LOCAL_ONLY"}
        ],
        "tasks": [
            {
                "task_id": "TASK-UNASSIGNABLE-01",
                "dataset_id": "DS-GENOMICS-01",
                "file_name": "oversized_genomics.csv",
                "name": "Oversized Confidential Genomic Biometrics",
                "size_mb": 300,
                "task_type": "genomics",
                "privacy_policy": "LOCAL_ONLY",
                "deadline_seconds": 60,
                "required_memory_mb": 1024,
                "required_storage_mb": 300,
                "dependency_ids": [],
                "source_resource": "LOCAL-01"
            }
        ],
        "expected_outcome": "unassigned_or_rejected",
        "test_constraints": ["Capacity and privacy violation must cause safe unassigned status without false success"]
    }
    f3_expected = {
        "validation_result": "VALID_CONTAINER",
        "analysis_status": "COMPLETED_WITH_UNASSIGNED",
        "scheduling_result": "UNASSIGNED",
        "unassigned_tasks": ["TASK-UNASSIGNABLE-01"],
        "reason": "Local tier capacity exceeded (requires 300MB, only 10MB free); MEC and Cloud prohibited by LOCAL_ONLY policy."
    }
    sz = build_scenario_zip(
        f3_path,
        f3_manifest,
        {"oversized_genomics.csv": "gene,marker\nG1,M1\n" * 100},
        {"mec_empty.csv": "empty\n"},
        {"cloud_empty.csv": "empty\n"},
        {"tasks": f3_manifest["tasks"]},
        f3_expected,
        "Scenario failed_03 tests unassignable task handling without false success reporting."
    )
    scenario_inventory.append({
        "filename": f3_path.name,
        "category": "FAILED",
        "purpose": "Tasks exceed capacity or violate privacy constraints",
        "expected": "Invalid assignments rejected or remain unassigned",
        "size": sz
    })

    # =========================================================================
    # LOOP 01: Large Bounded Queue
    # =========================================================================
    l1_path = BASE_OUTPUT_DIR / "loop_01_large_task_queue.zip"
    l1_tasks_list = [
        {
            "task_id": f"TASK-QUEUE-{i:03d}",
            "dataset_id": f"DS-QUEUE-{i:03d}",
            "file_name": f"batch_item_{i}.csv",
            "name": f"Batch Workload Item {i}",
            "size_mb": 1,
            "task_type": "batch_job",
            "privacy_policy": "TRUSTED_EDGE" if i % 2 == 0 else "CLOUD_ALLOWED",
            "deadline_seconds": 30,
            "required_memory_mb": 64,
            "required_storage_mb": 1,
            "dependency_ids": [],
            "source_resource": "MEC-01" if i % 2 == 0 else "CLOUD-01"
        }
        for i in range(1, 46)
    ]
    l1_manifest = {
        "scenario_id": "loop_01",
        "scenario_name": "Large Bounded Task Queue",
        "scenario_category": "loop_timeout",
        "description": "Tests scheduler batch limits and queue responsiveness under a bounded batch of 45 clinical workloads.",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "resources": create_standard_resource_definitions(),
        "datasets": [
            {"dataset_id": "DS-BATCH-LOCAL", "file_name": "batch_local.csv", "format": "CSV", "size_mb": 2, "tier": "local", "privacy_policy": "LOCAL_ONLY"},
            {"dataset_id": "DS-BATCH-MEC", "file_name": "batch_mec.csv", "format": "CSV", "size_mb": 2, "tier": "mec", "privacy_policy": "TRUSTED_EDGE"},
            {"dataset_id": "DS-BATCH-CLOUD", "file_name": "batch_cloud.csv", "format": "CSV", "size_mb": 2, "tier": "cloud", "privacy_policy": "CLOUD_ALLOWED"}
        ],
        "tasks": l1_tasks_list,
        "batch_limit": 50,
        "expected_outcome": "bounded_batch_success",
        "test_constraints": ["Processes 45 items in bounded batch without infinite loop"]
    }
    l1_expected = {
        "validation_result": "VALID",
        "queue_length": 45,
        "batch_limit": 50,
        "status": "BATCH_PROCESSED_WITHIN_LIMITS",
        "safe_handling": True
    }
    sz = build_scenario_zip(
        l1_path,
        l1_manifest,
        {"batch_local.csv": "task,status\n" + "\n".join(f"T_LOC_{i},OK" for i in range(15))},
        {"batch_mec.csv": "task,status\n" + "\n".join(f"T_MEC_{i},OK" for i in range(15))},
        {"batch_cloud.csv": "task,status\n" + "\n".join(f"T_CLD_{i},OK" for i in range(15))},
        {"tasks": l1_tasks_list},
        l1_expected,
        "Scenario loop_01 tests bounded queue limits."
    )
    scenario_inventory.append({
        "filename": l1_path.name,
        "category": "LOOP/TIMEOUT",
        "purpose": "Large but bounded task queue",
        "expected": "Processing remains responsive or reports overload",
        "size": sz
    })

    # =========================================================================
    # LOOP 02: Dependency Cycle Detection
    # =========================================================================
    l2_path = BASE_OUTPUT_DIR / "loop_02_dependency_cycle.zip"
    l2_manifest = {
        "scenario_id": "loop_02",
        "scenario_name": "Task Dependency Cycle Detection",
        "scenario_category": "loop_timeout",
        "description": "Simulates cyclic workflow dependencies (TASK-CYC-A -> TASK-CYC-B -> TASK-CYC-C -> TASK-CYC-A). Scheduler must detect the cycle and break loop.",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "resources": create_standard_resource_definitions(),
        "datasets": [
            {"dataset_id": "DS-CYC-01", "file_name": "cyc_local.json", "format": "JSON", "size_mb": 1, "tier": "local", "privacy_policy": "LOCAL_ONLY"},
            {"dataset_id": "DS-CYC-02", "file_name": "cyc_mec.json", "format": "JSON", "size_mb": 1, "tier": "mec", "privacy_policy": "TRUSTED_EDGE"},
            {"dataset_id": "DS-CYC-03", "file_name": "cyc_cloud.json", "format": "JSON", "size_mb": 1, "tier": "cloud", "privacy_policy": "CLOUD_ALLOWED"}
        ],
        "tasks": [
            {"task_id": "TASK-CYC-A", "dataset_id": "DS-CYC-01", "file_name": "cyc_local.json", "name": "Telemetry Ingest A", "size_mb": 1, "privacy_policy": "LOCAL_ONLY", "dependency_ids": ["TASK-CYC-C"], "source_resource": "LOCAL-01"},
            {"task_id": "TASK-CYC-B", "dataset_id": "DS-CYC-02", "file_name": "cyc_mec.json", "name": "Edge Aggregator B", "size_mb": 1, "privacy_policy": "TRUSTED_EDGE", "dependency_ids": ["TASK-CYC-A"], "source_resource": "MEC-01"},
            {"task_id": "TASK-CYC-C", "dataset_id": "DS-CYC-03", "file_name": "cyc_cloud.json", "name": "Analytics Publisher C", "size_mb": 1, "privacy_policy": "CLOUD_ALLOWED", "dependency_ids": ["TASK-CYC-B"], "source_resource": "CLOUD-01"}
        ],
        "expected_outcome": "cycle_detected_rejection",
        "test_constraints": ["Detect dependency cycles and safely reject"]
    }
    l2_expected = {
        "validation_result": "CYCLE_DETECTED",
        "cycle_path": ["TASK-CYC-A", "TASK-CYC-B", "TASK-CYC-C", "TASK-CYC-A"],
        "status": "REJECTED_CYCLIC_DEPENDENCY",
        "safe_handling": True
    }
    sz = build_scenario_zip(
        l2_path,
        l2_manifest,
        {"cyc_local.json": '{"task": "TASK-CYC-A"}'},
        {"cyc_mec.json": '{"task": "TASK-CYC-B"}'},
        {"cyc_cloud.json": '{"task": "TASK-CYC-C"}'},
        {"tasks": l2_manifest["tasks"]},
        l2_expected,
        "Scenario loop_02 tests circular dependency detection."
    )
    scenario_inventory.append({
        "filename": l2_path.name,
        "category": "LOOP/TIMEOUT",
        "purpose": "Task dependency metadata contains a cycle",
        "expected": "Cycle is detected and safely rejected",
        "size": sz
    })

    # =========================================================================
    # LOOP 03: Timeout Simulation
    # =========================================================================
    l3_path = BASE_OUTPUT_DIR / "loop_03_timeout_simulation.zip"
    l3_manifest = {
        "scenario_id": "loop_03",
        "scenario_name": "Resource Timeout & Watchdog Simulation",
        "scenario_category": "loop_timeout",
        "description": "Configures task execution exceeding watchdog limit (timeout_seconds: 2, simulated_latency_ms: 5000, max_retries: 3).",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "resources": create_standard_resource_definitions(),
        "datasets": [
            {"dataset_id": "DS-TIME-01", "file_name": "timeout_task.json", "format": "JSON", "size_mb": 1, "tier": "local", "privacy_policy": "LOCAL_ONLY"},
            {"dataset_id": "DS-TIME-02", "file_name": "timeout_edge.json", "format": "JSON", "size_mb": 1, "tier": "mec", "privacy_policy": "TRUSTED_EDGE"},
            {"dataset_id": "DS-TIME-03", "file_name": "timeout_cloud.json", "format": "JSON", "size_mb": 1, "tier": "cloud", "privacy_policy": "CLOUD_ALLOWED"}
        ],
        "tasks": [
            {
                "task_id": "TASK-TIMEOUT-01",
                "dataset_id": "DS-TIME-01",
                "file_name": "timeout_task.json",
                "name": "Simulated Delayed Inference",
                "size_mb": 1,
                "timeout_seconds": 2,
                "deadline_seconds": 1,
                "simulated_latency_ms": 5000,
                "max_retries": 3,
                "privacy_policy": "TRUSTED_EDGE",
                "dependency_ids": [],
                "source_resource": "MEC-01"
            }
        ],
        "expected_outcome": "timeout_watchdog_cancellation",
        "test_constraints": ["Task times out, retries within limits, or is cancelled safely"]
    }
    l3_expected = {
        "validation_result": "VALID",
        "execution_status": "TIMED_OUT",
        "retries_attempted": 3,
        "terminated_by": "WatchdogTimer",
        "safe_handling": True
    }
    sz = build_scenario_zip(
        l3_path,
        l3_manifest,
        {"timeout_task.json": '{"mode": "simulated_delay", "delay_ms": 5000}'},
        {"timeout_edge.json": '{"edge_listener": "active"}'},
        {"timeout_cloud.json": '{"cloud_sync": "active"}'},
        {"tasks": l3_manifest["tasks"]},
        l3_expected,
        "Scenario loop_03 tests watchdog timeout termination."
    )
    scenario_inventory.append({
        "filename": l3_path.name,
        "category": "LOOP/TIMEOUT",
        "purpose": "Resource response configured to exceed test timeout",
        "expected": "Task times out, retries within limits, cancelled safely",
        "size": sz
    })

    # =========================================================================
    # Copy all 11 scenario ZIPs into sample_upload_datasets for web interface
    # =========================================================================
    for sc in scenario_inventory:
        src = BASE_OUTPUT_DIR / sc["filename"]
        dst = SAMPLE_UPLOAD_DIR / sc["filename"]
        if src.exists():
            with open(src, "rb") as f_in, open(dst, "wb") as f_out:
                f_out.write(f_in.read())

    # Copy external README for corrupt archive
    if f1_readme_path.exists():
        with open(f1_readme_path, "r", encoding="utf-8") as f_in, open(SAMPLE_UPLOAD_DIR / f1_readme_path.name, "w", encoding="utf-8") as f_out:
            f_out.write(f_in.read())

    # =========================================================================
    # Generate Inventory CSV
    # =========================================================================
    csv_path = BASE_OUTPUT_DIR / "dataset_test_matrix_inventory.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["Scenario Filename", "Category", "Validation Purpose", "Expected Outcome", "Size (Bytes)", "SHA-256 Checksum"])
        for sc in scenario_inventory:
            p = BASE_OUTPUT_DIR / sc["filename"]
            with open(p, "rb") as f:
                sha = calc_sha256(f.read())
            writer.writerow([sc["filename"], sc["category"], sc["purpose"], sc["expected"], sc["size"], sha])

    with open(csv_path, "rb") as f_in, open(SAMPLE_UPLOAD_DIR / csv_path.name, "wb") as f_out:
        f_out.write(f_in.read())

    # =========================================================================
    # Generate Root Master README.md
    # =========================================================================
    root_readme_path = BASE_OUTPUT_DIR / "README.md"
    master_readme_text = (
        "# SecureDT — Digital Twin Edge–Cloud Master Test Dataset Suite\n\n"
        "This suite contains **11 standardized ZIP test datasets** for testing the project's dataset upload, "
        "validation, analysis, storage eligibility, task scheduling, failure handling, and timeout detection.\n\n"
        "## Infrastructure Resources Represented\n"
        "1. **Local Storage** (`LOCAL-01`): On-premises hospital workstation (HIPAA Tier-1 Vault, `LOCAL_ONLY` policy).\n"
        "2. **MEC/Edge Storage** (`MEC-01`): Nearby trusted edge cluster (`TRUSTED_EDGE` policy, low-latency compute).\n"
        "3. **Cloud Storage** (`CLOUD-01`): Central cloud repository (`CLOUD_ALLOWED` policy, large-capacity aggregate).\n\n"
        "## Test Scenarios Overview\n\n"
        "### Category A: Successful Datasets (5 archives)\n"
        "| Filename | Test Purpose | Expected Outcome |\n"
        "|---|---|---|\n"
        "| `success_01_basic_all_storage.zip` | Valid data for Local, MEC, and Cloud | Analysis succeeds (3/3 assigned) |\n"
        "| `success_02_mixed_file_formats.zip` | Valid supported CSV, JSON, and TXT samples | All formats parsed and analyzed |\n"
        "| `success_03_capacity_aware.zip` | Different dataset sizes and resource capacities | Assignments respect capacity headroom |\n"
        "| `success_04_privacy_aware.zip` | Different privacy policies across datasets | Only policy-permitted destinations are eligible |\n"
        "| `success_05_multi_task_scheduling.zip` | 6 independent tasks across three resources | GA scheduler produces traceable decisions |\n\n"
        "### Category B: Failed Datasets (3 archives)\n"
        "| Filename | Test Purpose | Expected Outcome |\n"
        "|---|---|---|\n"
        "| `failed_01_corrupt_archive.zip` | Invalid or truncated ZIP archive | Archive validation fails safely (HTTP 400) |\n"
        "| `failed_02_invalid_manifest.zip` | Missing required fields or invalid manifest structure | Manifest validation fails with clear error |\n"
        "| `failed_03_capacity_or_policy_violation.zip` | Tasks exceed capacity or violate privacy constraints | Invalid assignments rejected / unassigned |\n\n"
        "### Category C: Loop and Timeout Datasets (3 archives)\n"
        "| Filename | Test Purpose | Expected Outcome |\n"
        "|---|---|---|\n"
        "| `loop_01_large_task_queue.zip` | Large but bounded task queue (45 tasks) | Processing remains responsive within limits |\n"
        "| `loop_02_dependency_cycle.zip` | Task dependency metadata contains a cycle | Cycle detected and rejected safely |\n"
        "| `loop_03_timeout_simulation.zip` | Resource response exceeds test timeout | Times out safely, bounds retries |\n\n"
        "## Internal Directory Structure\n"
        "Every valid ZIP archive follows this structure:\n"
        "```text\n"
        "scenario_name.zip\n"
        "├── manifest.json\n"
        "├── README.txt\n"
        "├── local/\n"
        "│   ├── resource.json\n"
        "│   └── dataset/\n"
        "│       └── local_tasks.csv\n"
        "├── mec/\n"
        "│   ├── resource.json\n"
        "│   └── dataset/\n"
        "│       └── mec_tasks.csv\n"
        "├── cloud/\n"
        "│   ├── resource.json\n"
        "│   └── dataset/\n"
        "│       └── cloud_tasks.csv\n"
        "├── tasks/\n"
        "│   └── task_metadata.json\n"
        "└── expected_results/\n"
        "    └── expected_result.json\n"
        "```\n\n"
        "## How to Test\n"
        "1. Open the SecureDT application in your browser: `http://127.0.0.1:8000/upload/`\n"
        "2. Click **Choose Archive** and select any of the 11 scenario ZIP files (or pick from the quick preset dropdown).\n"
        "3. Choose **Simulation Mode** or **Execution Mode** and click **Upload & Analyze Archive**.\n"
        "4. Observe the real-time 10-stage analysis pipeline and verify the persistent report against `expected_results/expected_result.json`.\n"
    )
    with open(root_readme_path, "w", encoding="utf-8") as fh:
        fh.write(master_readme_text)

    # =========================================================================
    # Generate Master Suite ZIP
    # =========================================================================
    master_zip_path = BASE_OUTPUT_DIR / "master_test_datasets_suite.zip"
    with zipfile.ZipFile(master_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README.md", master_readme_text)
        zf.write(csv_path, arcname="dataset_test_matrix_inventory.csv")
        zf.write(f1_readme_path, arcname="README_failed_01_corrupt_archive.txt")
        for sc in scenario_inventory:
            zf.write(BASE_OUTPUT_DIR / sc["filename"], arcname=f"scenarios/{sc['filename']}")

    with open(master_zip_path, "rb") as f_in, open(SAMPLE_UPLOAD_DIR / master_zip_path.name, "wb") as f_out:
        f_out.write(f_in.read())

    print(f"\nMaster Suite generated: {master_zip_path} ({os.path.getsize(master_zip_path)} bytes)")
    print(f"Total scenario archives: {len(scenario_inventory)}")
    print(f"Inventory CSV: {csv_path}")
    print(f"Root README: {root_readme_path}")


if __name__ == "__main__":
    generate_all_scenarios()
