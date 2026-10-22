"""
Medical Image Processing, Digital Twin & Security Policy Scheduling Test Suite.
================================================================================
Comprehensive verification for:
1. Medical image preprocessing engine (validation, CLAHE, resizing, checksums, timing, corruption handling).
2. Privacy policy engine (LOCAL_ONLY, TRUSTED_EDGE, CLOUD_ALLOWED hard constraint feasibility & dispatch validation).
3. Digital Twin state mirroring (LOCAL measured hardware, MEC live telemetry, CLOUD simulation).
4. Multi-objective Genetic Algorithm & Baseline Schedulers (Round Robin, First Fit, Random, Greedy, Privacy-Aware).
5. Task execution across execution tiers (LOCAL genuine execution, MEC dispatch, CLOUD simulation).
6. Comparative experiment benchmark API & CSV export streaming.
"""

import os
import io
import csv
import time
import shutil
import hashlib
import tempfile
from PIL import Image
import numpy as np

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from engine.image_processor import MedicalImageProcessor
from engine.policy_engine import PolicyEngine
from engine.digital_twin import DigitalTwin
from engine.scheduler import Scheduler
from engine.genetic_algorithm import GeneticAlgorithm
from tasks.models import Task
from tasks.services import (
    build_task_dict,
    execute_task_locally,
    execute_task_cloud_simulation,
    run_ga_dispatch,
)
from mec_manager.models import MECAgent, Heartbeat
from datasets.models import MedicalDatasetMetadata, MedicalDatasetSample


class MedicalImageProcessorTests(TestCase):
    """Test verification for the genuine medical image preprocessing engine."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="secure_dt_test_")
        self.processor = MedicalImageProcessor(output_dir=os.path.join(self.temp_dir, "processed"))

        # Create a valid synthetic grayscale test image
        self.valid_img_path = os.path.join(self.temp_dir, "test_lung_scan.png")
        arr = np.random.randint(20, 230, size=(128, 128), dtype=np.uint8)
        img = Image.fromarray(arr, mode="L")
        img.save(self.valid_img_path)

        # Create a corrupt non-image file
        self.corrupt_img_path = os.path.join(self.temp_dir, "corrupt_scan.png")
        with open(self.corrupt_img_path, "wb") as f:
            f.write(b"NOT_A_VALID_IMAGE_HEADER_DATA_STREAM_XYZ123456789")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_normalize_clahe_pipeline(self):
        """Test full CLAHE + normalization pipeline with 224x224 target resolution."""
        res = self.processor.process(
            image_path=self.valid_img_path,
            operation="normalize_clahe",
            target_resolution=224,
        )

        self.assertTrue(os.path.exists(res["output_path"]), "Output image must exist on disk.")
        self.assertEqual(res["target_resolution"], 224)
        self.assertEqual(res["operation"], "normalize_clahe")
        self.assertGreater(res["processing_time_s"], 0.0)
        self.assertEqual(len(res["input_checksum"]), 64)
        self.assertEqual(len(res["output_checksum"]), 64)

        # Verify output dimensions
        with Image.open(res["output_path"]) as out_img:
            self.assertEqual(out_img.size, (224, 224))
            self.assertEqual(out_img.mode, "L")

    def test_grayscale_resize_pipeline(self):
        """Test grayscale resize pipeline without CLAHE."""
        res = self.processor.process(
            image_path=self.valid_img_path,
            operation="grayscale_resize",
            target_resolution=112,
        )
        self.assertTrue(os.path.exists(res["output_path"]))
        with Image.open(res["output_path"]) as out_img:
            self.assertEqual(out_img.size, (112, 112))

    def test_corrupted_image_rejection(self):
        """Test that corrupted files are strictly rejected with an informative error."""
        with self.assertRaises(ValueError) as ctx:
            self.processor.process(image_path=self.corrupt_img_path, raise_on_error=True)
        self.assertIn("Corrupted or invalid image", str(ctx.exception))

    def test_nonexistent_image_rejection(self):
        """Test that missing files are rejected."""
        with self.assertRaises(FileNotFoundError):
            self.processor.process(image_path=os.path.join(self.temp_dir, "missing.png"), raise_on_error=True)


class PolicyEngineTests(TestCase):
    """Test verification for hard privacy constraints and dispatch eligibility."""

    def setUp(self):
        self.resources = [
            {
                "resource_id": "LOCAL",
                "resource_type": "local",
                "availability": True,
                "is_stale": False,
                "is_online": True,
                "max_memory": 8192,
                "supported_workloads": ["normalize_clahe", "grayscale_resize"],
            },
            {
                "resource_id": "MEC-1",
                "resource_type": "mec",
                "availability": True,
                "is_stale": False,
                "is_online": True,
                "max_memory": 4096,
                "supported_workloads": ["normalize_clahe", "grayscale_resize"],
            },
            {
                "resource_id": "MEC-2",
                "resource_type": "mec",
                "availability": False,
                "is_stale": True,
                "is_online": False,
                "max_memory": 4096,
                "supported_workloads": ["normalize_clahe"],
            },
            {
                "resource_id": "CLOUD",
                "resource_type": "cloud",
                "availability": True,
                "is_stale": False,
                "is_online": True,
                "max_memory": 32768,
                "supported_workloads": ["normalize_clahe", "grayscale_resize"],
            },
        ]

    def test_local_only_policy_enforcement(self):
        """LOCAL_ONLY tasks must be eligible ONLY on LOCAL."""
        task = {"privacy_policy": "LOCAL_ONLY", "memory_mb": 512, "operation": "normalize_clahe"}
        eligible = PolicyEngine.get_eligible_resources(task, self.resources)
        eligible_ids = [r["resource_id"] for r in eligible]

        self.assertEqual(eligible_ids, ["LOCAL"])

        # Validate dispatch
        valid_local, _ = PolicyEngine.validate_dispatch(task, "LOCAL", self.resources)
        self.assertTrue(valid_local)

        valid_mec, reason_mec = PolicyEngine.validate_dispatch(task, "MEC-1", self.resources)
        self.assertFalse(valid_mec)
        self.assertIn("LOCAL_ONLY", reason_mec)

        valid_cloud, reason_cloud = PolicyEngine.validate_dispatch(task, "CLOUD", self.resources)
        self.assertFalse(valid_cloud)
        self.assertIn("LOCAL_ONLY", reason_cloud)

    def test_trusted_edge_policy_enforcement(self):
        """TRUSTED_EDGE tasks can run on LOCAL or online MEC, never CLOUD or offline MEC."""
        task = {"privacy_policy": "TRUSTED_EDGE", "memory_mb": 512, "operation": "normalize_clahe"}
        eligible = PolicyEngine.get_eligible_resources(task, self.resources)
        eligible_ids = [r["resource_id"] for r in eligible]

        self.assertIn("LOCAL", eligible_ids)
        self.assertIn("MEC-1", eligible_ids)
        self.assertNotIn("MEC-2", eligible_ids)  # Offline/stale
        self.assertNotIn("CLOUD", eligible_ids)  # Forbidden

        valid_cloud, _ = PolicyEngine.validate_dispatch(task, "CLOUD", self.resources)
        self.assertFalse(valid_cloud)

        valid_stale_mec, _ = PolicyEngine.validate_dispatch(task, "MEC-2", self.resources)
        self.assertFalse(valid_stale_mec)

    def test_cloud_allowed_policy_enforcement(self):
        """CLOUD_ALLOWED tasks can run on LOCAL, online MEC, or CLOUD."""
        task = {"privacy_policy": "CLOUD_ALLOWED", "memory_mb": 512, "operation": "normalize_clahe"}
        eligible = PolicyEngine.get_eligible_resources(task, self.resources)
        eligible_ids = [r["resource_id"] for r in eligible]

        self.assertIn("LOCAL", eligible_ids)
        self.assertIn("MEC-1", eligible_ids)
        self.assertIn("CLOUD", eligible_ids)
        self.assertNotIn("MEC-2", eligible_ids)  # Still offline


class DigitalTwinAndSchedulersTests(TestCase):
    """Test Digital Twin metrics tracking and GA vs Baseline Schedulers."""

    def setUp(self):
        self.twin = DigitalTwin()
        self.scheduler = Scheduler(self.twin, seed=42)
        self.sample_tasks = [
            {
                "task_id": "MED-01",
                "name": "Pneumonia-Confidential",
                "privacy_policy": "LOCAL_ONLY",
                "privacy_sensitivity": 0.90,
                "data_size_mb": 1.0,
                "cpu_cycles_giga": 0.6,
                "deadline_ms": 350,
            },
            {
                "task_id": "MED-02",
                "name": "Pneumonia-WardScan",
                "privacy_policy": "TRUSTED_EDGE",
                "privacy_sensitivity": 0.50,
                "data_size_mb": 0.8,
                "cpu_cycles_giga": 0.4,
                "deadline_ms": 280,
            },
            {
                "task_id": "MED-03",
                "name": "Pneumonia-PublicResearch",
                "privacy_policy": "CLOUD_ALLOWED",
                "privacy_sensitivity": 0.15,
                "data_size_mb": 0.5,
                "cpu_cycles_giga": 0.3,
                "deadline_ms": 400,
            },
        ]

    def test_digital_twin_telemetry_modes(self):
        """LOCAL must be MEASURED_HARDWARE and CLOUD must be SIMULATED_CLOUD."""
        states = {s["resource_id"]: s for s in self.twin.states()}

        self.assertIn("LOCAL", states)
        self.assertIn("CLOUD", states)

        self.assertEqual(states["LOCAL"]["telemetry_mode"], "MEASURED_HARDWARE")
        self.assertFalse(states["LOCAL"]["is_simulated"])

        self.assertEqual(states["CLOUD"]["telemetry_mode"], "SIMULATED_CLOUD")
        self.assertTrue(states["CLOUD"]["is_simulated"])

    def test_ga_optimizer_privacy_compliance(self):
        """Proposed GA must satisfy privacy constraints for all tasks."""
        assignments, _, history, best_fitness = GeneticAlgorithm(
            self.twin.states(),
            population=30,
            generations=20,
            seed=42,
        ).optimize(self.sample_tasks)

        self.assertEqual(len(assignments), 3)
        # Task 0 is LOCAL_ONLY -> Must be LOCAL
        self.assertEqual(assignments[0], "LOCAL")
        # Task 1 is TRUSTED_EDGE -> Must NOT be CLOUD
        self.assertNotEqual(assignments[1], "CLOUD")
        # Best fitness must be finite
        self.assertLess(best_fitness, 9999.0)

    def test_all_baselines_execution(self):
        """All 6 scheduling algorithms must run successfully on identical workloads."""
        results = self.scheduler.run_all_baselines(self.sample_tasks, seed=42)

        for algo in ["proposed_ga", "round_robin", "first_fit", "random", "greedy", "privacy_aware"]:
            self.assertIn(algo, results)
            m = results[algo]["metrics"]
            self.assertIn("avg_latency_ms", m)
            self.assertIn("deadline_miss_rate", m)
            self.assertIn("total_energy_j", m)
            self.assertIn("policy_compliance_rate", m)


class TaskExecutionTiersTests(TestCase):
    """Test genuine execution of medical tasks across execution tiers."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="secure_dt_task_test_")
        self.test_img = os.path.join(self.temp_dir, "sample_cxr.png")
        arr = np.random.randint(30, 220, size=(100, 100), dtype=np.uint8)
        Image.fromarray(arr, mode="L").save(self.test_img)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_execute_task_locally(self):
        """Execute task locally on hospital workstation."""
        task = Task.objects.create(
            name="Local-Pneumonia-Test",
            priority=1,
            data_size_mb=0.8,
            cpu_cycles_giga=0.5,
            deadline_ms=300,
            privacy_policy="LOCAL_ONLY",
            image_path=self.test_img,
            operation="normalize_clahe",
            target_resolution=224,
            status="QUEUED",
        )

        success, msg = execute_task_locally(task)
        self.assertTrue(success, f"Local execution failed: {msg}")

        task.refresh_from_db()
        self.assertEqual(task.status, "COMPLETED")
        self.assertEqual(task.assigned_node, "LOCAL")
        self.assertEqual(task.assigned_tier, "LOCAL")
        self.assertFalse(task.is_simulated_execution)
        self.assertTrue(os.path.exists(task.output_path))
        self.assertEqual(len(task.output_checksum), 64)
        self.assertGreater(task.execution_time, 0.0)

    def test_execute_task_cloud_simulation(self):
        """Execute CLOUD_ALLOWED task in simulated cloud tier."""
        task = Task.objects.create(
            name="Cloud-Pneumonia-Test",
            priority=3,
            data_size_mb=0.5,
            cpu_cycles_giga=0.3,
            deadline_ms=500,
            privacy_policy="CLOUD_ALLOWED",
            image_path=self.test_img,
            operation="grayscale_resize",
            target_resolution=224,
            status="QUEUED",
        )

        success, msg = execute_task_cloud_simulation(task)
        self.assertTrue(success, f"Cloud execution failed: {msg}")

        task.refresh_from_db()
        self.assertEqual(task.status, "COMPLETED")
        self.assertEqual(task.assigned_node, "CLOUD")
        self.assertEqual(task.assigned_tier, "CLOUD")
        self.assertTrue(task.is_simulated_execution)
        self.assertGreater(task.total_latency_ms, 150.0)  # includes simulated WAN latency


class APIExperimentBenchmarksTests(TestCase):
    """Test API benchmark comparison and CSV export streaming."""

    def setUp(self):
        self.user = User.objects.create_user(username="res_tester", password="secure_test_password123")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_compare_endpoint(self):
        """GET and POST /api/digital-twin/compare/ returns all 6 schedulers."""
        response = self.client.post("/api/digital-twin/compare/", {
            "tasks_count": 6,
            "seed": 42,
            "population": 20,
            "generations": 10,
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("metadata", data)
        self.assertIn("algorithms", data)
        self.assertEqual(data["metadata"]["tasks_count"], 6)

        for algo in ["proposed_ga", "round_robin", "first_fit", "random", "greedy", "privacy_aware"]:
            self.assertIn(algo, data["algorithms"])

    def test_export_experiments_csv_endpoint(self):
        """GET /api/digital-twin/experiments/export-csv/ streams valid RFC-compliant CSV."""
        response = self.client.get("/api/digital-twin/experiments/export-csv/?tasks_count=6&seed=42")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response["Content-Type"].startswith("text/csv"))
        self.assertIn("attachment; filename=", response["Content-Disposition"])

        content = response.content.decode("utf-8")
        reader = csv.reader(io.StringIO(content))
        header = next(reader)

        self.assertIn("Algorithm", header)
        self.assertIn("Avg_Latency_ms", header)
        self.assertIn("Deadline_Miss_Rate", header)
        self.assertIn("Policy_Compliance_Rate", header)

        rows = list(reader)
        # Should have data rows for the algorithms
        algo_rows = [r for r in rows if r and r[0] in ["proposed_ga", "round_robin", "first_fit", "random", "greedy", "privacy_aware"]]
        self.assertEqual(len(algo_rows), 6)


class SchedulerStrictEligibilityTests(TestCase):
    """Rigorous tests for offline-node rejection, strict policy enforcement, and blocked-task handling."""

    def setUp(self):
        self.twin = DigitalTwin()

    def test_strict_rejection_of_offline_and_stale_nodes(self):
        """Offline, stale, or quarantined nodes must be strictly rejected from eligible candidates."""
        res_list = [
            {"resource_id": "LOCAL", "resource_type": "local", "availability": True, "is_online": True, "is_stale": False, "max_memory": 4096},
            {"resource_id": "MEC-01", "resource_type": "mec", "availability": False, "is_online": False, "is_stale": False, "max_memory": 8192},
            {"resource_id": "MEC-02", "resource_type": "mec", "availability": True, "is_online": False, "is_stale": True, "max_memory": 8192},
            {"resource_id": "CLOUD", "resource_type": "cloud", "availability": True, "is_online": True, "is_stale": False, "max_memory": 65536},
        ]
        task = {
            "task_id": "T_TEST_1",
            "privacy_policy": "TRUSTED_EDGE",
            "memory_mb": 1024,
            "operation": "normalize_clahe",
        }
        candidates = PolicyEngine.get_eligible_resources(task, res_list)
        candidate_ids = [c["resource_id"] for c in candidates]

        # Only LOCAL should be eligible (MEC-01 is offline, MEC-02 is stale, CLOUD is barred by TRUSTED_EDGE)
        self.assertEqual(candidate_ids, ["LOCAL"])
        self.assertNotIn("MEC-01", candidate_ids)
        self.assertNotIn("MEC-02", candidate_ids)
        self.assertNotIn("CLOUD", candidate_ids)

        # validate_dispatch must also fail for offline/stale nodes
        valid, reason = PolicyEngine.validate_dispatch(task, "MEC-01", res_list)
        self.assertFalse(valid)
        self.assertIn("offline", reason.lower())

        valid_stale, reason_stale = PolicyEngine.validate_dispatch(task, "MEC-02", res_list)
        self.assertFalse(valid_stale)

    def test_no_eligible_resource_returns_blocked_with_zero_violations(self):
        """When no resource meets task requirements, task is BLOCKED and policy violations remain 0."""
        # Simulated resources where LOCAL is offline and CLOUD is available
        res_list = [
            {"resource_id": "LOCAL", "resource_type": "local", "availability": False, "is_online": False, "is_stale": False, "max_memory": 4096},
            {"resource_id": "CLOUD", "resource_type": "cloud", "availability": True, "is_online": True, "is_stale": False, "max_memory": 65536,
             "network_latency_ms": 150.0, "cpu_utilization": 0.4, "energy_rate": 5.0, "privacy_loss_factor": 0.4, "security_risk": 0.2},
        ]
        # LOCAL_ONLY task - cannot go to cloud
        task = {
            "task_id": "T_UNASSIGNABLE",
            "privacy_policy": "LOCAL_ONLY",
            "memory_mb": 512,
            "data_size_mb": 2.0,
            "cpu_cycles_giga": 0.5,
            "deadline_ms": 500,
            "privacy_sensitivity": 0.9,
            "security_sensitivity": 0.5,
        }

        sched = Scheduler(self.twin)
        candidates = sched._get_eligible_candidates(task, res_list)
        self.assertEqual(candidates, [])

        # Schedulers must safely assign BLOCKED
        for schedule_func in [sched.round_robin_schedule, sched.first_fit_schedule, sched.greedy_schedule, sched.privacy_aware_schedule]:
            # Temporarily stub states
            orig_states = sched.dt.states
            sched.dt.states = lambda: res_list
            try:
                assigns, metrics = schedule_func([task])
                self.assertEqual(assigns, ["BLOCKED"])
                self.assertEqual(metrics["blocked_tasks"], 1)
                self.assertEqual(metrics["policy_violations"], 0)
            finally:
                sched.dt.states = orig_states

    def test_ga_strict_blocked_chromosome_when_no_eligible_nodes(self):
        """Genetic algorithm assigns BLOCKED when no resources meet privacy criteria."""
        res_list = [
            {"resource_id": "CLOUD", "resource_type": "cloud", "availability": True, "is_online": True, "is_stale": False, "max_memory": 65536,
             "network_latency_ms": 150.0, "cpu_utilization": 0.4, "energy_rate": 5.0, "privacy_loss_factor": 0.4, "security_risk": 0.2},
        ]
        ga = GeneticAlgorithm(res_list, population=10, generations=5, seed=42)
        task = {
            "task_id": "T_LOCAL_ONLY",
            "privacy_policy": "LOCAL_ONLY",
            "memory_mb": 512,
            "data_size_mb": 1.0,
            "cpu_cycles_giga": 0.5,
            "deadline_ms": 500,
        }
        assignments, _, _, _ = ga.optimize([task])
        self.assertEqual(assignments, ["BLOCKED"])

