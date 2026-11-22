"""
Generator for Test ZIP Packages with 3-Storage Systems Coverage:
1. complete_hospital_suite_11_datasets.zip (5 Success + 3 Failed + 3 Loop Datasets)
2. success_5_datasets_tri_storage.zip (5 Success across Local, MEC, Cloud)
3. failed_3_datasets_error_batch.zip (3 Error / Malformed / Unsupported Datasets)
4. loop_3_datasets_timeout_batch.zip (3 Looping / Watchdog / Timeout Datasets)
"""

import os
import io
import json
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw


def build_manifest(
    scenario_id: str,
    package_name: str,
    description: str,
    dataset_meta: dict,
    scenario_category: str = "success",
    **extra,
) -> dict:
    """Build a manifest that satisfies the mandatory Section 5 schema fields."""
    return {
        "scenario_id": scenario_id,
        "scenario_name": package_name,
        "scenario_category": scenario_category,
        "package_name": package_name,
        "description": description,
        "resources": [
            {
                "resource_id": "LOCAL-01",
                "resource_name": "Hospital Local Workstation Storage",
                "resource_type": "local",
                "capacity_mb": 51200,
                "available_mb": 40000,
                "status": "online",
                "trusted": True,
                "privacy_tier_allowed": "LOCAL_ONLY",
            },
            {
                "resource_id": "MEC-01",
                "resource_name": "Hospital MEC Edge Node Cluster",
                "resource_type": "mec",
                "capacity_mb": 204800,
                "available_mb": 150000,
                "status": "online",
                "trusted": True,
                "privacy_tier_allowed": "TRUSTED_EDGE",
            },
            {
                "resource_id": "CLOUD-01",
                "resource_name": "Central Cloud Storage Repository",
                "resource_type": "cloud",
                "capacity_mb": 1024000,
                "available_mb": 800000,
                "status": "online",
                "trusted": True,
                "privacy_tier_allowed": "CLOUD_ALLOWED",
            },
        ],
        "datasets": dataset_meta,
        **extra,
        **dataset_meta,
    }


def create_synthetic_xray_image() -> bytes:
    """Create a realistic synthetic 224x224 grayscale medical image."""
    img = Image.new("L", (224, 224), color=20)
    draw = ImageDraw.Draw(img)
    # Draw simulated rib cage and lung field contours
    draw.ellipse([30, 40, 95, 180], fill=65, outline=90)
    draw.ellipse([129, 40, 194, 180], fill=60, outline=90)
    draw.rectangle([96, 30, 128, 190], fill=140)  # Spine / sternum
    draw.ellipse([70, 90, 140, 160], fill=110)   # Cardiac silhouette
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_corrupted_image_bytes() -> bytes:
    """Create a corrupted non-image header byte stream."""
    return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"\xff\x00\xde\xad\xbe\xef\x00\x00TRUNCATED_CORRUPT_BUFFER_EOF"


def generate_packages():
    output_dir = Path("sample_upload_datasets")
    output_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # 1. Five Success Datasets
    # -------------------------------------------------------------------------
    # Success 1 (LOCAL_STORAGE): Patient Clinical Vitals CSV
    vitals_csv_content = (
        "patient_id,encounter_id,heart_rate,blood_pressure_sys,blood_pressure_dia,respiratory_rate,spo2,temperature_c,news2_score,clinical_status\n"
        "PAT-8812,ENC-2026-0912,74,122,78,16,98,36.8,1,STABLE\n"
        "PAT-8813,ENC-2026-0913,88,136,84,18,97,37.2,2,MONITOR\n"
        "PAT-8814,ENC-2026-0914,104,95,62,24,93,38.6,7,HIGH_ACUITY\n"
        "PAT-8815,ENC-2026-0915,68,118,76,14,99,36.6,0,NORMAL\n"
        "PAT-8816,ENC-2026-0916,82,126,80,17,97,37.0,1,STABLE\n"
    )

    # Success 2 (MEC_STORAGE): Radiological Scan PNG
    xray_png_bytes = create_synthetic_xray_image()

    # Success 3 (CLOUD_STORAGE): Outpatient Appointments Schedule JSON
    appointments_json = {
        "schedule_batch_id": "SCHED-BATCH-20261023",
        "clinic_department": "Outpatient Multi-Specialty Clinic",
        "target_storage": "CLOUD_STORAGE",
        "privacy_policy": "CLOUD_ALLOWED",
        "total_appointments": 8,
        "records": [
            {"slot_id": "SLOT-01", "room": "OR-101", "specialty": "Cardiology", "status": "CONFIRMED", "start_time": "08:30", "duration_min": 30},
            {"slot_id": "SLOT-02", "room": "OR-102", "specialty": "Pulmonology", "status": "CONFIRMED", "start_time": "09:00", "duration_min": 45},
            {"slot_id": "SLOT-03", "room": "OR-103", "specialty": "Neurology", "status": "CONFIRMED", "start_time": "09:30", "duration_min": 30},
            {"slot_id": "SLOT-04", "room": "OR-101", "specialty": "Cardiology", "status": "CONFIRMED", "start_time": "10:15", "duration_min": 30},
            {"slot_id": "SLOT-05", "room": "OR-104", "specialty": "Orthopedics", "status": "CONFIRMED", "start_time": "11:00", "duration_min": 60},
            {"slot_id": "SLOT-06", "room": "OR-102", "specialty": "Pulmonology", "status": "CONFIRMED", "start_time": "11:30", "duration_min": 30},
            {"slot_id": "SLOT-07", "room": "OR-103", "specialty": "Neurology", "status": "CONFIRMED", "start_time": "13:00", "duration_min": 45},
            {"slot_id": "SLOT-08", "room": "OR-101", "specialty": "Cardiology", "status": "CONFIRMED", "start_time": "14:00", "duration_min": 30},
        ]
    }

    # Success 4 (MEC_STORAGE): Laboratory Metabolic Panel JSON
    lab_panel_json = {
        "laboratory_order_id": "LAB-2026-7731",
        "specimen_type": "Whole Blood / Serum",
        "target_storage": "MEC_STORAGE",
        "privacy_policy": "TRUSTED_EDGE",
        "analytes": [
            {"analyte": "Glucose", "value": 98.4, "unit": "mg/dL", "reference_range": "70-99", "status": "NORMAL"},
            {"analyte": "Blood Urea Nitrogen", "value": 14.2, "unit": "mg/dL", "reference_range": "7-20", "status": "NORMAL"},
            {"analyte": "Creatinine", "value": 0.95, "unit": "mg/dL", "reference_range": "0.7-1.3", "status": "NORMAL"},
            {"analyte": "Sodium", "value": 141.0, "unit": "mEq/L", "reference_range": "136-145", "status": "NORMAL"},
            {"analyte": "Potassium", "value": 4.3, "unit": "mEq/L", "reference_range": "3.5-5.1", "status": "NORMAL"},
            {"analyte": "Chloride", "value": 102.0, "unit": "mEq/L", "reference_range": "96-106", "status": "NORMAL"},
            {"analyte": "Carbon Dioxide", "value": 24.0, "unit": "mEq/L", "reference_range": "23-29", "status": "NORMAL"},
            {"analyte": "Calcium", "value": 9.2, "unit": "mg/dL", "reference_range": "8.5-10.2", "status": "NORMAL"},
        ]
    }

    # Success 5 (LOCAL_STORAGE): Clinical Encounter Document JSON
    encounter_doc_json = {
        "encounter_id": "ENC-2026-9041",
        "department": "Emergency Medicine / Acute Care",
        "target_storage": "LOCAL_STORAGE",
        "privacy_policy": "LOCAL_ONLY",
        "attending_specialty": "Emergency Medicine",
        "icd10_diagnoses": [
            {"code": "J18.9", "description": "Pneumonia, unspecified organism", "primary": True},
            {"code": "R06.02", "description": "Shortness of breath", "primary": False},
            {"code": "R50.9", "description": "Fever, unspecified", "primary": False}
        ],
        "clinical_notes": (
            "Patient presented with acute cough, fever, and progressive dyspnea. "
            "Vital signs indicate elevated respiratory rate and mild hypoxemia. "
            "Chest radiography scheduled at MEC edge imaging station. "
            "Strict HIPAA §164.312 privacy controls active on this on-premises clinical record."
        )
    }

    # -------------------------------------------------------------------------
    # 2. Three Failed / Error Datasets
    # -------------------------------------------------------------------------
    # Error 1: Corrupted Image File
    corrupt_image_bytes = create_corrupted_image_bytes()

    # Error 2: Incomplete Patient Record Missing Mandatory Fields
    incomplete_patient_json = {
        "encounter_type": "Emergency",
        "notes": "Patient triage begun but vital signs and patient_uuid are completely missing from record stream.",
        "expected_error": "ERR_MISSING_MANDATORY_FIELDS"
    }

    # Error 3: Unsupported / Schema Mismatch Format
    unsupported_format_bytes = b"<legacy_unsupported_protocol_v1>INVALID_XML_PAYLOAD_NON_COMPLIANT</legacy_unsupported_protocol_v1>"

    # -------------------------------------------------------------------------
    # 3. Three Loop / Timeout Datasets
    # -------------------------------------------------------------------------
    # Loop 1: Watchdog Execution Limit Exceeded
    loop_compute_json = {
        "task_id": "LOOP-COMPUTE-01",
        "description": "Compute-heavy task designed with recursive iteration exceeding maximum execution deadline.",
        "workload_type": "execution_time_limit",
        "cpu_cycles_giga": 5.0,
        "timeout_seconds": 2,
        "deadline_ms": 100,
        "expected_status": "TIMED_OUT",
        "loop_condition": "while(true){ cpu_stress_iteration(); }",
        "watchdog_protection": "Graceful cancellation triggered when execution runtime exceeds watchdog threshold."
    }

    # Loop 2: Simulated Worker Unresponsive / Dropped Heartbeat
    loop_worker_json = {
        "task_id": "LOOP-WORKER-02",
        "description": "Simulates worker node thread communication failure and dropped response heartbeat.",
        "workload_type": "worker_unresponsive",
        "timeout_seconds": 3,
        "expected_status": "TIMED_OUT",
        "heartbeat_interval_ms": 500,
        "simulated_action": "Worker enters unacknowledged sleep state; orphan detector reclaims lock."
    }

    # Loop 3: Retry Loop Exhaustion
    loop_retry_json = {
        "task_id": "LOOP-RETRY-03",
        "description": "Simulates transient network transmission failures triggering bounded exponential backoff.",
        "workload_type": "retry_exhaustion",
        "max_retries": 3,
        "current_attempt": 0,
        "expected_status": "FAILED",
        "backoff_multiplier": 1.5,
        "safety_guarantee": "Strict retry counter prevents infinite recursion; marks task FAILED after attempt 3."
    }

    # -------------------------------------------------------------------------
    # Package 1: COMPLETE SUITE (11 Datasets)
    # -------------------------------------------------------------------------
    complete_zip_path = output_dir / "complete_hospital_suite_11_datasets.zip"
    manifest_complete = build_manifest(
        scenario_id="complete_suite_11",
        package_name="Complete Hospital Multi-Tier Suite (11 Datasets)",
        description="Includes 5 success datasets for Local/MEC/Cloud, 3 failed datasets, and 3 loop/timeout datasets.",
        scenario_category="mixed",
        dataset_meta={
            "hospital_ehr_patient_vitals.csv": {"tier": "LOCAL_STORAGE", "policy": "LOCAL_ONLY", "privacy_policy": "LOCAL_ONLY", "category": "SUCCESS", "type": "Clinical Vitals", "source_device": "LOCAL-01"},
            "chest_xray_scan_radiology.png": {"tier": "MEC_STORAGE", "policy": "TRUSTED_EDGE", "privacy_policy": "TRUSTED_EDGE", "category": "SUCCESS", "type": "Radiological Scan", "source_device": "MEC-01"},
            "outpatient_appointments_schedule.json": {"tier": "CLOUD_STORAGE", "policy": "CLOUD_ALLOWED", "privacy_policy": "CLOUD_ALLOWED", "category": "SUCCESS", "type": "Scheduling Batch", "source_device": "CLOUD-01"},
            "laboratory_metabolic_panel.json": {"tier": "MEC_STORAGE", "policy": "TRUSTED_EDGE", "privacy_policy": "TRUSTED_EDGE", "category": "SUCCESS", "type": "Lab Report", "source_device": "MEC-01"},
            "clinical_encounter_document.json": {"tier": "LOCAL_STORAGE", "policy": "LOCAL_ONLY", "privacy_policy": "LOCAL_ONLY", "category": "SUCCESS", "type": "Physician Documentation", "source_device": "LOCAL-01"},
            "corrupted_medical_scan.png": {"category": "ERROR", "expected_status": "FAILED", "reason": "Corrupted Header", "privacy_policy": "TRUSTED_EDGE", "source_device": "MEC-01"},
            "incomplete_patient_record.json": {"category": "ERROR", "expected_status": "REJECTED", "reason": "Missing Fields", "privacy_policy": "LOCAL_ONLY", "source_device": "LOCAL-01"},
            "unsupported_legacy_format.dat": {"category": "ERROR", "expected_status": "REJECTED", "reason": "Invalid Schema", "privacy_policy": "LOCAL_ONLY", "source_device": "LOCAL-01"},
            "loop_workload_infinite_compute.json": {"category": "TIMEOUT", "expected_status": "TIMED_OUT", "reason": "Compute Exceeded", "privacy_policy": "TRUSTED_EDGE", "source_device": "MEC-01"},
            "loop_worker_unresponsive_heartbeat.json": {"category": "TIMEOUT", "expected_status": "TIMED_OUT", "reason": "Worker Dropped", "privacy_policy": "TRUSTED_EDGE", "source_device": "MEC-01"},
            "loop_retry_exhaustion_batch.json": {"category": "TIMEOUT", "expected_status": "FAILED", "reason": "Max Retries Reached", "privacy_policy": "CLOUD_ALLOWED", "source_device": "CLOUD-01"},
        },
        storage_architecture={
            "tier_1": "LOCAL_STORAGE (On-Premises High-Privacy Vault, 50 GB)",
            "tier_2": "MEC_STORAGE (Hospital Edge Compute Node, 200 GB)",
            "tier_3": "CLOUD_STORAGE (Central Cloud Synchronizer, 1000 GB)"
        },
    )

    with zipfile.ZipFile(complete_zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(manifest_complete, indent=2))
        z.writestr("hospital_ehr_patient_vitals.csv", vitals_csv_content)
        z.writestr("chest_xray_scan_radiology.png", xray_png_bytes)
        z.writestr("outpatient_appointments_schedule.json", json.dumps(appointments_json, indent=2))
        z.writestr("laboratory_metabolic_panel.json", json.dumps(lab_panel_json, indent=2))
        z.writestr("clinical_encounter_document.json", json.dumps(encounter_doc_json, indent=2))
        z.writestr("corrupted_medical_scan.png", corrupt_image_bytes)
        z.writestr("incomplete_patient_record.json", json.dumps(incomplete_patient_json, indent=2))
        z.writestr("unsupported_legacy_format.dat", unsupported_format_bytes)
        z.writestr("loop_workload_infinite_compute.json", json.dumps(loop_compute_json, indent=2))
        z.writestr("loop_worker_unresponsive_heartbeat.json", json.dumps(loop_worker_json, indent=2))
        z.writestr("loop_retry_exhaustion_batch.json", json.dumps(loop_retry_json, indent=2))

    print(f"Created: {complete_zip_path} ({os.path.getsize(complete_zip_path)} bytes)")

    # -------------------------------------------------------------------------
    # Package 2: SUCCESS BATCH (5 Datasets across 3 Storage Tiers)
    # -------------------------------------------------------------------------
    success_zip_path = output_dir / "success_5_datasets_tri_storage.zip"
    manifest_success = build_manifest(
        scenario_id="success_tri_storage_05",
        package_name="5 Success Datasets Across 3 Storage Systems",
        description="All 5 datasets succeed and allocate to Local (2), MEC (2), and Cloud (1).",
        dataset_meta={
            "hospital_ehr_patient_vitals.csv": {"tier": "LOCAL_STORAGE", "policy": "LOCAL_ONLY", "privacy_policy": "LOCAL_ONLY", "source_device": "LOCAL-01"},
            "chest_xray_scan_radiology.png": {"tier": "MEC_STORAGE", "policy": "TRUSTED_EDGE", "privacy_policy": "TRUSTED_EDGE", "source_device": "MEC-01"},
            "outpatient_appointments_schedule.json": {"tier": "CLOUD_STORAGE", "policy": "CLOUD_ALLOWED", "privacy_policy": "CLOUD_ALLOWED", "source_device": "CLOUD-01"},
            "laboratory_metabolic_panel.json": {"tier": "MEC_STORAGE", "policy": "TRUSTED_EDGE", "privacy_policy": "TRUSTED_EDGE", "source_device": "MEC-01"},
            "clinical_encounter_document.json": {"tier": "LOCAL_STORAGE", "policy": "LOCAL_ONLY", "privacy_policy": "LOCAL_ONLY", "source_device": "LOCAL-01"},
        },
    )
    with zipfile.ZipFile(success_zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(manifest_success, indent=2))
        z.writestr("hospital_ehr_patient_vitals.csv", vitals_csv_content)
        z.writestr("chest_xray_scan_radiology.png", xray_png_bytes)
        z.writestr("outpatient_appointments_schedule.json", json.dumps(appointments_json, indent=2))
        z.writestr("laboratory_metabolic_panel.json", json.dumps(lab_panel_json, indent=2))
        z.writestr("clinical_encounter_document.json", json.dumps(encounter_doc_json, indent=2))

    print(f"Created: {success_zip_path} ({os.path.getsize(success_zip_path)} bytes)")

    # -------------------------------------------------------------------------
    # Package 3: FAILED BATCH (3 Error Datasets)
    # -------------------------------------------------------------------------
    failed_zip_path = output_dir / "failed_3_datasets_error_batch.zip"
    manifest_failed = build_manifest(
        scenario_id="failed_error_batch_03",
        package_name="3 Failed / Error Hospital Workload Datasets",
        description="Contains corrupted image, missing fields, and unsupported schema mismatch.",
        scenario_category="failed",
        dataset_meta={
            "corrupted_medical_scan.png": {"expected_status": "FAILED", "code": "ERR_MALFORMED_HEADER", "privacy_policy": "TRUSTED_EDGE", "source_device": "MEC-01"},
            "incomplete_patient_record.json": {"expected_status": "REJECTED", "code": "ERR_MISSING_MANDATORY_FIELDS", "privacy_policy": "LOCAL_ONLY", "source_device": "LOCAL-01"},
            "unsupported_legacy_format.dat": {"expected_status": "REJECTED", "code": "ERR_UNSUPPORTED_FORMAT", "privacy_policy": "LOCAL_ONLY", "source_device": "LOCAL-01"},
        },
    )
    with zipfile.ZipFile(failed_zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(manifest_failed, indent=2))
        z.writestr("corrupted_medical_scan.png", corrupt_image_bytes)
        z.writestr("incomplete_patient_record.json", json.dumps(incomplete_patient_json, indent=2))
        z.writestr("unsupported_legacy_format.dat", unsupported_format_bytes)

    print(f"Created: {failed_zip_path} ({os.path.getsize(failed_zip_path)} bytes)")

    # -------------------------------------------------------------------------
    # Package 4: LOOP BATCH (3 Timeout / Retry Loop Datasets)
    # -------------------------------------------------------------------------
    loop_zip_path = output_dir / "loop_3_datasets_timeout_batch.zip"
    manifest_loop = build_manifest(
        scenario_id="loop_timeout_batch_03",
        package_name="3 Looping / Timeout Hospital Workload Datasets",
        description="Contains infinite compute watchdog loop, unresponsive worker node, and retry exhaustion loop.",
        scenario_category="loop",
        dataset_meta={
            "loop_workload_infinite_compute.json": {"expected_status": "TIMED_OUT", "trigger": "Watchdog Timeout", "privacy_policy": "TRUSTED_EDGE", "source_device": "MEC-01"},
            "loop_worker_unresponsive_heartbeat.json": {"expected_status": "TIMED_OUT", "trigger": "Dropped Node", "privacy_policy": "TRUSTED_EDGE", "source_device": "MEC-01"},
            "loop_retry_exhaustion_batch.json": {"expected_status": "FAILED", "trigger": "Max Retries Reached", "privacy_policy": "CLOUD_ALLOWED", "source_device": "CLOUD-01"},
        },
    )
    with zipfile.ZipFile(loop_zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(manifest_loop, indent=2))
        z.writestr("loop_workload_infinite_compute.json", json.dumps(loop_compute_json, indent=2))
        z.writestr("loop_worker_unresponsive_heartbeat.json", json.dumps(loop_worker_json, indent=2))
        z.writestr("loop_retry_exhaustion_batch.json", json.dumps(loop_retry_json, indent=2))

    print(f"Created: {loop_zip_path} ({os.path.getsize(loop_zip_path)} bytes)")


if __name__ == "__main__":
    generate_packages()
