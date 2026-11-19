# SecureDT — Digital Twin Edge–Cloud Master Test Dataset Suite

This suite contains **30 standardized ZIP test datasets** — 10 success, 10 failure, and 10 loop/timeout scenarios — for testing the project's dataset upload, validation, analysis, storage eligibility, task scheduling, failure handling, and timeout detection.

## Infrastructure Resources Represented
1. **Local Storage** (`LOCAL-01`): On-premises hospital workstation (HIPAA Tier-1 Vault, `LOCAL_ONLY` policy).
2. **MEC/Edge Storage** (`MEC-01`): Nearby trusted edge cluster (`TRUSTED_EDGE` policy, low-latency compute).
3. **Cloud Storage** (`CLOUD-01`): Central cloud repository (`CLOUD_ALLOWED` policy, large-capacity aggregate).

## Test Scenarios Overview

### Category A: Successful Datasets (10 archives)
| Filename | Test Purpose | Expected Outcome |
|---|---|---|
| `success_01_basic_all_storage.zip` | Valid data for Local, MEC, and Cloud | Analysis succeeds (3/3 assigned) |
| `success_02_mixed_file_formats.zip` | Valid supported CSV, JSON, and TXT samples | All formats parsed and analyzed |
| `success_03_capacity_aware.zip` | Different dataset sizes and resource capacities | Assignments respect capacity headroom |
| `success_04_privacy_aware.zip` | Different privacy policies across datasets | Only policy-permitted destinations are eligible |
| `success_05_multi_task_scheduling.zip` | 6 independent tasks across three resources | GA scheduler produces traceable decisions |
| `success_06_device_telemetry_stream.zip` | Telemetry, diagnostic inference, and health aggregate | Analysis succeeds (3/3 assigned) |
| `success_07_mixed_format_lab_records.zip` | Lab request CSV, pathology JSON, and clinical notes TXT | All formats parsed and allocated by tier |
| `success_08_ambulatory_care_workloads.zip` | Four-task scheduling with two edge diagnostic batches | Analysis succeeds (4/4 assigned) |
| `success_09_fhir_interoperability_batch.zip` | FHIR-style imaging bundle with consent governance | Analysis succeeds (3/3 assigned) |
| `success_10_pharmacy_inventory_sync.zip` | Controlled-drug, cold-chain, label, and supply-chain workloads | Analysis succeeds (4/4 assigned) |

### Category B: Failed Datasets (10 archives)
| Filename | Test Purpose | Expected Outcome |
|---|---|---|
| `failed_01_corrupt_archive.zip` | Invalid or truncated ZIP archive | Archive validation fails safely (HTTP 400) |
| `failed_02_invalid_manifest.zip` | Missing required fields or invalid manifest structure | Manifest validation fails with clear error |
| `failed_03_capacity_or_policy_violation.zip` | Tasks exceed capacity or violate privacy constraints | Invalid assignments rejected / unassigned |
| `failed_04_missing_resources_field.zip` | Manifest omits mandatory `resources` field | Schema validation fails cleanly |
| `failed_05_resources_wrong_type.zip` | `resources` declared as object instead of list | Schema validation rejects type mismatch |
| `failed_06_insufficient_resource_tiers.zip` | Only two resource tiers declared | Three-tier requirement enforced |
| `failed_07_malformed_manifest_json.zip` | Truncated JSON syntax in manifest | JSON parse error reported safely |
| `failed_08_disallowed_executable.zip` | Executable `.exe` payload in archive | Archive blocked by extension policy |
| `failed_09_path_traversal_entry.zip` | ZIP entry with `../` escape path | Path traversal defense rejects archive |
| `failed_10_decompression_limit.zip` | 280 MB expansion payload | Decompression bomb rejected by expansion cap |

### Category C: Loop and Timeout Datasets (10 archives)
| Filename | Test Purpose | Expected Outcome |
|---|---|---|
| `loop_01_large_task_queue.zip` | Large but bounded task queue (45 tasks) | Processing remains responsive within limits |
| `loop_02_dependency_cycle.zip` | Task dependency metadata contains a cycle | Cycle detected and rejected safely |
| `loop_03_timeout_simulation.zip` | Resource response exceeds test timeout | Times out safely, bounds retries |
| `loop_04_self_dependency_loop.zip` | Task depends on itself | One-node cycle detected and rejected |
| `loop_05_mutual_dependency_deadlock.zip` | Two tasks wait on each other | Mutual deadlock detected |
| `loop_06_five_node_dependency_cycle.zip` | Five-task closed dependency chain | Long cycle detected and rejected |
| `loop_07_edge_worker_watchdog.zip` | MEC worker exceeds 2-second watchdog | Timeout alert with 2 bounded retries |
| `loop_08_cloud_sync_retry_storm.zip` | Cloud sync latency far above timeout | Timeout alert with 5 bounded retries |
| `loop_09_retry_exhaustion_batch.zip` | Three timeout tasks with one retry each | All timeouts reported with bounded retries |
| `loop_10_cycle_and_timeout_mixed.zip` | Cycle combined with a timeout task | Cycle detected first; archive safely rejected |

## Internal Directory Structure
Every valid ZIP archive follows this structure:
```text
scenario_name.zip
├── manifest.json
├── README.txt
├── local/
│   ├── resource.json
│   └── dataset/
│       └── local_tasks.csv
├── mec/
│   ├── resource.json
│   └── dataset/
│       └── mec_tasks.csv
├── cloud/
│   ├── resource.json
│   └── dataset/
│       └── cloud_tasks.csv
├── tasks/
│   └── task_metadata.json
└── expected_results/
    └── expected_result.json
```

## How to Test
1. Open the SecureDT application in your browser: `http://127.0.0.1:8000/upload/`
2. Click **Choose Archive** and select any of the 30 scenario ZIP files (or pick from the quick preset dropdown).
3. Choose **Simulation Mode** or **Execution Mode** and click **Upload & Analyze Archive**.
4. Observe the real-time 10-stage analysis pipeline and verify the persistent report against `expected_results/expected_result.json`.
