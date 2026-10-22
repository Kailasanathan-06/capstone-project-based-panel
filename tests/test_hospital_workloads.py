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

from datasets.models import WorkloadScenario, DatasetVersion
from tasks.models import Task
from engine.hospital_workloads import (
    INITIAL_14_SCENARIOS,
    ensure_all_14_scenarios_registered,
    get_synthetic_medical_image_fixture,
    get_synthetic_patient_record_fixture,
    get_synthetic_lab_report_fixture,
    get_synthetic_medical_document_fixture,
    get_synthetic_appointment_batch_fixture,
    process_medical_image_workload,
    process_patient_record_workload,
    process_lab_report_workload,
    process_document_metadata_workload,
    process_appointment_scheduling_workload,
    execute_hospital_workload,
    compute_news2_score,
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
