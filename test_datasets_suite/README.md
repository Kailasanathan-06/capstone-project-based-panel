# SecureDT — Digital Twin Edge–Cloud Master Test Dataset Suite

This suite contains **11 standardized ZIP test datasets** for testing the project's dataset upload, validation, analysis, storage eligibility, task scheduling, failure handling, and timeout detection.

## Infrastructure Resources Represented
1. **Local Storage** (`LOCAL-01`): On-premises hospital workstation (HIPAA Tier-1 Vault, `LOCAL_ONLY` policy).
2. **MEC/Edge Storage** (`MEC-01`): Nearby trusted edge cluster (`TRUSTED_EDGE` policy, low-latency compute).
3. **Cloud Storage** (`CLOUD-01`): Central cloud repository (`CLOUD_ALLOWED` policy, large-capacity aggregate).

## Test Scenarios Overview

### Category A: Successful Datasets (5 archives)
| Filename | Test Purpose | Expected Outcome |
|---|---|---|
| `success_01_basic_all_storage.zip` | Valid data for Local, MEC, and Cloud | Analysis succeeds (3/3 assigned) |
| `success_02_mixed_file_formats.zip` | Valid supported CSV, JSON, and TXT samples | All formats parsed and analyzed |
| `success_03_capacity_aware.zip` | Different dataset sizes and resource capacities | Assignments respect capacity headroom |
| `success_04_privacy_aware.zip` | Different privacy policies across datasets | Only policy-permitted destinations are eligible |
| `success_05_multi_task_scheduling.zip` | 6 independent tasks across three resources | GA scheduler produces traceable decisions |

### Category B: Failed Datasets (3 archives)
| Filename | Test Purpose | Expected Outcome |
|---|---|---|
| `failed_01_corrupt_archive.zip` | Invalid or truncated ZIP archive | Archive validation fails safely (HTTP 400) |
| `failed_02_invalid_manifest.zip` | Missing required fields or invalid manifest structure | Manifest validation fails with clear error |
| `failed_03_capacity_or_policy_violation.zip` | Tasks exceed capacity or violate privacy constraints | Invalid assignments rejected / unassigned |

### Category C: Loop and Timeout Datasets (3 archives)
| Filename | Test Purpose | Expected Outcome |
|---|---|---|
| `loop_01_large_task_queue.zip` | Large but bounded task queue (45 tasks) | Processing remains responsive within limits |
| `loop_02_dependency_cycle.zip` | Task dependency metadata contains a cycle | Cycle detected and rejected safely |
| `loop_03_timeout_simulation.zip` | Resource response exceeds test timeout | Times out safely, bounds retries |

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
2. Click **Choose Archive** and select any of the 11 scenario ZIP files (or pick from the quick preset dropdown).
3. Choose **Simulation Mode** or **Execution Mode** and click **Upload & Analyze Archive**.
4. Observe the real-time 10-stage analysis pipeline and verify the persistent report against `expected_results/expected_result.json`.
