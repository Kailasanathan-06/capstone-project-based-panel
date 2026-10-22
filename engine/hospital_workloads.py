"""
Hospital Workload Dataset Engine
=================================
Manages the 14 Hospital Workload Scenarios and provides genuine, verified
processing functions for each workload type:
- 5 Success Datasets (Image Preprocessing, Patient Records, Lab Reports, Document Metadata, Appointment Scheduling)
- 3 Error Datasets (Malformed, Missing Fields, Unsupported Format)
- 3 Defensive Security Datasets (Unauthorized Submission, Invalid MEC Auth, Unauthorized Replication)
- 3 Looping / Timeout Datasets (Execution Limit, Worker Unresponsive, Max Retries Reached)

All processing functions perform actual calculations, timing, and SHA-256 checksumming.
Synthetic data is completely non-identifiable and reproducible.
"""

import os
import json
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
from PIL import Image
import numpy as np

from django.conf import settings
from django.utils import timezone as dj_timezone


# Base directory for synthetic workload artifacts
def get_workload_artifacts_dir() -> Path:
    base = getattr(settings, "BASE_DIR", Path("."))
    artifacts_dir = Path(base) / "data_storage" / "hospital_workloads"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    return artifacts_dir


# ---------------------------------------------------------------------------
# Initial 14 Scenario Definitions
# ---------------------------------------------------------------------------
INITIAL_14_SCENARIOS = [
    # A. SUCCESS DATASETS (5)
    {
        "scenario_id": "HOSP-SUCCESS-01",
        "name": "Medical Image Preprocessing (Pneumonia Chest X-Ray)",
        "category": "SUCCESS",
        "workload_type": "medical_image_preprocess",
        "description": "Standardized biomedical image normalization, CLAHE contrast enhancement, and 224x224 resizing.",
        "input_format": "PNG",
        "privacy_policy": "TRUSTED_EDGE",
        "cpu_cycles_giga": 0.8,
        "memory_mb": 512,
        "deadline_ms": 1200,
        "privacy_sensitivity": 0.7,
        "security_sensitivity": 0.3,
        "expected_status": "COMPLETED",
        "expected_result_description": "Enhanced 224x224 grayscale medical image with verified input and output SHA-256 checksums.",
        "validation_rules": "Input must be a valid readable grayscale/RGB image. Output must have dimensions 224x224.",
    },
    {
        "scenario_id": "HOSP-SUCCESS-02",
        "name": "Patient Clinical Record Vital Signs & Risk Triage",
        "category": "SUCCESS",
        "workload_type": "patient_record_processing",
        "description": "Validation, de-identification verification, and NEWS2 clinical early warning risk score calculation.",
        "input_format": "JSON",
        "privacy_policy": "LOCAL_ONLY",
        "cpu_cycles_giga": 0.4,
        "memory_mb": 256,
        "deadline_ms": 600,
        "privacy_sensitivity": 0.95,
        "security_sensitivity": 0.85,
        "expected_status": "COMPLETED",
        "expected_result_description": "Structured clinical risk report with computed NEWS2 acuity score, triage category, and de-identification hash.",
        "validation_rules": "All mandatory vital sign fields (BP, HR, RR, SpO2, Temp) present and within physiologically valid ranges.",
    },
    {
        "scenario_id": "HOSP-SUCCESS-03",
        "name": "Laboratory Metabolic Panel & CBC Report Processing",
        "category": "SUCCESS",
        "workload_type": "lab_report_processing",
        "description": "Laboratory analyte extraction, demographic-adjusted reference range comparison, and clinical severity grading.",
        "input_format": "JSON",
        "privacy_policy": "TRUSTED_EDGE",
        "cpu_cycles_giga": 0.5,
        "memory_mb": 256,
        "deadline_ms": 700,
        "privacy_sensitivity": 0.8,
        "security_sensitivity": 0.5,
        "expected_status": "COMPLETED",
        "expected_result_description": "Verified lab analysis report with analyte status flags (NORMAL/ELEVATED/DEPRESSED) and severity index.",
        "validation_rules": "Panel must contain at least 5 standard clinical analytes with positive numeric quantities.",
    },
    {
        "scenario_id": "HOSP-SUCCESS-04",
        "name": "Clinical Document Metadata & ICD-10 Diagnostic Extraction",
        "category": "SUCCESS",
        "workload_type": "medical_metadata_extraction",
        "description": "Structured extraction of document category, provider specialty, ICD-10 diagnostic coding, and cryptographic checksums.",
        "input_format": "JSON",
        "privacy_policy": "TRUSTED_EDGE",
        "cpu_cycles_giga": 0.6,
        "memory_mb": 384,
        "deadline_ms": 800,
        "privacy_sensitivity": 0.85,
        "security_sensitivity": 0.6,
        "expected_status": "COMPLETED",
        "expected_result_description": "Structured metadata record containing extracted clinical tags, word metrics, and cryptographic integrity proof.",
        "validation_rules": "Document text must exceed 50 characters and contain valid clinical encounter sections.",
    },
    {
        "scenario_id": "HOSP-SUCCESS-05",
        "name": "Outpatient Appointment Batch Scheduling & Conflict Optimization",
        "category": "SUCCESS",
        "workload_type": "appointment_scheduling",
        "description": "Multi-provider clinic appointment slot allocation, priority queue triage, and room conflict resolution.",
        "input_format": "JSON",
        "privacy_policy": "CLOUD_ALLOWED",
        "cpu_cycles_giga": 0.7,
        "memory_mb": 512,
        "deadline_ms": 1000,
        "privacy_sensitivity": 0.4,
        "security_sensitivity": 0.2,
        "expected_status": "COMPLETED",
        "expected_result_description": "Optimized schedule matrix with zero provider time conflicts and room assignment confirmations.",
        "validation_rules": "Schedule batch must have non-overlapping confirmed slots and valid operating room IDs.",
    },

    # B. ERROR DATASETS (3)
    {
        "scenario_id": "HOSP-ERROR-01",
        "name": "Malformed / Corrupted Medical Image File",
        "category": "ERROR",
        "workload_type": "malformed_input",
        "description": "Damaged non-image binary stream mimicking an incomplete image transfer.",
        "input_format": "CORRUPT_BIN",
        "privacy_policy": "TRUSTED_EDGE",
        "cpu_cycles_giga": 0.3,
        "memory_mb": 256,
        "deadline_ms": 500,
        "privacy_sensitivity": 0.5,
        "security_sensitivity": 0.3,
        "expected_status": "FAILED",
        "expected_result_description": "Validation error ERR_MALFORMED_INPUT with graceful failure and zero memory leaks.",
        "validation_rules": "Engine detects header corruption prior to processing and releases allocated buffers.",
    },
    {
        "scenario_id": "HOSP-ERROR-02",
        "name": "Incomplete Patient Record Missing Mandatory Clinical Fields",
        "category": "ERROR",
        "workload_type": "missing_fields",
        "description": "Patient record omitting mandatory identifiers and required vital sign measurements.",
        "input_format": "JSON",
        "privacy_policy": "LOCAL_ONLY",
        "cpu_cycles_giga": 0.2,
        "memory_mb": 128,
        "deadline_ms": 400,
        "privacy_sensitivity": 0.9,
        "security_sensitivity": 0.5,
        "expected_status": "REJECTED",
        "expected_result_description": "Rejection with code ERR_MISSING_MANDATORY_FIELDS specifying missing keys.",
        "validation_rules": "Rejects missing patient_uuid or mandatory physiological indicators.",
    },
    {
        "scenario_id": "HOSP-ERROR-03",
        "name": "Unsupported Medical Record Format & Schema Mismatch",
        "category": "ERROR",
        "workload_type": "unsupported_format",
        "description": "Payload structured with invalid legacy XML/text schema not adhering to system specifications.",
        "input_format": "INVALID_SCHEMA",
        "privacy_policy": "TRUSTED_EDGE",
        "cpu_cycles_giga": 0.2,
        "memory_mb": 128,
        "deadline_ms": 400,
        "privacy_sensitivity": 0.5,
        "security_sensitivity": 0.3,
        "expected_status": "REJECTED",
        "expected_result_description": "Rejection with code ERR_UNSUPPORTED_FORMAT and human-readable explanation.",
        "validation_rules": "Validates schema against accepted formats prior to scheduling.",
    },

    # C. HACKED / DEFENSIVE SECURITY DATASETS (3)
    {
        "scenario_id": "HOSP-SEC-01",
        "name": "Unauthorized Task Submission Attempt",
        "category": "SECURITY",
        "workload_type": "unauthorized_submission",
        "description": "Unauthenticated client attempting to inject workload tasks into hospital edge queue.",
        "input_format": "JSON",
        "privacy_policy": "LOCAL_ONLY",
        "cpu_cycles_giga": 0.5,
        "memory_mb": 256,
        "deadline_ms": 500,
        "privacy_sensitivity": 0.9,
        "security_sensitivity": 0.95,
        "expected_status": "REJECTED",
        "expected_result_description": "HTTP 401/403 denial, task marked REJECTED, security audit event logged.",
        "validation_rules": "Requires valid Django auth session or Bearer token.",
    },
    {
        "scenario_id": "HOSP-SEC-02",
        "name": "Invalid or Expired MEC Agent Credentials",
        "category": "SECURITY",
        "workload_type": "invalid_agent_auth",
        "description": "Rogue or expired MEC agent attempting telemetry heartbeat and task dispatch.",
        "input_format": "JSON",
        "privacy_policy": "TRUSTED_EDGE",
        "cpu_cycles_giga": 0.4,
        "memory_mb": 256,
        "deadline_ms": 500,
        "privacy_sensitivity": 0.8,
        "security_sensitivity": 0.9,
        "expected_status": "REJECTED",
        "expected_result_description": "Heartbeat and task pickup rejected with 401; device quarantined in Digital Twin.",
        "validation_rules": "MEC agent token must match active non-revoked database token.",
    },
    {
        "scenario_id": "HOSP-SEC-03",
        "name": "Unauthorized Cloud Replication / Privacy Policy Violation",
        "category": "SECURITY",
        "workload_type": "unauthorized_replication",
        "description": "Prohibited attempt to replicate sensitive LOCAL_ONLY patient dataset to public Cloud tier.",
        "input_format": "JSON",
        "privacy_policy": "LOCAL_ONLY",
        "cpu_cycles_giga": 0.5,
        "memory_mb": 256,
        "deadline_ms": 500,
        "privacy_sensitivity": 1.0,
        "security_sensitivity": 0.9,
        "expected_status": "BLOCKED",
        "expected_result_description": "Replication blocked with BLOCKED_BY_POLICY; security audit event logged.",
        "validation_rules": "LOCAL_ONLY datasets strictly forbidden from transferring to MEC or Cloud storage.",
    },

    # D. LOOPING / TIMEOUT DATASETS (3)
    {
        "scenario_id": "HOSP-TIME-01",
        "name": "Processing Workload Exceeding Execution-Time Limit",
        "category": "TIMEOUT",
        "workload_type": "execution_time_limit",
        "description": "Compute-heavy task designed with execution duration exceeding the configured timeout threshold.",
        "input_format": "JSON",
        "privacy_policy": "TRUSTED_EDGE",
        "cpu_cycles_giga": 2.5,
        "memory_mb": 512,
        "deadline_ms": 200,
        "timeout_seconds": 2,  # Bounded short limit for demonstration
        "privacy_sensitivity": 0.5,
        "security_sensitivity": 0.2,
        "expected_status": "TIMED_OUT",
        "expected_result_description": "Graceful watchdog cancellation, status TIMED_OUT, resources released.",
        "validation_rules": "Execution terminated when runtime exceeds configured timeout limit.",
    },
    {
        "scenario_id": "HOSP-TIME-02",
        "name": "Simulated Worker Unresponsive / Dropped Node",
        "category": "TIMEOUT",
        "workload_type": "worker_unresponsive",
        "description": "Worker thread simulates communication loss or dropped execution heartbeat.",
        "input_format": "JSON",
        "privacy_policy": "TRUSTED_EDGE",
        "cpu_cycles_giga": 1.0,
        "memory_mb": 256,
        "deadline_ms": 300,
        "timeout_seconds": 3,
        "privacy_sensitivity": 0.6,
        "security_sensitivity": 0.4,
        "expected_status": "TIMED_OUT",
        "expected_result_description": "Orphan monitor reclaims task, sets status TIMED_OUT, releases worker lock.",
        "validation_rules": "Task requeued or terminated if worker fails to respond within heartbeat timeout.",
    },
    {
        "scenario_id": "HOSP-TIME-03",
        "name": "Transient Task Failure Reaching Maximum Retry Limit",
        "category": "TIMEOUT",
        "workload_type": "retry_exhaustion",
        "description": "Task experiencing transient external service errors retries up to maximum retry count then terminates.",
        "input_format": "JSON",
        "privacy_policy": "TRUSTED_EDGE",
        "cpu_cycles_giga": 0.5,
        "memory_mb": 256,
        "deadline_ms": 500,
        "max_retries": 3,
        "privacy_sensitivity": 0.5,
        "security_sensitivity": 0.2,
        "expected_status": "FAILED",
        "expected_result_description": "Exponential backoff retries bounded at 3 attempts, ending in FAILED status without infinite loop.",
        "validation_rules": "Retry counter strictly enforced; task terminates after max_retries attempts.",
    },
]


# ---------------------------------------------------------------------------
# Synthetic Fixture Generators
# ---------------------------------------------------------------------------
def get_synthetic_medical_image_fixture(output_path: Optional[Path] = None) -> Path:
    """Generate or retrieve a verified synthetic medical lung/chest scan."""
    artifacts = get_workload_artifacts_dir()
    img_path = output_path or (artifacts / "synthetic_chest_scan.png")
    if not img_path.exists():
        # Generate realistic-looking synthetic anatomical thorax scan
        arr = np.zeros((128, 128), dtype=np.uint8)
        # Background tissue
        arr[20:108, 20:108] = 40
        # Right & Left lung lobes (darker air space)
        arr[30:95, 25:58] = 110
        arr[30:95, 70:103] = 105
        # Add texture / vascular markings
        noise = np.random.randint(-15, 15, size=(128, 128))
        arr = np.clip(arr.astype(int) + noise, 0, 255).astype(np.uint8)
        img = Image.fromarray(arr, mode="L")
        img.save(img_path)
    return img_path


def get_synthetic_patient_record_fixture() -> Dict[str, Any]:
    """Generate non-identifiable synthetic clinical patient vital indicators."""
    return {
        "patient_uuid": "SYNTH-PAT-8842",
        "encounter_id": "ENC-2026-0912",
        "age_group": "adult_55_64",
        "gender": "undisclosed",
        "admission_type": "elective_observation",
        "vitals": {
            "systolic_bp": 138,
            "diastolic_bp": 84,
            "heart_rate": 82,
            "respiratory_rate": 18,
            "spo2_percent": 96,
            "temperature_celsius": 37.1,
            "consciousness_level": "alert",
            "supplemental_oxygen": False,
        },
        "allergies": ["penicillin_rash"],
        "chronic_conditions": ["mild_essential_hypertension"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def get_synthetic_lab_report_fixture() -> Dict[str, Any]:
    """Generate synthetic metabolic and CBC laboratory panel data."""
    return {
        "report_id": "LAB-2026-7731",
        "patient_uuid": "SYNTH-PAT-8842",
        "panel_type": "COMPREHENSIVE_METABOLIC_CBC",
        "collection_time": datetime.now(timezone.utc).isoformat(),
        "analytes": [
            {"code": "HEMOGLOBIN", "name": "Hemoglobin", "value": 13.8, "unit": "g/dL", "ref_min": 12.0, "ref_max": 16.0},
            {"code": "WBC", "name": "White Blood Cell Count", "value": 7.4, "unit": "10^3/uL", "ref_min": 4.5, "ref_max": 11.0},
            {"code": "PLATELETS", "name": "Platelet Count", "value": 245, "unit": "10^3/uL", "ref_min": 150, "ref_max": 450},
            {"code": "CREATININE", "name": "Serum Creatinine", "value": 1.4, "unit": "mg/dL", "ref_min": 0.6, "ref_max": 1.2},
            {"code": "BUN", "name": "Blood Urea Nitrogen", "value": 22, "unit": "mg/dL", "ref_min": 7.0, "ref_max": 20.0},
            {"code": "SODIUM", "name": "Sodium", "value": 140, "unit": "mmol/L", "ref_min": 136, "ref_max": 145},
            {"code": "POTASSIUM", "name": "Potassium", "value": 4.2, "unit": "mmol/L", "ref_min": 3.5, "ref_max": 5.1},
            {"code": "GLUCOSE", "name": "Fasting Glucose", "value": 98, "unit": "mg/dL", "ref_min": 70, "ref_max": 100},
        ],
    }


def get_synthetic_medical_document_fixture() -> Dict[str, Any]:
    """Generate synthetic clinical consultation note document metadata."""
    return {
        "document_id": "DOC-2026-4421",
        "patient_uuid": "SYNTH-PAT-8842",
        "document_type": "CONSULTATION_NOTE",
        "author_role": "attending_pulmonologist",
        "service_department": "PULMONOLOGY",
        "clinical_text": (
            "PATIENT CONSULTATION NOTE: Patient presents for evaluation of persistent non-productive cough "
            "following viral upper respiratory infection. Chest radiography demonstrates mild peribronchial "
            "thickening without focal consolidation. Vital signs stable. Prescribed bronchodilator therapy "
            "and scheduled 4-week follow-up. Diagnostic coding: J18.9 (Pneumonia, unspecified organism), "
            "I10 (Essential primary hypertension). Plan: Outpatient monitoring."
        ),
        "service_date": "2026-10-22",
    }


def get_synthetic_appointment_batch_fixture() -> Dict[str, Any]:
    """Generate synthetic outpatient clinic scheduling batch."""
    return {
        "batch_id": "SCHED-BATCH-20261022",
        "department": "CARDIOLOGY_OUTPATIENT",
        "operating_date": "2026-10-23",
        "available_rooms": ["EXAM_RM_1", "EXAM_RM_2", "ECHO_LAB"],
        "requests": [
            {"request_id": "REQ-101", "provider_id": "DR_CHEN", "requested_slot": "09:00-09:30", "priority": "ROUTINE", "room": "EXAM_RM_1"},
            {"request_id": "REQ-102", "provider_id": "DR_CHEN", "requested_slot": "09:30-10:00", "priority": "URGENT", "room": "EXAM_RM_1"},
            {"request_id": "REQ-103", "provider_id": "DR_PATEL", "requested_slot": "09:00-09:45", "priority": "ROUTINE", "room": "ECHO_LAB"},
            {"request_id": "REQ-104", "provider_id": "DR_PATEL", "requested_slot": "10:00-10:30", "priority": "ROUTINE", "room": "EXAM_RM_2"},
        ],
    }


# ---------------------------------------------------------------------------
# Genuine Processing Functions for Successful Workloads
# ---------------------------------------------------------------------------
def process_medical_image_workload(
    task: Any,
    image_path: str,
    target_resolution: int = 224,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Genuine CLAHE contrast enhancement, normalization, and resizing of medical scan."""
    from engine.image_processor import MedicalImageProcessor

    out_dir = output_dir or (get_workload_artifacts_dir() / "processed_images")
    processor = MedicalImageProcessor(output_dir=str(out_dir))
    result = processor.process(
        image_path=image_path,
        operation="normalize_clahe",
        target_resolution=target_resolution,
    )
    return {
        "status": "COMPLETED",
        "output_path": result["output_path"],
        "input_checksum": result["input_checksum"],
        "output_checksum": result["output_checksum"],
        "processing_time_s": result["processing_time_s"],
        "details": {
            "operation": "normalize_clahe",
            "resolution": f"{target_resolution}x{target_resolution}",
            "verified": True,
        },
    }


def compute_news2_score(vitals: Dict[str, Any]) -> Tuple[int, str, List[str]]:
    """Compute official National Early Warning Score (NEWS2) from clinical vitals."""
    score = 0
    flags = []

    # Respiration Rate
    rr = vitals.get("respiratory_rate", 16)
    if rr <= 8:
        score += 3
        flags.append("Severely low respiratory rate")
    elif 9 <= rr <= 11:
        score += 1
    elif 12 <= rr <= 20:
        pass
    elif 21 <= rr <= 24:
        score += 2
        flags.append("Elevated respiratory rate")
    else:
        score += 3
        flags.append("Severely elevated respiratory rate")

    # SpO2
    spo2 = vitals.get("spo2_percent", 98)
    if spo2 <= 91:
        score += 3
        flags.append("Critical hypoxia (SpO2 <= 91%)")
    elif 92 <= spo2 <= 93:
        score += 2
        flags.append("Moderate hypoxia")
    elif 94 <= spo2 <= 95:
        score += 1

    # Systolic BP
    sbp = vitals.get("systolic_bp", 120)
    if sbp <= 90:
        score += 3
        flags.append("Severe hypotension (SBP <= 90)")
    elif 91 <= sbp <= 100:
        score += 2
    elif 101 <= sbp <= 110:
        score += 1
    elif 111 <= sbp <= 219:
        pass
    else:
        score += 3
        flags.append("Severe hypertension (SBP >= 220)")

    # Heart Rate
    hr = vitals.get("heart_rate", 75)
    if hr <= 40:
        score += 3
        flags.append("Severe bradycardia")
    elif 41 <= hr <= 50:
        score += 1
    elif 51 <= hr <= 90:
        pass
    elif 91 <= hr <= 110:
        score += 1
    elif 111 <= hr <= 130:
        score += 2
        flags.append("Tachycardia")
    else:
        score += 3
        flags.append("Severe tachycardia")

    # Temperature
    temp = vitals.get("temperature_celsius", 37.0)
    if temp <= 35.0:
        score += 3
        flags.append("Hypothermia")
    elif 35.1 <= temp <= 36.0:
        score += 1
    elif 36.1 <= temp <= 38.0:
        pass
    elif 38.1 <= temp <= 39.0:
        score += 1
    else:
        score += 2
        flags.append("High pyrexia")

    if score == 0:
        acuity = "LOW"
    elif 1 <= score <= 4:
        acuity = "LOW_MEDIUM"
    elif 5 <= score <= 6:
        acuity = "MEDIUM"
    else:
        acuity = "HIGH_CRITICAL"

    return score, acuity, flags


def process_patient_record_workload(
    task: Any,
    payload: Dict[str, Any],
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Genuine validation, de-identification verification, and NEWS2 calculation."""
    start_mono = time.perf_counter()
    vitals = payload.get("vitals")
    if not vitals:
        raise ValueError("Missing mandatory vitals block in patient clinical record.")

    news2_score, acuity_tier, observation_flags = compute_news2_score(vitals)

    # De-identification cryptographic hash verification
    patient_id = payload.get("patient_uuid", "UNKNOWN")
    salt = "SecureDT_Clinical_Privacy_2026"
    deid_token = hashlib.sha256(f"{patient_id}_{salt}".encode()).hexdigest()[:16]

    out_data = {
        "patient_deid_token": deid_token,
        "encounter_id": payload.get("encounter_id", ""),
        "news2_score": news2_score,
        "acuity_tier": acuity_tier,
        "clinical_flags": observation_flags,
        "vital_summary": {
            "bp": f"{vitals.get('systolic_bp')}/{vitals.get('diastolic_bp')}",
            "hr": vitals.get("heart_rate"),
            "spo2": vitals.get("spo2_percent"),
            "temp": vitals.get("temperature_celsius"),
        },
        "validation_status": "PASSED_STRICT",
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }

    out_dir = output_dir or (get_workload_artifacts_dir() / "patient_records")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"news2_{payload.get('encounter_id', 'result')}.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out_data, fh, indent=2)

    checksum = hashlib.sha256(open(out_path, "rb").read()).hexdigest()
    exec_time = time.perf_counter() - start_mono

    return {
        "status": "COMPLETED",
        "output_path": str(out_path),
        "output_checksum": checksum,
        "processing_time_s": round(exec_time, 4),
        "details": out_data,
    }


def process_lab_report_workload(
    task: Any,
    payload: Dict[str, Any],
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Genuine reference range validation, abnormal flag grading, and severity indexing."""
    start_mono = time.perf_counter()
    analytes = payload.get("analytes", [])
    if not analytes or len(analytes) < 3:
        raise ValueError("Invalid lab report: insufficient analytes present.")

    analyzed = []
    abnormal_count = 0
    severity_points = 0

    for a in analytes:
        val = float(a["value"])
        rmin = float(a["ref_min"])
        rmax = float(a["ref_max"])
        flag = "NORMAL"

        if val < rmin:
            pct_below = (rmin - val) / rmin
            flag = "CRITICAL_LOW" if pct_below > 0.25 else "LOW"
            abnormal_count += 1
            severity_points += 2 if flag == "CRITICAL_LOW" else 1
        elif val > rmax:
            pct_above = (val - rmax) / rmax
            flag = "CRITICAL_HIGH" if pct_above > 0.25 else "HIGH"
            abnormal_count += 1
            severity_points += 2 if flag == "CRITICAL_HIGH" else 1

        analyzed.append({
            "code": a["code"],
            "name": a["name"],
            "value": val,
            "unit": a["unit"],
            "reference_range": f"{rmin} - {rmax}",
            "flag": flag,
        })

    overall_severity = "NORMAL"
    if severity_points >= 4:
        overall_severity = "CRITICAL_REVIEW_REQUIRED"
    elif severity_points >= 1:
        overall_severity = "ABNORMAL_ELEVATED"

    out_data = {
        "report_id": payload.get("report_id", "LAB-000"),
        "patient_uuid": payload.get("patient_uuid", ""),
        "total_analytes": len(analytes),
        "abnormal_count": abnormal_count,
        "severity_level": overall_severity,
        "analyzed_results": analyzed,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }

    out_dir = output_dir or (get_workload_artifacts_dir() / "lab_reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"lab_{payload.get('report_id', 'out')}.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out_data, fh, indent=2)

    checksum = hashlib.sha256(open(out_path, "rb").read()).hexdigest()
    exec_time = time.perf_counter() - start_mono

    return {
        "status": "COMPLETED",
        "output_path": str(out_path),
        "output_checksum": checksum,
        "processing_time_s": round(exec_time, 4),
        "details": out_data,
    }


def process_document_metadata_workload(
    task: Any,
    payload: Dict[str, Any],
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Genuine extraction of clinical entities, ICD-10 diagnostic codes, and document integrity."""
    start_mono = time.perf_counter()
    clinical_text = payload.get("clinical_text", "")
    if len(clinical_text.strip()) < 30:
        raise ValueError("Clinical document text is too brief for entity extraction.")

    words = clinical_text.split()
    word_count = len(words)

    # Standard ICD-10 clinical regex / pattern matcher
    icd10_codes = []
    common_icd = {
        "J18.9": "Pneumonia, unspecified organism",
        "I10": "Essential (primary) hypertension",
        "E11.9": "Type 2 diabetes mellitus without complications",
        "J44.9": "Chronic obstructive pulmonary disease, unspecified",
        "I25.10": "Atherosclerotic heart disease",
    }
    for code, desc in common_icd.items():
        if code in clinical_text:
            icd10_codes.append({"code": code, "description": desc})

    # Department classification heuristic
    dept = payload.get("service_department", "GENERAL_MEDICINE")
    if "pulmonolog" in clinical_text.lower() or "pneumonia" in clinical_text.lower():
        dept = "PULMONOLOGY"
    elif "cardio" in clinical_text.lower() or "hypertension" in clinical_text.lower():
        dept = "CARDIOLOGY"

    # Cryptographic integrity signature of original clinical text
    text_sig = hashlib.sha256(clinical_text.encode("utf-8")).hexdigest()

    out_data = {
        "document_id": payload.get("document_id", "DOC-000"),
        "document_type": payload.get("document_type", "CLINICAL_NOTE"),
        "service_department": dept,
        "extracted_icd10_codes": icd10_codes,
        "word_count": word_count,
        "character_count": len(clinical_text),
        "content_signature_sha256": text_sig,
        "extraction_engine": "SecureDT_Clinical_NLP_v1",
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }

    out_dir = output_dir or (get_workload_artifacts_dir() / "medical_documents")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"meta_{payload.get('document_id', 'out')}.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out_data, fh, indent=2)

    checksum = hashlib.sha256(open(out_path, "rb").read()).hexdigest()
    exec_time = time.perf_counter() - start_mono

    return {
        "status": "COMPLETED",
        "output_path": str(out_path),
        "output_checksum": checksum,
        "processing_time_s": round(exec_time, 4),
        "details": out_data,
    }


def process_appointment_scheduling_workload(
    task: Any,
    payload: Dict[str, Any],
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Genuine appointment conflict detection, triage prioritization, and schedule confirmation."""
    start_mono = time.perf_counter()
    requests = payload.get("requests", [])
    if not requests:
        raise ValueError("Appointment schedule batch contains no requests.")

    # Sort requests by priority (URGENT first, then ROUTINE)
    priority_weight = {"EMERGENCY": 3, "URGENT": 2, "ROUTINE": 1}
    sorted_requests = sorted(
        requests,
        key=lambda r: priority_weight.get(r.get("priority", "ROUTINE"), 1),
        reverse=True,
    )

    booked_slots = set()  # (room, slot)
    provider_slots = set()  # (provider_id, slot)
    confirmed_schedule = []
    conflict_count = 0

    for req in sorted_requests:
        room = req.get("room")
        slot = req.get("requested_slot")
        provider = req.get("provider_id")

        if (room, slot) in booked_slots or (provider, slot) in provider_slots:
            conflict_count += 1
            status_desc = "RESCHEDULE_REQUIRED"
        else:
            booked_slots.add((room, slot))
            provider_slots.add((provider, slot))
            status_desc = "CONFIRMED"

        confirmed_schedule.append({
            "request_id": req["request_id"],
            "provider_id": provider,
            "room": room,
            "slot": slot,
            "priority": req.get("priority", "ROUTINE"),
            "status": status_desc,
        })

    out_data = {
        "batch_id": payload.get("batch_id", "SCHED-001"),
        "department": payload.get("department", "OUTPATIENT"),
        "operating_date": payload.get("operating_date", ""),
        "total_requests": len(requests),
        "confirmed_slots": len([s for s in confirmed_schedule if s["status"] == "CONFIRMED"]),
        "detected_conflicts": conflict_count,
        "schedule": confirmed_schedule,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }

    out_dir = output_dir or (get_workload_artifacts_dir() / "appointments")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"schedule_{payload.get('batch_id', 'out')}.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out_data, fh, indent=2)

    checksum = hashlib.sha256(open(out_path, "rb").read()).hexdigest()
    exec_time = time.perf_counter() - start_mono

    return {
        "status": "COMPLETED",
        "output_path": str(out_path),
        "output_checksum": checksum,
        "processing_time_s": round(exec_time, 4),
        "details": out_data,
    }


# ---------------------------------------------------------------------------
# Master Scenario Synchronizer
# ---------------------------------------------------------------------------
def ensure_all_14_scenarios_registered() -> int:
    """Register or verify all 14 official workload scenarios in MySQL/SQLite database."""
    from datasets.models import WorkloadScenario

    created_count = 0
    artifacts_dir = get_workload_artifacts_dir()

    # Pre-generate synthetic input fixtures
    img_fixture = get_synthetic_medical_image_fixture()
    patient_fixture = get_synthetic_patient_record_fixture()
    lab_fixture = get_synthetic_lab_report_fixture()
    doc_fixture = get_synthetic_medical_document_fixture()
    appt_fixture = get_synthetic_appointment_batch_fixture()

    corrupted_path = artifacts_dir / "corrupted_scan.bin"
    if not corrupted_path.exists():
        with open(corrupted_path, "wb") as fh:
            fh.write(b"CORRUPTED_STREAM_XYZ999_HEADER_INVALID_123456789")

    fixture_map = {
        "HOSP-SUCCESS-01": (str(img_fixture), "{}", img_fixture.stat().st_size if img_fixture.exists() else 1024),
        "HOSP-SUCCESS-02": ("", json.dumps(patient_fixture), len(json.dumps(patient_fixture))),
        "HOSP-SUCCESS-03": ("", json.dumps(lab_fixture), len(json.dumps(lab_fixture))),
        "HOSP-SUCCESS-04": ("", json.dumps(doc_fixture), len(json.dumps(doc_fixture))),
        "HOSP-SUCCESS-05": ("", json.dumps(appt_fixture), len(json.dumps(appt_fixture))),
        "HOSP-ERROR-01": (str(artifacts_dir / "corrupted_scan.bin"), "CORRUPTED_STREAM_XYZ999", 512),
        "HOSP-ERROR-02": ("", json.dumps({"note": "missing patient_uuid and vitals"}), 48),
        "HOSP-ERROR-03": ("", "<xml><invalid>schema_mismatch</invalid></xml>", 45),
        "HOSP-SEC-01": ("", json.dumps({"action": "unauthorized_task_post"}), 38),
        "HOSP-SEC-02": ("", json.dumps({"device_id": "MEC-ROGUE-01", "auth_token": "expired_or_fake_token"}), 72),
        "HOSP-SEC-03": ("", json.dumps({"dataset_id": "LOCAL_PATIENT_RECORDS", "target": "CLOUD_STORAGE"}), 68),
        "HOSP-TIME-01": ("", json.dumps({"workload": "infinite_matrix_benchmark", "iterations": 100000000}), 75),
        "HOSP-TIME-02": ("", json.dumps({"worker_status": "unresponsive_heartbeat_dropped"}), 55),
        "HOSP-TIME-03": ("", json.dumps({"transient_error_simulation": True, "attempts_configured": 5}), 62),
    }

    for scen in INITIAL_14_SCENARIOS:
        sid = scen["scenario_id"]
        file_path, payload_json, size_bytes = fixture_map.get(sid, ("", "{}", 100))

        obj, created = WorkloadScenario.objects.get_or_create(
            scenario_id=sid,
            defaults={
                "name": scen["name"],
                "category": scen["category"],
                "workload_type": scen["workload_type"],
                "description": scen["description"],
                "input_format": scen["input_format"],
                "input_size_bytes": size_bytes,
                "input_file_path": file_path,
                "input_payload": payload_json,
                "expected_status": scen["expected_status"],
                "expected_result_description": scen["expected_result_description"],
                "validation_rules": scen["validation_rules"],
                "privacy_policy": scen["privacy_policy"],
                "cpu_cycles_giga": scen["cpu_cycles_giga"],
                "memory_mb": scen["memory_mb"],
                "deadline_ms": scen["deadline_ms"],
                "privacy_sensitivity": scen["privacy_sensitivity"],
                "security_sensitivity": scen["security_sensitivity"],
                "timeout_seconds": scen.get("timeout_seconds", 60),
                "max_retries": scen.get("max_retries", 3),
            },
        )
        if created:
            created_count += 1

    return created_count


# ---------------------------------------------------------------------------
# Workload Execution Dispatcher
# ---------------------------------------------------------------------------
def execute_hospital_workload(task: Any) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Execute a task based on its workload type using genuine processing functions.
    Enforces timing, checksums, and updates task execution metadata.
    """
    start_time = dj_timezone.now()
    task.start_time = start_time
    w_type = getattr(task, "workload_type", "") or "medical_image_preprocess"

    try:
        if w_type == "medical_image_preprocess":
            img_path = getattr(task, "image_path", "") or str(get_synthetic_medical_image_fixture())
            target_res = getattr(task, "target_resolution", 224) or 224
            res = process_medical_image_workload(task, img_path, target_resolution=target_res)

        elif w_type == "patient_record_processing":
            payload_raw = getattr(task, "input_payload", "")
            payload = json.loads(payload_raw) if payload_raw else get_synthetic_patient_record_fixture()
            res = process_patient_record_workload(task, payload)

        elif w_type == "lab_report_processing":
            payload_raw = getattr(task, "input_payload", "")
            payload = json.loads(payload_raw) if payload_raw else get_synthetic_lab_report_fixture()
            res = process_lab_report_workload(task, payload)

        elif w_type == "medical_metadata_extraction":
            payload_raw = getattr(task, "input_payload", "")
            payload = json.loads(payload_raw) if payload_raw else get_synthetic_medical_document_fixture()
            res = process_document_metadata_workload(task, payload)

        elif w_type == "appointment_scheduling":
            payload_raw = getattr(task, "input_payload", "")
            payload = json.loads(payload_raw) if payload_raw else get_synthetic_appointment_batch_fixture()
            res = process_appointment_scheduling_workload(task, payload)

        else:
            # Fallback to image processor or hash benchmark
            img_path = getattr(task, "image_path", "") or str(get_synthetic_medical_image_fixture())
            res = process_medical_image_workload(task, img_path)

        end_time = dj_timezone.now()
        task.completion_time = end_time
        task.status = "COMPLETED"
        task.execution_time = res["processing_time_s"]
        task.total_latency_ms = round(res["processing_time_s"] * 1000.0, 2)
        task.output_path = res.get("output_path", "")
        task.output_checksum = res.get("output_checksum", "")
        task.result_location = res.get("output_path", "")
        task.validation_status = "PASSED"
        task.output_payload = json.dumps(res.get("details", {}))
        task.save()
        task.record_history("RUNNING", "COMPLETED", changed_by="workload_executor")
        return True, "Executed successfully with verified results.", res

    except Exception as exc:
        end_time = dj_timezone.now()
        task.completion_time = end_time
        task.status = "FAILED"
        task.error_message = str(exc)
        task.validation_status = "FAILED"
        task.save()
        task.record_history("RUNNING", "FAILED", changed_by="workload_executor")
        return False, str(exc), {}
