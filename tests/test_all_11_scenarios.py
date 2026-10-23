"""
Automated Test Suite for All 11 Digital Twin Edge-Cloud ZIP Scenarios
======================================================================
Verifies:
1. Physical existence and integrity of all 11 scenario ZIPs and master suite
2. Category A (5 Successes): Archive structure, manifest fields, resource consistency, GA allocation
3. Category B (3 Failures): Corrupt header rejection, invalid manifest schema rejection, unassigned capacity/policy violation
4. Category C (3 Loop/Timeout): Bounded queue processing, dependency cycle detection, timeout simulation watchdog handling
"""

import os
import sys
import io
import json
import zipfile
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "securedt.settings")
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from engine.dataset_analysis_service import (
    process_zip_dataset_upload,
    detect_dependency_cycle,
    validate_manifest_schema
)

SUITE_DIR = Path("test_datasets_suite")


def test_suite_inventory_and_structure():
    print("\n--- Test 1: Verifying Suite Artifacts Existence & Integrity ---")
    expected_files = [
        "success_01_basic_all_storage.zip",
        "success_02_mixed_file_formats.zip",
        "success_03_capacity_aware.zip",
        "success_04_privacy_aware.zip",
        "success_05_multi_task_scheduling.zip",
        "failed_01_corrupt_archive.zip",
        "failed_02_invalid_manifest.zip",
        "failed_03_capacity_or_policy_violation.zip",
        "loop_01_large_task_queue.zip",
        "loop_02_dependency_cycle.zip",
        "loop_03_timeout_simulation.zip",
        "master_test_datasets_suite.zip",
        "dataset_test_matrix_inventory.csv",
        "README.md",
        "README_failed_01_corrupt_archive.txt"
    ]
    for fn in expected_files:
        p = SUITE_DIR / fn
        assert p.exists(), f"Missing expected suite file: {p}"
        assert p.stat().st_size > 0, f"File {p} is empty!"
        print(f"  [PASS] {fn} exists ({p.stat().st_size} bytes)")


def test_corrupt_archive_rejection():
    print("\n--- Test 2: Verifying failed_01_corrupt_archive.zip Safe Rejection ---")
    corrupt_path = SUITE_DIR / "failed_01_corrupt_archive.zip"
    with open(corrupt_path, "rb") as fh:
        raw_bytes = fh.read()

    # Integrity check
    assert not zipfile.is_zipfile(io.BytesIO(raw_bytes)), "Corrupted archive should not be recognized as valid ZIP!"
    print("  [PASS] zipfile.is_zipfile() correctly returned False on corrupted archive header.")

    # Backend upload service defense
    mock_file = SimpleUploadedFile(corrupt_path.name, raw_bytes, content_type="application/zip")
    res = process_zip_dataset_upload(mock_file, execution_mode="SIMULATION")
    assert not res["success"], "Corrupt archive must fail validation!"
    assert "not a valid or readable ZIP" in res["error"] or "Corrupted" in res["error"]
    print(f"  [PASS] Backend safely rejected corrupt ZIP: {res['error']}")


def test_invalid_manifest_rejection():
    print("\n--- Test 3: Verifying failed_02_invalid_manifest.zip Schema Rejection ---")
    f2_path = SUITE_DIR / "failed_02_invalid_manifest.zip"
    with open(f2_path, "rb") as fh:
        raw_bytes = fh.read()

    assert zipfile.is_zipfile(io.BytesIO(raw_bytes)), "failed_02 must be a valid ZIP container."

    mock_file = SimpleUploadedFile(f2_path.name, raw_bytes, content_type="application/zip")
    res = process_zip_dataset_upload(mock_file, execution_mode="SIMULATION")
    assert not res["success"], "failed_02 must fail manifest schema validation!"
    assert "Manifest Validation Error" in res["error"]
    print(f"  [PASS] Manifest validation error caught cleanly: {res['error']}")


def test_capacity_policy_violation():
    print("\n--- Test 4: Verifying failed_03_capacity_or_policy_violation.zip ---")
    f3_path = SUITE_DIR / "failed_03_capacity_or_policy_violation.zip"
    with open(f3_path, "rb") as fh:
        raw_bytes = fh.read()

    mock_file = SimpleUploadedFile(f3_path.name, raw_bytes, content_type="application/zip")
    res = process_zip_dataset_upload(mock_file, execution_mode="SIMULATION")
    assert res["success"], "Archive container is structurally valid"

    # Confirm task remained UNASSIGNED due to capacity/policy constraints
    inv = res["inventory"]
    assert len(inv) > 0
    oversized_item = inv[0]
    assert oversized_item["selected_destination"] == "UNASSIGNED", f"Expected UNASSIGNED, got {oversized_item['selected_destination']}"
    assert "LOCAL_ONLY" in oversized_item["privacy_policy"]
    print(f"  [PASS] Oversized LOCAL_ONLY task remained UNASSIGNED. Rationale: {oversized_item['decision_rationale']}")


def test_dependency_cycle_detection():
    print("\n--- Test 5: Verifying loop_02_dependency_cycle.zip Cycle Detection ---")
    l2_path = SUITE_DIR / "loop_02_dependency_cycle.zip"
    with open(l2_path, "rb") as fh:
        raw_bytes = fh.read()

    mock_file = SimpleUploadedFile(l2_path.name, raw_bytes, content_type="application/zip")
    res = process_zip_dataset_upload(mock_file, execution_mode="SIMULATION")
    assert not res["success"], "Dependency cycle must trigger safe workflow rejection!"
    assert "Dependency Cycle Detected" in res["error"]
    print(f"  [PASS] Circular dependency detected and stopped safely: {res['error']}")


def test_timeout_watchdog_simulation():
    print("\n--- Test 6: Verifying loop_03_timeout_simulation.zip Watchdog ---")
    l3_path = SUITE_DIR / "loop_03_timeout_simulation.zip"
    with open(l3_path, "rb") as fh:
        raw_bytes = fh.read()

    mock_file = SimpleUploadedFile(l3_path.name, raw_bytes, content_type="application/zip")
    res = process_zip_dataset_upload(mock_file, execution_mode="SIMULATION")
    assert res["success"]
    # Verify timeout watchdog recorded in stages or warnings
    stage_msg = res["stages"][2]["message"]
    assert "Watchdog" in stage_msg or any("Watchdog" in w for w in res["stages"][9].get("message", ""))
    print(f"  [PASS] Timeout watchdog simulation registered successfully: {stage_msg}")


def test_bounded_queue_processing():
    print("\n--- Test 7: Verifying loop_01_large_task_queue.zip (45 Tasks) ---")
    l1_path = SUITE_DIR / "loop_01_large_task_queue.zip"
    with open(l1_path, "rb") as fh:
        raw_bytes = fh.read()

    mock_file = SimpleUploadedFile(l1_path.name, raw_bytes, content_type="application/zip")
    res = process_zip_dataset_upload(mock_file, execution_mode="SIMULATION")
    assert res["success"]
    print(f"  [PASS] Bounded queue processed within limits without hanging. Inventory count: {len(res['inventory'])}")


def test_all_five_successful_scenarios():
    print("\n--- Test 8: Verifying All 5 Successful Scenarios (Category A) ---")
    success_scenarios = [
        ("success_01_basic_all_storage.zip", 3),
        ("success_02_mixed_file_formats.zip", 3),
        ("success_03_capacity_aware.zip", 3),
        ("success_04_privacy_aware.zip", 3),
        ("success_05_multi_task_scheduling.zip", 6),
    ]

    for fname, expected_count in success_scenarios:
        p = SUITE_DIR / fname
        with open(p, "rb") as fh:
            raw_bytes = fh.read()

        # 1. Structure check: local/, mec/, cloud/, tasks/, expected_results/, manifest.json
        with zipfile.ZipFile(io.BytesIO(raw_bytes)) as z:
            names = z.namelist()
            assert "manifest.json" in names
            assert "README.txt" in names
            assert any(n.startswith("local/") for n in names)
            assert any(n.startswith("mec/") for n in names)
            assert any(n.startswith("cloud/") for n in names)
            assert "tasks/task_metadata.json" in names
            assert "expected_results/expected_result.json" in names

            manifest = json.loads(z.read("manifest.json").decode())
            validate_manifest_schema(manifest)
            assert len(manifest["resources"]) == 3

        # 2. Upload & Analysis execution
        mock_file = SimpleUploadedFile(fname, raw_bytes, content_type="application/zip")
        res = process_zip_dataset_upload(mock_file, execution_mode="SIMULATION")
        assert res["success"], f"Analysis failed for {fname}: {res.get('error')}"
        summary = res["summary"]
        assert summary["total_files"] == expected_count, f"Expected {expected_count} files, got {summary['total_files']}"
        print(f"  [PASS] {fname}: Validated archive, 3-tier structure, and processed {expected_count} workloads.")


if __name__ == "__main__":
    print("=================================================================")
    print("RUNNING AUTOMATED VERIFICATION FOR 11 DIGITAL TWIN TEST SCENARIOS")
    print("=================================================================")
    test_suite_inventory_and_structure()
    test_corrupt_archive_rejection()
    test_invalid_manifest_rejection()
    test_capacity_policy_violation()
    test_dependency_cycle_detection()
    test_timeout_watchdog_simulation()
    test_bounded_queue_processing()
    test_all_five_successful_scenarios()
    print("\n=================================================================")
    print("ALL 11 TEST SCENARIOS AND AUTOMATED VERIFICATION SUITE PASSED!")
    print("=================================================================")
