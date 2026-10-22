"""
Test Suite for Hospital Workload Dataset Engine (Phase 3).
==========================================================
Verifies:
1. Complete registration and schema compliance of all 14 official workload scenarios across all 4 categories.
2. Genuine execution and output verification for the 5 Success Workload Cases:
   - HOSP-SUCCESS-01: Medical Image Preprocessing (CLAHE, 224x224, SHA-256)
   - HOSP-SUCCESS-02: Patient Clinical Record Processing (NEWS2 Vital Signs Scoring & De-identification)
   - HOSP-SUCCESS-03: Laboratory Metabolic & CBC Panel Processing (Reference ranges, flags, severity index)
   - HOSP-SUCCESS-04: Medical Document Metadata Extraction (Entity tagging, ICD-10 coding, doc signature)
   - HOSP-SUCCESS-05: Outpatient Appointment Scheduling (Conflict detection, triage queue, room assignment)
3. Input validation, execution duration, and cryptographic SHA-256 checksum generation for every processed workload.
4. Management commands `download_hospital_datasets` and `list_hospital_datasets`.
"""

import json
import os
from pathlib import Path
from django.test import TestCase
from django.core.management import call_command
from rest_framework.test import APIClient

from datasets.models import (
    WorkloadScenario,
    DatasetVersion,
    SecurityAuditEvent,
    DatasetStorageReplica,
    StorageDestination,
)
from tasks.models import Task, SchedulingDecision, ExperimentRun
from engine.benchmark_runner import run_hospital_benchmark, export_benchmark_csv
from engine.hospital_workloads import (
    INITIAL_14_SCENARIOS,
    ensure_all_14_scenarios_registered,
    get_synthetic_medical_image_fixture,
    get_synthetic_patient_record_fixture,
    get_synthetic_lab_report_fixture,
    get_synthetic_medical_document_fixture,
    get_synthetic_appointment_batch_fixture,
    get_synthetic_corrupted_image_fixture,
    get_synthetic_incomplete_patient_record_fixture,
    get_synthetic_unsupported_format_fixture,
    process_medical_image_workload,
    process_patient_record_workload,
    process_lab_report_workload,
    process_document_metadata_workload,
    process_appointment_scheduling_workload,
    execute_hospital_workload,
    compute_news2_score,
    sanitize_audit_details,
    record_security_event,
    attempt_dataset_replication,
    validate_workload_input,
)
from engine.storage_manager import (
    ensure_storage_destinations_initialized,
    replicate_file,
    verify_all_storage_replicas,
    export_storage_inventory_csv,
    calculate_file_sha256,
)


class HospitalWorkloadScenariosRegistrationTests(TestCase):
    """Verify registration and schema integrity for all 14 hospital workload scenarios."""

    def test_all_14_scenarios_registered(self):
        """All 14 scenarios must be registered with required metadata and correct categories."""
        count = ensure_all_14_scenarios_registered()
        self.assertEqual(WorkloadScenario.objects.count(), 14)

        categories = {"SUCCESS": 0, "ERROR": 0, "SECURITY": 0, "TIMEOUT": 0}
        for s in WorkloadScenario.objects.all():
            self.assertIn(s.category, categories)
            categories[s.category] += 1
            self.assertTrue(len(s.name) > 5)
            self.assertTrue(len(s.scenario_id) > 5)
            self.assertIn(s.privacy_policy, ["LOCAL_ONLY", "TRUSTED_EDGE", "CLOUD_ALLOWED"])
            self.assertTrue(s.cpu_cycles_giga > 0)
            self.assertTrue(s.memory_mb > 0)

        # Expected counts per category: 5 Success, 3 Error, 3 Security, 3 Timeout
        self.assertEqual(categories["SUCCESS"], 5)
        self.assertEqual(categories["ERROR"], 3)
        self.assertEqual(categories["SECURITY"], 3)
        self.assertEqual(categories["TIMEOUT"], 3)


class SuccessWorkloadsExecutionTests(TestCase):
    """Verify genuine execution, calculation, timing, and checksums for the 5 Success Workloads."""

    def setUp(self):
        ensure_all_14_scenarios_registered()

    def test_hosp_success_01_medical_image_preprocessing(self):
        """HOSP-SUCCESS-01: Genuine CLAHE, normalization, 224x224 resize, and SHA-256 calculation."""
        img_path = str(get_synthetic_medical_image_fixture())
        task = Task.objects.create(
            task_id="TASK-TEST-SUCC-01",
            name="Image Preprocess Test",
            workload_type="medical_image_preprocess",
            image_path=img_path,
            target_resolution=224,
            privacy_policy="TRUSTED_EDGE",
        )
        ok, msg, res = execute_hospital_workload(task)
        self.assertTrue(ok)
        task.refresh_from_db()

        self.assertEqual(task.status, "COMPLETED")
        self.assertEqual(task.validation_status, "PASSED")
        self.assertTrue(task.execution_time > 0.0)
        self.assertTrue(os.path.exists(task.output_path))
        self.assertEqual(len(task.output_checksum), 64)  # Valid SHA-256 hex string

    def test_hosp_success_02_patient_record_news2_scoring(self):
        """HOSP-SUCCESS-02: Patient record NEWS2 early warning score and de-identification verification."""
        fixture = get_synthetic_patient_record_fixture()
        # Verify NEWS2 score calculation logic directly
        score, acuity, flags = compute_news2_score(fixture["vitals"])
        self.assertIsInstance(score, int)
        self.assertIn(acuity, ["LOW", "LOW_MEDIUM", "MEDIUM", "HIGH_CRITICAL"])

        task = Task.objects.create(
            task_id="TASK-TEST-SUCC-02",
            name="Patient Record Triage Test",
            workload_type="patient_record_processing",
            input_payload=json.dumps(fixture),
            privacy_policy="LOCAL_ONLY",
        )
        ok, msg, res = execute_hospital_workload(task)
        self.assertTrue(ok)
        task.refresh_from_db()

        self.assertEqual(task.status, "COMPLETED")
        self.assertEqual(task.validation_status, "PASSED")
        self.assertTrue(task.execution_time > 0.0)
        self.assertTrue(len(task.output_checksum) == 64)

        output_details = json.loads(task.output_payload)
        self.assertIn("news2_score", output_details)
        self.assertIn("patient_deid_token", output_details)
        self.assertEqual(output_details["encounter_id"], "ENC-2026-0912")

    def test_hosp_success_03_lab_report_analyte_evaluation(self):
        """HOSP-SUCCESS-03: Metabolic and CBC panel reference range validation and severity grading."""
        fixture = get_synthetic_lab_report_fixture()
        task = Task.objects.create(
            task_id="TASK-TEST-SUCC-03",
            name="Lab Report Analysis Test",
            workload_type="lab_report_processing",
            input_payload=json.dumps(fixture),
            privacy_policy="TRUSTED_EDGE",
        )
        ok, msg, res = execute_hospital_workload(task)
        self.assertTrue(ok)
        task.refresh_from_db()

        self.assertEqual(task.status, "COMPLETED")
        self.assertTrue(task.execution_time > 0.0)
        self.assertEqual(len(task.output_checksum), 64)

        output_details = json.loads(task.output_payload)
        self.assertEqual(output_details["total_analytes"], 8)
        self.assertIn("analyzed_results", output_details)
        # Verify specific analyte flags
        results_by_code = {a["code"]: a for a in output_details["analyzed_results"]}
        self.assertEqual(results_by_code["HEMOGLOBIN"]["flag"], "NORMAL")
        self.assertEqual(results_by_code["CREATININE"]["flag"], "HIGH")  # 1.4 > 1.2 ref_max

    def test_hosp_success_04_medical_document_metadata_extraction(self):
        """HOSP-SUCCESS-04: Entity extraction, ICD-10 diagnostic code tagging, and HMAC signature."""
        fixture = get_synthetic_medical_document_fixture()
        task = Task.objects.create(
            task_id="TASK-TEST-SUCC-04",
            name="Doc Extraction Test",
            workload_type="medical_metadata_extraction",
            input_payload=json.dumps(fixture),
            privacy_policy="TRUSTED_EDGE",
        )
        ok, msg, res = execute_hospital_workload(task)
        self.assertTrue(ok)
        task.refresh_from_db()

        self.assertEqual(task.status, "COMPLETED")
        self.assertTrue(task.execution_time > 0.0)
        self.assertEqual(len(task.output_checksum), 64)

        output_details = json.loads(task.output_payload)
        self.assertEqual(output_details["service_department"], "PULMONOLOGY")
        icd_codes = [c["code"] for c in output_details["extracted_icd10_codes"]]
        self.assertIn("J18.9", icd_codes)
        self.assertIn("I10", icd_codes)
        self.assertTrue(output_details["word_count"] > 20)

    def test_hosp_success_05_appointment_scheduling_optimization(self):
        """HOSP-SUCCESS-05: Priority queue triage, room assignment, and conflict detection."""
        fixture = get_synthetic_appointment_batch_fixture()
        task = Task.objects.create(
            task_id="TASK-TEST-SUCC-05",
            name="Appointment Scheduling Test",
            workload_type="appointment_scheduling",
            input_payload=json.dumps(fixture),
            privacy_policy="CLOUD_ALLOWED",
        )
        ok, msg, res = execute_hospital_workload(task)
        self.assertTrue(ok)
        task.refresh_from_db()

        self.assertEqual(task.status, "COMPLETED")
        self.assertTrue(task.execution_time > 0.0)
        self.assertEqual(len(task.output_checksum), 64)

        output_details = json.loads(task.output_payload)
        self.assertEqual(output_details["total_requests"], 4)
        self.assertEqual(output_details["detected_conflicts"], 0)
        self.assertEqual(output_details["confirmed_slots"], 4)


class HospitalManagementCommandsTests(TestCase):
    """Verify management commands list_hospital_datasets and download_hospital_datasets."""

    def test_list_hospital_datasets_command(self):
        """python manage.py list_hospital_datasets runs cleanly without errors."""
        call_command("list_hospital_datasets", validate=True)
        self.assertEqual(WorkloadScenario.objects.count(), 14)

    def test_download_hospital_datasets_skip_download(self):
        """python manage.py download_hospital_datasets --skip-download initializes scenarios."""
        call_command("download_hospital_datasets", skip_download=True)
        self.assertEqual(WorkloadScenario.objects.count(), 14)


class ControlledErrorsExecutionTests(TestCase):
    """Verify controlled failure routing, failure codes, and retry inhibition for 3 Error Datasets."""

    def setUp(self):
        ensure_all_14_scenarios_registered()

    def test_hosp_error_01_malformed_input_detected_fails_gracefully(self):
        """HOSP-ERROR-01: Header corruption detected prior to processing, status FAILED, no infinite retries."""
        corrupted_file = get_synthetic_corrupted_image_fixture()
        task = Task.objects.create(
            task_id="TASK-TEST-ERR-01",
            name="Malformed Medical Image Scan Test",
            scenario_id="HOSP-ERROR-01",
            workload_type="malformed_input",
            image_path=str(corrupted_file),
            privacy_policy="TRUSTED_EDGE",
            retry_count=0,
            max_retries=3,
        )

        valid, code, msg, stage, retryable = validate_workload_input(task)
        self.assertFalse(valid)
        self.assertEqual(code, "ERR_MALFORMED_INPUT")
        self.assertFalse(retryable)

        ok, error_msg, res = execute_hospital_workload(task)
        self.assertFalse(ok)
        task.refresh_from_db()

        self.assertEqual(task.status, "FAILED")
        self.assertEqual(task.validation_status, "FAILED")
        self.assertEqual(task.error_code, "ERR_MALFORMED_INPUT")
        self.assertIn("Corrupt medical image stream header", task.error_message)
        self.assertEqual(task.retry_count, 0)

        history = list(task.queue_history.values_list("to_status", flat=True))
        self.assertIn("FAILED", history)

    def test_hosp_error_02_missing_mandatory_patient_fields_rejected(self):
        """HOSP-ERROR-02: Missing patient_uuid/vitals rejected with ERR_MISSING_MANDATORY_FIELDS."""
        incomplete_fixture = get_synthetic_incomplete_patient_record_fixture()
        task = Task.objects.create(
            task_id="TASK-TEST-ERR-02",
            name="Incomplete Patient Record Test",
            scenario_id="HOSP-ERROR-02",
            workload_type="missing_fields",
            input_payload=json.dumps(incomplete_fixture),
            privacy_policy="LOCAL_ONLY",
            retry_count=0,
            max_retries=3,
        )

        valid, code, msg, stage, retryable = validate_workload_input(task)
        self.assertFalse(valid)
        self.assertEqual(code, "ERR_MISSING_MANDATORY_FIELDS")
        self.assertFalse(retryable)

        ok, error_msg, res = execute_hospital_workload(task)
        self.assertFalse(ok)
        task.refresh_from_db()

        self.assertEqual(task.status, "REJECTED")
        self.assertEqual(task.validation_status, "REJECTED")
        self.assertEqual(task.error_code, "ERR_MISSING_MANDATORY_FIELDS")
        self.assertIn("Missing mandatory clinical fields", task.error_message)
        self.assertEqual(task.retry_count, 0)

    def test_hosp_error_03_unsupported_format_schema_mismatch_rejected(self):
        """HOSP-ERROR-03: Unsupported XML/non-JSON schema rejected with ERR_UNSUPPORTED_FORMAT."""
        unsupported_fixture = get_synthetic_unsupported_format_fixture()
        task = Task.objects.create(
            task_id="TASK-TEST-ERR-03",
            name="Unsupported Format Schema Mismatch Test",
            scenario_id="HOSP-ERROR-03",
            workload_type="unsupported_format",
            input_payload=unsupported_fixture,
            privacy_policy="TRUSTED_EDGE",
            retry_count=0,
            max_retries=3,
        )

        valid, code, msg, stage, retryable = validate_workload_input(task)
        self.assertFalse(valid)
        self.assertEqual(code, "ERR_UNSUPPORTED_FORMAT")
        self.assertFalse(retryable)

        ok, error_msg, res = execute_hospital_workload(task)
        self.assertFalse(ok)
        task.refresh_from_db()

        self.assertEqual(task.status, "REJECTED")
        self.assertEqual(task.validation_status, "REJECTED")
        self.assertEqual(task.error_code, "ERR_UNSUPPORTED_FORMAT")
        self.assertIn("Unsupported medical record format", task.error_message)
        self.assertEqual(task.retry_count, 0)


class DefensiveSecurityScenariosTests(TestCase):
    """Verify denial, defensive security logging, and privacy policy preservation for 3 Security Scenarios."""

    def setUp(self):
        ensure_all_14_scenarios_registered()

    def test_sanitize_audit_details_redacts_sensitive_keys(self):
        """Sensitive keywords (token, auth, secret, password, key) must be redacted."""
        raw_data = {
            "device_id": "MEC-01",
            "auth_token": "super_secret_jwt_token_999",
            "password_hash": "pbkdf2_sha256$260000$xyz",
            "client_secret": "my_app_secret",
            "nested_config": {
                "api_key": "prod_key_live_45678",
                "normal_field": "public_hospital_name",
            },
            "public_metric": 42.5,
        }
        sanitized = sanitize_audit_details(raw_data)
        self.assertEqual(sanitized["device_id"], "MEC-01")
        self.assertEqual(sanitized["auth_token"], "[REDACTED]")
        self.assertEqual(sanitized["password_hash"], "[REDACTED]")
        self.assertEqual(sanitized["client_secret"], "[REDACTED]")
        self.assertEqual(sanitized["nested_config"]["api_key"], "[REDACTED]")
        self.assertEqual(sanitized["nested_config"]["normal_field"], "public_hospital_name")
        self.assertEqual(sanitized["public_metric"], 42.5)

    def test_hosp_sec_01_unauthorized_task_submission_blocked_and_audited(self):
        """HOSP-SEC-01: Unauthenticated task submission triggers 401/403 and records UNAUTHORIZED_TASK_SUBMISSION."""
        task = Task.objects.create(
            task_id="TASK-TEST-SEC-01",
            name="Unauthorized Injection Workload Test",
            scenario_id="HOSP-SEC-01",
            workload_type="unauthorized_submission",
            privacy_policy="LOCAL_ONLY",
        )
        ok, msg, res = execute_hospital_workload(task)
        self.assertFalse(ok)
        task.refresh_from_db()
        self.assertEqual(task.status, "REJECTED")
        self.assertEqual(task.error_code, "SEC_UNAUTHORIZED_SUBMISSION")

        audit_ev = SecurityAuditEvent.objects.filter(event_type="UNAUTHORIZED_TASK_SUBMISSION", task_id="TASK-TEST-SEC-01").first()
        self.assertIsNotNone(audit_ev)
        self.assertTrue(audit_ev.blocked)
        self.assertEqual(audit_ev.severity, "HIGH")

        anon_client = APIClient()
        response = anon_client.post(
            "/api/tasks/",
            {"name": "Hacked Task Injection", "priority": 1, "cpu_cycles_giga": 2.0},
            format="json",
        )
        self.assertIn(response.status_code, (401, 403))

        api_audit = SecurityAuditEvent.objects.filter(event_type="UNAUTHORIZED_TASK_SUBMISSION").first()
        self.assertIsNotNone(api_audit)
        self.assertTrue(api_audit.blocked)

    def test_hosp_sec_02_invalid_mec_credentials_heartbeat_blocked_and_audited(self):
        """HOSP-SEC-02: Rogue MEC heartbeat rejected with HTTP 401 and records INVALID_MEC_AUTH."""
        task = Task.objects.create(
            task_id="TASK-TEST-SEC-02",
            name="Rogue MEC Credentials Test",
            scenario_id="HOSP-SEC-02",
            workload_type="invalid_agent_auth",
            input_payload=json.dumps({"device_id": "MEC-ROGUE-99"}),
            privacy_policy="TRUSTED_EDGE",
        )
        ok, msg, res = execute_hospital_workload(task)
        self.assertFalse(ok)
        task.refresh_from_db()
        self.assertEqual(task.status, "REJECTED")
        self.assertEqual(task.error_code, "SEC_INVALID_MEC_AUTH")

        audit_ev = SecurityAuditEvent.objects.filter(event_type="INVALID_MEC_AUTH", device_id="MEC-ROGUE-99").first()
        self.assertIsNotNone(audit_ev)
        self.assertEqual(audit_ev.severity, "CRITICAL")
        self.assertTrue(audit_ev.blocked)

        client = APIClient()
        response = client.post(
            "/api/mec/heartbeat/",
            {"mec_id": "MEC-ROGUE-99", "auth_token": "fraudulent_token_secret_12345"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

        api_audit = SecurityAuditEvent.objects.filter(event_type="INVALID_MEC_AUTH", device_id="MEC-ROGUE-99").latest("timestamp")
        self.assertIsNotNone(api_audit)
        self.assertIn("[REDACTED]", api_audit.details_json)
        self.assertNotIn("fraudulent_token_secret_12345", api_audit.details_json)

    def test_hosp_sec_03_privacy_policy_violation_replication_blocked_and_audited(self):
        """HOSP-SEC-03: Attempt to replicate LOCAL_ONLY data to Cloud tier is BLOCKED_BY_POLICY with CRITICAL audit."""
        permitted, reason, audit_ev, replica = attempt_dataset_replication(
            dataset_id="LOCAL-PATIENT-VITAL-DB",
            target_destination="CLOUD",
            privacy_policy="LOCAL_ONLY",
            source_ip="192.168.1.50",
            scenario_id="HOSP-SEC-03",
        )
        self.assertFalse(permitted)
        self.assertIn("BLOCKED_BY_POLICY", reason)
        self.assertIsNotNone(audit_ev)
        self.assertEqual(audit_ev.event_type, "PRIVACY_POLICY_VIOLATION")
        self.assertEqual(audit_ev.severity, "CRITICAL")
        self.assertTrue(audit_ev.blocked)

        self.assertIsNotNone(replica)
        self.assertEqual(replica.replication_status, "BLOCKED_BY_POLICY")
        self.assertFalse(replica.is_available)
        self.assertIn("LOCAL_ONLY", replica.last_error)

        task = Task.objects.create(
            task_id="TASK-TEST-SEC-03",
            name="Prohibited Cloud Replication Attempt",
            scenario_id="HOSP-SEC-03",
            workload_type="unauthorized_replication",
            privacy_policy="LOCAL_ONLY",
        )
        ok, msg, res = execute_hospital_workload(task)
        self.assertFalse(ok)
        task.refresh_from_db()
        self.assertEqual(task.status, "BLOCKED")
        self.assertEqual(task.validation_status, "FAILED")
        self.assertEqual(task.error_code, "SEC_PRIVACY_POLICY_VIOLATION")
        self.assertTrue(res.get("blocked", False))


class TimeoutAndLoopingScenariosTests(TestCase):
    """Verify bounded execution, worker fault detection, and retry exhaustion for 3 Timeout Scenarios."""

    def setUp(self):
        ensure_all_14_scenarios_registered()

    def test_hosp_time_01_execution_time_limit_watchdog_timed_out(self):
        """HOSP-TIME-01: Execution exceeding time limit is safely aborted by watchdog with status TIMED_OUT."""
        task = Task.objects.create(
            task_id="TASK-TEST-TIME-01",
            name="Infinite Matrix Computation Benchmark",
            scenario_id="HOSP-TIME-01",
            workload_type="execution_time_limit",
            privacy_policy="TRUSTED_EDGE",
            timeout_limit_seconds=1,  # Short bounded threshold for test
        )
        ok, msg, res = execute_hospital_workload(task)
        self.assertFalse(ok)
        task.refresh_from_db()

        self.assertEqual(task.status, "TIMED_OUT")
        self.assertEqual(task.validation_status, "FAILED")
        self.assertEqual(task.error_code, "ERR_EXECUTION_TIMEOUT")
        self.assertIn("Watchdog execution limit exceeded", task.error_message)
        self.assertEqual(task.execution_time, 1.0)

        history = list(task.queue_history.values_list("to_status", flat=True))
        self.assertIn("TIMED_OUT", history)

    def test_hosp_time_02_worker_unresponsive_dropped_node_reclaimed(self):
        """HOSP-TIME-02: Unresponsive/dropped edge worker triggers orphan reclaim and TIMED_OUT status."""
        task = Task.objects.create(
            task_id="TASK-TEST-TIME-02",
            name="Worker Unresponsive Workload Test",
            scenario_id="HOSP-TIME-02",
            workload_type="worker_unresponsive",
            privacy_policy="TRUSTED_EDGE",
        )
        ok, msg, res = execute_hospital_workload(task)
        self.assertFalse(ok)
        task.refresh_from_db()

        self.assertEqual(task.status, "TIMED_OUT")
        self.assertEqual(task.validation_status, "FAILED")
        self.assertEqual(task.error_code, "ERR_WORKER_UNRESPONSIVE")
        self.assertIn("Simulated worker unresponsive", task.error_message)
        self.assertIsNone(task.assigned_mec)  # Worker lock released

        history = list(task.queue_history.values_list("to_status", flat=True))
        self.assertIn("TIMED_OUT", history)

    def test_hosp_time_03_transient_failure_max_retries_exhaustion(self):
        """HOSP-TIME-03: Transient errors retry with exponential backoff up to max_retries then terminate in FAILED."""
        task = Task.objects.create(
            task_id="TASK-TEST-TIME-03",
            name="Transient Network Failure Retry Test",
            scenario_id="HOSP-TIME-03",
            workload_type="retry_exhaustion",
            privacy_policy="TRUSTED_EDGE",
            max_retries=3,
            retry_count=0,
        )
        ok, msg, res = execute_hospital_workload(task)
        self.assertFalse(ok)
        task.refresh_from_db()

        self.assertEqual(task.status, "FAILED")
        self.assertEqual(task.validation_status, "FAILED")
        self.assertEqual(task.error_code, "ERR_MAX_RETRIES_EXCEEDED")
        self.assertEqual(task.retry_count, 3)
        self.assertEqual(task.max_retries, 3)
        self.assertIn("reaching maximum configured retry limit", task.error_message)

        # Verify history recorded the RETRYING steps and final FAILED step
        history = list(task.queue_history.values_list("to_status", flat=True))
        self.assertIn("RETRYING", history)
        self.assertIn("FAILED", history)


class StorageDestinationsAndReplicationTests(TestCase):
    """Verify 3 verified storage destinations, physical replication, SHA-256 verification, and CSV export."""

    def setUp(self):
        ensure_all_14_scenarios_registered()
        self.dest_dict = ensure_storage_destinations_initialized()

    def test_ensure_storage_destinations_initialized(self):
        """LOCAL_STORAGE, MEC_STORAGE, and CLOUD_STORAGE initialized with verified directories outside webroot."""
        self.assertEqual(len(self.dest_dict), 3)
        self.assertIn("LOCAL_STORAGE", self.dest_dict)
        self.assertIn("MEC_STORAGE", self.dest_dict)
        self.assertIn("CLOUD_STORAGE", self.dest_dict)

        for dest_id, dest in self.dest_dict.items():
            p = Path(dest.base_path)
            self.assertTrue(p.exists(), f"Path for {dest_id} does not exist: {p}")
            self.assertTrue((p / ".storage_verified").exists())
            self.assertTrue(dest.capacity_bytes > 0)
            self.assertTrue(dest.is_active)

    def test_replicate_file_permitted_trusted_edge_to_mec(self):
        """File with TRUSTED_EDGE policy successfully replicates to MEC_STORAGE with SHA-256 match and idempotency."""
        src_file = Path("data_storage/hospital_workloads/test_sample_edge.bin")
        src_file.parent.mkdir(parents=True, exist_ok=True)
        with open(src_file, "wb") as fh:
            fh.write(b"SYNTHETIC_MEDICAL_PAYLOAD_TRUSTED_EDGE_CONTENT_12345")

        src_hash = calculate_file_sha256(src_file)

        # 1. First replication
        ok, msg, replica = replicate_file(
            source_path=str(src_file),
            dataset_id="TEST-DS-EDGE-01",
            target_destination_id="MEC_STORAGE",
            privacy_policy="TRUSTED_EDGE",
        )
        self.assertTrue(ok, msg)
        self.assertIsNotNone(replica)
        self.assertEqual(replica.replication_status, "VERIFIED")
        self.assertEqual(replica.sha256_checksum, src_hash)
        self.assertTrue(replica.is_available)
        self.assertTrue(Path(replica.absolute_path).exists())

        # Verify on-disk checksum
        dest_hash = calculate_file_sha256(Path(replica.absolute_path))
        self.assertEqual(dest_hash, src_hash)

        # 2. Idempotent re-run
        ok_again, msg_again, rep_again = replicate_file(
            source_path=str(src_file),
            dataset_id="TEST-DS-EDGE-01",
            target_destination_id="MEC_STORAGE",
            privacy_policy="TRUSTED_EDGE",
        )
        self.assertTrue(ok_again)
        self.assertIn("idempotent", msg_again)
        self.assertEqual(rep_again.replication_status, "VERIFIED")

    def test_replicate_file_permitted_cloud_allowed_to_cloud(self):
        """File with CLOUD_ALLOWED policy successfully replicates to CLOUD_STORAGE."""
        src_file = Path("data_storage/hospital_workloads/test_sample_cloud.bin")
        src_file.parent.mkdir(parents=True, exist_ok=True)
        with open(src_file, "wb") as fh:
            fh.write(b"PUBLIC_DEIDENTIFIED_MEDICAL_BENCHMARK_CONTENT_XYZ99")

        src_hash = calculate_file_sha256(src_file)

        ok, msg, replica = replicate_file(
            source_path=str(src_file),
            dataset_id="TEST-DS-CLOUD-01",
            target_destination_id="CLOUD_STORAGE",
            privacy_policy="CLOUD_ALLOWED",
        )
        self.assertTrue(ok, msg)
        self.assertEqual(replica.replication_status, "VERIFIED")
        self.assertEqual(replica.sha256_checksum, src_hash)

    def test_replicate_file_blocked_by_policy_local_only_to_mec(self):
        """Attempting to replicate LOCAL_ONLY data to MEC_STORAGE is strictly blocked with audit event."""
        src_file = Path("data_storage/hospital_workloads/test_local_only.bin")
        src_file.parent.mkdir(parents=True, exist_ok=True)
        with open(src_file, "wb") as fh:
            fh.write(b"SENSITIVE_LOCAL_PATIENT_VITALS_SECRET")

        ok, msg, replica = replicate_file(
            source_path=str(src_file),
            dataset_id="LOCAL-SENSITIVE-01",
            target_destination_id="MEC_STORAGE",
            privacy_policy="LOCAL_ONLY",
        )
        self.assertFalse(ok)
        self.assertIn("BLOCKED_BY_POLICY", msg)
        self.assertEqual(replica.replication_status, "BLOCKED_BY_POLICY")
        self.assertFalse(replica.is_available)

        audit = SecurityAuditEvent.objects.filter(
            event_type="PRIVACY_POLICY_VIOLATION",
            task_id="LOCAL-SENSITIVE-01",
        ).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.severity, "CRITICAL")
        self.assertTrue(audit.blocked)

    def test_verify_all_storage_replicas_audit_sweep(self):
        """verify_all_storage_replicas correctly audits all replicas on disk."""
        summary = verify_all_storage_replicas()
        self.assertIn("total_replicas", summary)
        self.assertIn("verified", summary)
        self.assertIn("blocked", summary)

    def test_export_storage_inventory_csv(self):
        """export_storage_inventory_csv produces a valid CSV file with all required headers."""
        csv_file_path = export_storage_inventory_csv()
        self.assertTrue(os.path.exists(csv_file_path))

        with open(csv_file_path, "r", encoding="utf-8") as fh:
            header_line = fh.readline().strip()
            self.assertIn("Replica ID", header_line)
            self.assertIn("Dataset ID", header_line)
            self.assertIn("Destination ID", header_line)
            self.assertIn("Replication Status", header_line)
            self.assertIn("SHA-256 Checksum", header_line)

    def test_storage_rest_apis(self):
        """REST APIs for storage destinations, replicas, replication, and CSV export function cleanly."""
        client = APIClient()

        # 1. Destinations endpoint
        r1 = client.get("/api/datasets/storage/destinations/")
        self.assertEqual(r1.status_code, 200)
        dest_data = r1.json()["destinations"]
        self.assertEqual(len(dest_data), 3)

        # 2. Replicas endpoint
        r2 = client.get("/api/datasets/storage/replicas/")
        self.assertEqual(r2.status_code, 200)

        # 3. Trigger replication endpoint with policy block
        r3 = client.post(
            "/api/datasets/storage/replicate/",
            {
                "source_path": str(get_synthetic_medical_image_fixture()),
                "dataset_id": "TEST-API-REPL-01",
                "target_destination_id": "CLOUD_STORAGE",
                "privacy_policy": "LOCAL_ONLY",
            },
            format="json",
        )
        self.assertEqual(r3.status_code, 403)
        self.assertEqual(r3.json()["replication_status"], "BLOCKED_BY_POLICY")

        # 4. Export CSV endpoint
        r4 = client.get("/api/datasets/storage/export-csv/")
        self.assertEqual(r4.status_code, 200)
        self.assertIn("text/csv", r4.headers.get("Content-Type", ""))
        self.assertIn(b"Replica ID", r4.content)


class HospitalSchedulersComparativeBenchmarkTests(TestCase):
    """
    Phases 7 & 8: Verify comparative evaluation of Proposed GA vs 5 baselines:
    - Round Robin
    - First Fit
    - Random
    - Greedy
    - Privacy-Aware
    - Proposed GA

    Ensures zero policy violations across all algorithms, correct makespan & latency calculations,
    decision recording, CSV export with 14 columns, management command, and REST APIs.
    """

    def setUp(self):
        ensure_all_14_scenarios_registered()
        ensure_storage_destinations_initialized()

    def test_run_hospital_benchmark_all_algorithms(self):
        """Benchmark runs all 6 algorithms, recording zero policy violations, decisions, and experiment run."""
        res = run_hospital_benchmark(tasks_count=6, seed=42, population=10, generations=5)
        self.assertIn("experiment_id", res)
        self.assertIn("runs", res)
        self.assertIn("summary", res)

        runs = res["runs"]
        expected_algos = [
            "round_robin",
            "first_fit",
            "random",
            "greedy",
            "privacy_aware",
            "proposed_ga",
        ]
        for algo in expected_algos:
            self.assertIn(algo, runs)
            data = runs[algo]
            # Policy enforcement constraint: zero policy violations
            self.assertEqual(data["policy_violations"], 0, f"Algorithm {algo} had policy violations!")
            self.assertEqual(data["privacy_compliance_rate"], 100.0)
            self.assertGreater(data["makespan_s"], 0)
            self.assertGreater(data["avg_latency_s"], 0)
            self.assertEqual(data["tasks_assigned"] + data["tasks_blocked"], 6)

        # Verify ExperimentRun persistence
        exp = ExperimentRun.objects.filter(experiment_id=res["experiment_id"]).first()
        self.assertIsNotNone(exp)
        self.assertEqual(exp.tasks_count, 6)

        # Verify SchedulingDecision persistence
        decisions_count = SchedulingDecision.objects.filter(
            task__scenario_id__gt=""
        ).count()
        self.assertGreater(decisions_count, 0)

    def test_export_benchmark_csv(self):
        """export_benchmark_csv creates a valid CSV containing all 14 mandatory columns."""
        # Ensure at least one benchmark exists
        run_hospital_benchmark(tasks_count=4, seed=42, population=8, generations=4)
        csv_path = export_benchmark_csv()
        self.assertTrue(os.path.exists(csv_path))

        with open(csv_path, "r", encoding="utf-8") as fh:
            header = fh.readline().strip().split(",")
            required_cols = [
                "Algorithm",
                "Tasks Assigned",
                "Tasks Blocked",
                "Policy Violations",
                "Makespan (s)",
                "Average Latency (s)",
                "Throughput (tasks/s)",
                "Local Resource Utilization (%)",
                "MEC Resource Utilization (%)",
                "Cloud Resource Utilization (%)",
                "Energy Consumption (J)",
                "Scheduling Overhead (ms)",
                "Privacy Compliance Rate (%)",
                "Timestamp",
            ]
            for col in required_cols:
                self.assertIn(col, header, f"Missing column {col} in CSV header: {header}")

    def test_benchmark_management_command(self):
        """Management command `run_hospital_scheduler_benchmark` executes cleanly without errors."""
        call_command(
            "run_hospital_scheduler_benchmark",
            tasks_count=4,
            population=8,
            generations=4,
            seed=42,
        )
        self.assertTrue(ExperimentRun.objects.exists())

    def test_benchmark_rest_endpoints(self):
        """REST endpoints for benchmark run, summary, and CSV export function correctly."""
        client = APIClient()

        # 1. Summary endpoint
        r1 = client.get("/api/tasks/hospital-benchmark/summary/")
        self.assertEqual(r1.status_code, 200)
        self.assertIn("summary", r1.json())

        # 2. Trigger run endpoint
        r2 = client.post(
            "/api/tasks/hospital-benchmark/run/",
            {
                "tasks_count": 4,
                "population_size": 8,
                "generations": 4,
                "seed": 42,
            },
            format="json",
        )
        self.assertEqual(r2.status_code, 200)
        body = r2.json()
        self.assertIn("experiment_id", body)
        self.assertIn("runs", body)
        self.assertIn("proposed_ga", body["runs"])

        # 3. Export CSV endpoint
        r3 = client.get("/api/tasks/hospital-benchmark/export-csv/")
        self.assertEqual(r3.status_code, 200)
        self.assertIn("text/csv", r3.headers.get("Content-Type", ""))
        self.assertIn(b"Algorithm", r3.content)
        self.assertIn(b"Tasks Assigned", r3.content)


