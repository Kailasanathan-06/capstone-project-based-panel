# Intelligent and Secure Task Scheduling for Digital Twin-Enabled Edge–Cloud Networks

An advanced academic research platform and edge-computing testbed that integrates **genuine hospital-workload processing**, a **live multi-tier Digital Twin**, and a **security-aware multi-objective Genetic Algorithm (GA)** scheduler evaluated against 5 baseline schedulers across Local, MEC, and Cloud network infrastructure.

> **Demonstration Scenario:** Hospital-related clinical workloads are employed as a realistic, high-assurance evaluation scenario to demonstrate privacy-preserving task offloading, strict placement policy enforcement, defensive cybersecurity monitoring, and timeout resilience.

---

## 1. System Architecture & End-to-End Workflow

```
+---------------------------------------------------------------------------------------------------------+
|                                    EDGE–CLOUD NETWORK ARCHITECTURE                                      |
+---------------------------------------------------------------------------------------------------------+
                                                     │
                                 [Workload Submission & Triage]
                    14 Real Hospital Workloads (Images, EHRs, Labs, Documents, Appointments)
                                                     │
                                                     ▼
+---------------------------------------------------------------------------------------------------------+
|                           POLICY ENGINE: PRIVACY & FEASIBILITY PLACEMENT                                |
|  - LOCAL_ONLY     : Strictly restricted to Hospital Workstation (Zero offloading permitted)            |
|  - TRUSTED_EDGE   : Eligible for Workstation or Authenticated, Non-Stale, Online MEC Nodes              |
|  - CLOUD_ALLOWED  : Eligible for Workstation, MEC Nodes, or Simulated Cloud Infrastructure               |
+---------------------------------------------------------------------------------------------------------+
                                                     │
                                                     ▼
+---------------------------------------------------------------------------------------------------------+
|                             DIGITAL TWIN: REAL-TIME VIRTUAL MIRROR                                      |
|  - LOCAL Workstation: Live hardware CPU & RAM metrics via `psutil` (MEASURED_HARDWARE)                  |
|  - MEC Edge Nodes   : Live telemetry via periodic heartbeats with 35s stale-timeout (MEASURED_HEARTBEAT) |
|  - CLOUD Tier       : High-capacity simulated execution tier with WAN latency model (SIMULATED_CLOUD)   |
+---------------------------------------------------------------------------------------------------------+
                                                     │
                                                     ▼
+---------------------------------------------------------------------------------------------------------+
|                     MULTI-OBJECTIVE GENETIC ALGORITHM (GA) & BASELINE SCHEDULERS                        |
|  Minimise: Fitness = w1*Latency + w2*Energy + w3*Privacy_Loss + w4*Security_Risk + Strict_Penalty       |
|  Strict Ineligibility: Unassignable tasks mapped to "BLOCKED" gene (-1). Zero Policy Violations!        |
|  Baselines: Round Robin | First Fit | Random | Greedy (Latency-First) | Privacy-Aware                   |
+---------------------------------------------------------------------------------------------------------+
                                                     │
                    ┌────────────────────────────────┼────────────────────────────────┐
                    │                                │                                │
                    ▼                                ▼                                ▼
         [LOCAL WORKSTATION]                  [MEC EDGE AGENT]               [SIMULATED CLOUD]
         - Direct Execution                  - Autonomous Poll               - WAN Transfer (170ms)
         - LOCAL_STORAGE (50 GB)             - MEC_STORAGE (200 GB)          - CLOUD_STORAGE (1000 GB)
         - Confidential Data                 - Authenticated MEC Tasks       - De-identified Workloads
                    │                                │                                │
                    └────────────────────────────────┼────────────────────────────────┘
                                                     │
                                                     ▼
+---------------------------------------------------------------------------------------------------------+
|                         GENUINE HOSPITAL WORKLOAD PROCESSING PIPELINE                                   |
|  1. Preprocessing & Normalization: CLAHE contrast equalization, 224x224 standardization, SHA-256        |
|  2. Clinical EHR Scoring: NEWS2 National Early Warning Score evaluation with vitals validation          |
|  3. Lab Panels: Comprehensive metabolic & CBC panel reference check, flagging, and severity indexing    |
|  4. Medical Document Metadata: ICD-10 diagnostic code tagging and cryptographic content signature       |
|  5. Outpatient Appointment Batch: Constraint satisfaction, time conflict elimination, queue ordering     |
|  6. Defensive Security: Recursive secret sanitization, rate-limiting, and privacy violation blockage    |
|  7. Watchdogs & Timers: Execution watchdog timers, dropped-worker reclamation, exponential backoff     |
+---------------------------------------------------------------------------------------------------------+
                                                     │
                                                     ▼
+---------------------------------------------------------------------------------------------------------+
|                         EXPERIMENT BENCHMARKING & 14-COLUMN CSV EXPORT                                  |
|  - Schedulers Evaluated: Proposed GA, Round Robin, First Fit, Random, Greedy, Privacy-Aware             |
|  - Metrics: Makespan (s), Latency (ms), Energy (J), Violations (0), Blocked, Throughput, Utilization    |
|  - 14-Column RFC-Compliant CSV Streaming: Direct export from REST API and Web UI                         |
+---------------------------------------------------------------------------------------------------------+
```

---

## 2. The 14 Hospital Workload Scenarios

The platform implements 14 genuine clinical workloads across 4 test categories. Every workload executes genuine computation with high-resolution timing, input/output SHA-256 checksums, and explicit policy validation (zero placeholders or simulated outcomes):

### Category 1: Success Workloads (5 Cases)
| Scenario ID | Name | Policy | Expected Status | Description & Genuine Output |
| :--- | :--- | :--- | :--- | :--- |
| **`HOSP-SUCCESS-01`** | Medical Image Preprocessing | `TRUSTED_EDGE` | `COMPLETED` | CLAHE adaptive contrast equalization, 224x224 Lanczos resizing, input & output SHA-256 checksums. |
| **`HOSP-SUCCESS-02`** | Patient Clinical Record Processing | `LOCAL_ONLY` | `COMPLETED` | NEWS2 National Early Warning Score calculation, vital signs risk stratification, and PHI de-identification. |
| **`HOSP-SUCCESS-03`** | Laboratory Metabolic & CBC Panel | `TRUSTED_EDGE` | `COMPLETED` | Reference range validation (glucose, creatinine, WBC, platelets), abnormal flagging, and clinical severity index. |
| **`HOSP-SUCCESS-04`** | Medical Document Metadata Extraction | `TRUSTED_EDGE` | `COMPLETED` | Entity tagging, ICD-10 diagnostic code extraction (e.g., J18.9 Pneumonia, E11 Type 2 Diabetes), SHA-256 signature. |
| **`HOSP-SUCCESS-05`** | Outpatient Appointment Scheduling | `CLOUD_ALLOWED` | `COMPLETED` | Batch scheduling, room and physician conflict resolution, urgency triage ordering, and slot allocation. |

### Category 2: Controlled Error Workloads (3 Cases)
| Scenario ID | Name | Policy | Expected Status | Error Code | Behavior |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`HOSP-ERROR-01`** | Malformed / Corrupted Image File | `TRUSTED_EDGE` | `FAILED` | `ERR_MALFORMED_INPUT` | Zero-byte or truncated header detected; non-retryable execution failure. |
| **`HOSP-ERROR-02`** | Incomplete Patient Record | `LOCAL_ONLY` | `REJECTED` | `ERR_MISSING_MANDATORY_FIELDS` | Pre-dispatch validation rejects record missing mandatory vitals without queuing. |
| **`HOSP-ERROR-03`** | Unsupported Record Format | `TRUSTED_EDGE` | `REJECTED` | `ERR_UNSUPPORTED_FORMAT` | Schema mismatch or unknown serialization rejected before scheduling. |

### Category 3: Defensive Security Scenarios (3 Cases)
| Scenario ID | Name | Policy | Expected Status | Event Type | Defensive Protection |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`HOSP-SEC-01`** | Unauthorized Task Submission | `LOCAL_ONLY` | `REJECTED` | `UNAUTHORIZED_TASK_SUBMISSION` | Unauthenticated submission rejected with HTTP 403; security audit recorded with redacted tokens. |
| **`HOSP-SEC-02`** | Invalid/Expired MEC Credentials | `TRUSTED_EDGE` | `REJECTED` | `INVALID_MEC_AUTH` | Rogue or expired token rejected; security audit recorded with sanitized payload. |
| **`HOSP-SEC-03`** | Unauthorized Cloud Replication | `LOCAL_ONLY` | `BLOCKED` | `PRIVACY_POLICY_VIOLATION` | Attempt to replicate `LOCAL_ONLY` data to Cloud is blocked by policy engine with audit event. |

### Category 4: Timeout & Retry Scenarios (3 Cases)
| Scenario ID | Name | Policy | Expected Status | Error Code | Fault-Tolerance Mechanism |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`HOSP-TIME-01`** | Workload Exceeding Time Limit | `TRUSTED_EDGE` | `TIMED_OUT` | `ERR_EXECUTION_TIMEOUT` | Precision watchdog timer aborts execution, frees CPU/RAM resources, status `TIMED_OUT`. |
| **`HOSP-TIME-02`** | Unresponsive Worker / Dropped Node | `TRUSTED_EDGE` | `TIMED_OUT` | `ERR_WORKER_UNRESPONSIVE` | Supervisor reclaims task, detaches offline MEC, status `TIMED_OUT`. |
| **`HOSP-TIME-03`** | Transient Failure Retry Exhaustion | `TRUSTED_EDGE` | `FAILED` | `ERR_MAX_RETRIES_EXCEEDED` | Exponential backoff retries strictly halt when `retry_count >= max_retries` (zero infinite loops). |

---

## 3. Verified 3-Tier Storage & Physical Replication

Data is managed across 3 verified physical storage tiers stored outside the public webroot (`data_storage/`):

1. **`LOCAL_STORAGE` (50 GB Capacity):**
   - Placement Policy: Strictly `LOCAL_ONLY`
   - Path: `data_storage/local_storage/`
   - Use Case: Highly confidential patient scans and identifiable medical records.
2. **`MEC_STORAGE` (200 GB Capacity):**
   - Placement Policy: `TRUSTED_EDGE`
   - Path: `data_storage/mec_storage/`
   - Use Case: De-identified hospital ward scans and edge-cached laboratory reports.
3. **`CLOUD_STORAGE` (1000 GB Capacity):**
   - Placement Policy: `CLOUD_ALLOWED`
   - Path: `data_storage/cloud_storage/`
   - Use Case: Public medical benchmarks and de-identified archives.

### Cryptographic Verification & Auditability:
- Every replicated file is physically copied and verified via SHA-256 cryptographic checksum matching.
- Re-transfers of unmodified files are skipped via idempotent hash checks.
- Audit sweeps verify on-disk replica health via `POST /api/datasets/storage/verify/`.
- Complete inventory export available via `GET /api/datasets/storage/export-csv/`.

---

## 4. Multi-Objective Scheduling & Comparative Benchmark

The scheduling engine compares the **Proposed Multi-Objective Genetic Algorithm (GA)** against **5 baseline schedulers** on identical hospital workloads:

1. **Proposed Genetic Algorithm (GA):** Tournament selection, single-point crossover, candidate-valid mutation, and multi-objective fitness balancing latency, energy, privacy loss, and security risk with strict ineligibility penalties.
2. **Round Robin:** Cycles tasks across policy-eligible nodes.
3. **First Fit:** Assigns each task to the first policy-eligible resource in hierarchy.
4. **Random:** Uniform random selection among policy-eligible resources.
5. **Greedy (Latency-First):** Minimizes predicted processing and transfer latency.
6. **Privacy-Aware:** Minimizes privacy loss with latency tie-breaking.

### Strict Policy Enforcement:
- Unassignable tasks receive a `"BLOCKED"` gene (`-1`) with high fitness penalty.
- **Zero Policy Violations:** All 6 algorithms achieve `policy_violations == 0` and 100% privacy compliance.
- Infeasible tasks are accounted for cleanly under `blocked_tasks` without throwing exceptions.

### 14-Column Benchmark CSV Export:
Exports RFC-compliant CSV containing:
`Algorithm, Tasks Assigned, Tasks Blocked, Policy Violations, Makespan (s), Average Latency (s), Throughput (tasks/s), Local Resource Utilization (%), MEC Resource Utilization (%), Cloud Resource Utilization (%), Energy Consumption (J), Scheduling Overhead (ms), Privacy Compliance Rate (%), Timestamp`

---

## 5. Management Commands

### 1. List Registered Hospital Workloads & Storage Tiers
```powershell
python manage.py list_hospital_datasets
```
Displays all 14 official workload scenarios, registered public datasets, and status of the 3 verified storage destinations.

### 2. Download / Register Benchmark Datasets
```powershell
python manage.py download_hospital_datasets --skip-download
```
Registers metadata and versions for MedMNIST benchmark datasets without requiring live external network access.

### 3. Run Comparative Schedulers Benchmark
```powershell
python manage.py run_hospital_scheduler_benchmark --tasks-count 14 --population 30 --generations 20 --seed 42
```
Executes all 6 scheduling algorithms on the hospital workload, stores decisions and experiment run in the database, displays the summary comparison table, and generates a timestamped CSV export in `data_storage/benchmarks/`.

---

## 6. REST API Endpoints

### Hospital Workloads & Scenarios:
- `GET /api/datasets/scenarios/` — List all 14 registered hospital workload scenarios.
- `POST /api/datasets/scenarios/run/<scenario_id>/` — Execute a live, genuine workload run and return output, duration, and SHA-256 checksums.

### Storage & Replication:
- `GET /api/datasets/storage/destinations/` — List the 3 verified storage destinations, capacities, and usage.
- `GET /api/datasets/storage/replicas/` — List physical replicas, checksums, and verification status.
- `POST /api/datasets/storage/replicate/` — Trigger policy-verified replication between tiers.
- `GET /api/datasets/storage/export-csv/` — Download storage replica inventory CSV.
- `POST /api/datasets/storage/verify/` — Perform an audit sweep of on-disk replicas.

### Comparative Scheduler Benchmark:
- `GET /api/tasks/hospital-benchmark/summary/` — Retrieve the latest benchmark experiment run.
- `POST /api/tasks/hospital-benchmark/run/` — Execute a comparative benchmark across all 6 algorithms.
- `GET /api/tasks/hospital-benchmark/export-csv/` — Download 14-column comparative benchmark CSV.

---

## 7. Getting Started (Windows Execution)

### Prerequisites:
- Python 3.11, 3.12, or 3.13 on Windows 10/11
- Virtual environment (`venv`)

### Step 1: Install Dependencies
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Apply Database Migrations
```powershell
python manage.py migrate
```

### Step 3: Run the Development Server
```powershell
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` to access the SecureDT dashboard:
- **Hospital Workloads & Datasets Lab:** `http://127.0.0.1:8000/medical-dataset/`
- **Task Routing & Schedulers Benchmark:** `http://127.0.0.1:8000/task-routing/`
- **Security Monitor & Audit Trails:** `http://127.0.0.1:8000/security-monitor/`
- **MEC Infrastructure:** `http://127.0.0.1:8000/mec-infrastructure/`
- **Digital Twin:** `http://127.0.0.1:8000/digital-twin/`

---

## 8. Automated Test Suite

Run the complete self-contained test suite:
```powershell
python manage.py test tests -v 2
```
All **58 tests** complete with `OK` in under 30 seconds with zero regressions, zero failures, and zero external network or cloud credential dependencies.

---

## 9. Research Limitations & Disclaimer

> [!WARNING]
> **Academic Research Prototype Notice:**
> This software is an engineering and computer science research testbed for evaluating task scheduling, edge computing, Digital Twins, and privacy placement policies in edge–cloud networks.
> It is **NOT** a medical diagnostic device and has **NOT** been certified or approved by the FDA, CE, or any health authority for clinical decision-making or diagnosis.