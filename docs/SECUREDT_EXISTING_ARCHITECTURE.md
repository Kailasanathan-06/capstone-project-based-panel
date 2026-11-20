# SecureDT Existing Architecture (Phase 1 Audit)

**Scope:** Current implementation audit of this repository (branch `feature/hospital-workload-extension`, HEAD `38aff2d`) against SecureDT 2.0 goals. This document describes *as-is* architecture; it does not propose unapproved redesign.

## 1. Project Overview
SecureDT is a Django-based research/testbed platform for **privacy-aware, policy-constrained task scheduling and dataset/workload management** across **Local (workstation), MEC (edge agent), and Cloud (simulated/emulated tier)** with a **Digital Twin** view, security simulation/monitoring, storage tiering, analytics, and reporting.

Primary stated domain scenario: hospital/clinical workload evaluation (14 workload scenarios, 30 ZIP test cases per existing docs/assets) to demonstrate placement, security, and resilience behaviors.

## 2. Technology Stack & Runtime
- **Language/Framework:** Python, Django >= 5.2,<6.0 (`requirements.txt`, `manage.py`, `securedt/settings.py`)
- **APIs/UI:** Django views/templates + Django REST Framework; `corsheaders`; `channels`/`daphne` included in dependencies/settings
- **Database:** SQLite default `db.sqlite3`; optional MySQL via env (`DB_ENGINE=mysql`, `DB_*`) (`securedt/settings.py`)
- **Config:** `.env` loading in settings (`DJANGO_SECRET_KEY`/`SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`)
- **Core libs:** `psutil`, `numpy`, `pandas`, `scikit-learn`, `scipy`, `Pillow`, `scikit-image`, `medmnist`, `reportlab`/`fpdf2`, `pytest`, `requests` (`requirements.txt`)
- **Repo root config:** `securedt/settings.py`, `securedt/urls.py`, `config.py`

## 3. Django Applications & Responsibilities
Registered apps (`securedt/settings.py`): `mec_manager`, `tasks`, `cloud`, `digital_twin`, `analytics`, `datasets` (+ DRF/auth/cors).

| App | Primary responsibility (as implemented) | Key modules |
|---|---|---|
| `datasets` | Dataset/upload metadata, 10-stage ZIP ingest/analysis pipeline UI+APIs, reports, storage allocation views, dashboard/task history pages, hospital workload scenario metadata | `datasets/models.py`, `datasets/views_pages.py`, `datasets/urls.py` |
| `tasks` | Task lifecycle, queue/history, GA/baseline dispatch orchestration, task execution endpoints, benchmark APIs | `tasks/models.py`, `tasks/services.py`, `tasks/views.py`, `tasks/urls.py` |
| `mec_manager` | MEC agent registration/pairing, token auth, heartbeat/telemetry, online/offline/revocation, task pull/report endpoints | `mec_manager/models.py`, `mec_manager/services.py`, `mec_manager/views.py`, `mec_manager/urls.py` |
| `digital_twin` | Digital twin state APIs, attack/mitigation/quarantine, storage simulation, security overview, experiment compare/export | `digital_twin/views.py`, `digital_twin/urls.py`, `engine/digital_twin.py` |
| `analytics` | Aggregated metrics (MEC/task/energy/security/cloud), AI status, benchmark, data flow | `analytics/views.py`, `analytics/urls.py` |
| `cloud` | Cloud/Drive file metadata, upload/download/status/folders/records APIs (with simulation/fallback behavior) | `cloud/models.py`, `cloud/views.py`, `cloud/urls.py`, `cloud/storage_manager.py` |

## 4. Core Engine Modules (`engine/`)
| Module | Role (as implemented) |
|---|---|
| `engine/genetic_algorithm.py` | Real GA optimizer: chromosome = per-task resource index; tournament selection, single-point crossover, per-gene mutation, elitism; fitness `w1*latency + w2*energy + w3*privacy_loss + w4*security_risk + deadline_penalty`; filters ineligible/offline candidates; blocked/unassignable represented as `BLOCKED`/`-1` |
| `engine/scheduler.py` | Scheduler facade + baselines (`round_robin`, `first_fit`, `random`, `greedy`, `privacy_aware`) and `proposed_ga_schedule`; shared cost/evaluation, policy-eligible candidate filtering via `PolicyEngine`, metrics aggregation, `run_all_baselines` |
| `engine/policy_engine.py` | Hard placement/dispatch constraints: policies `LOCAL_ONLY`, `TRUSTED_EDGE`, `CLOUD_ALLOWED`; availability/online/stale checks; memory/workload support checks; dispatch validation |
| `engine/digital_twin.py` | Virtual resource mirror: `LOCAL` measured via `psutil` (`MEASURED_HARDWARE`), MEC from DB/heartbeats with stale detection (`MEASURED_HEARTBEAT`), `CLOUD` explicitly simulated (`SIMULATED_CLOUD`); tracks CPU/memory/latency/energy/trust/risk/availability/tasks/status; attack/quarantine state updates |
| `engine/dataset_analysis_service.py` | 10-stage ZIP upload/analysis pipeline (upload/validation/inventory/feature extraction/resource status/privacy-security/scheduling/allocation/storage/report) with ZIP safety checks (path traversal, executables, decompression/limits handling), SHA-256, policy-aware eligibility/allocation, report persistence/export helpers; **upload allocation path uses deterministic heuristic scoring** (`run_ai_scheduler_allocation`) not the GA class |
| `engine/storage_manager.py` | 3-destination storage management: `LOCAL_STORAGE` (50 GB), `MEC_STORAGE` (200 GB), `CLOUD_STORAGE` (1000 GB, emulator-flagged); directories outside webroot, SHA-256 verification, privacy boundary enforcement, idempotent replication, audit on violations, inventory helpers |
| `engine/hospital_workloads.py` | Hospital workload scenario definitions/registration and workload/security-event processing helpers (14-scenario context; includes success/error/security/timeout categories) |
| `engine/ai_engine.py` | Risk classification using scikit-learn `RandomForestClassifier` (labels {safe, warning, high_risk}) with dataset train/load/persist and rule-based fallback; optional cached Groq LLM explanation path (config-gated) |
| `engine/risk_engine.py` | Normalized security risk computation `[0,1]` from attack/severity/privacy/trust/workload/exposure and risk bands |
| `engine/attack_simulator.py` | Virtual/in-process attack simulation on Digital Twin state (multiple attack types, kill-chain progression, detection/evasion/persistence effects); no real network/device interaction |
| `engine/security_monitor.py` | Security event/alert aggregation, threat-level derivation, overview payloads |
| `engine/benchmark_runner.py` | Comparative benchmark runner over hospital tasks for algorithms {proposed_ga, round_robin, first_fit, random, greedy, privacy_aware}; records `ExperimentRun`/`SchedulingDecision`, computes metrics, exports 14-column CSV |
| `engine/task_manager.py`, `engine/telemetry.py`, `engine/image_processor.py` | Task/telemetry/processing support utilities (present; role per module) |

## 5. Data Model Highlights
- **`datasets` models (`datasets/models.py`):** `Dataset` metadata, `MedicalDatasetMetadata/Sample`, `WorkloadScenario` (14-scenario metadata incl. policy/resources/deadlines), `DatasetVersion`, `StorageDestination`, `DatasetStorageReplica`, `SecurityAuditEvent`, `DatasetUpload`, `DatasetInventoryItem`, `DatasetAnalysisReport` (pipeline artifacts/reports/replication/audit).
- **`tasks` models (`tasks/models.py`):** `Task` (lifecycle statuses CREATED..RETRYING incl. PENDING/QUEUED/ASSIGNED/RUNNING/COMPLETED/FAILED/TIMED_OUT/BLOCKED/REJECTED, privacy policy, workload fields, assignment/tier/MEC, timing/checksums/results, scenario/error/timeout/retry metadata), `TaskQueueHistory`, `SchedulingDecision`, `ExperimentRun`.
- **`mec_manager` models (`mec_manager/models.py`):** `MECAgent` (unique `device_id` MEC-XXX, auth token, pairing/registration, online/revoked, diagnostics incl. last IP as non-identity), `PairingCode` (one-time), `Heartbeat` (telemetry history: CPU/RAM/disk/storage/latency/energy/task/load/host info).
- **`cloud` models (`cloud/models.py`):** `GoogleDriveFile`, `CloudFolder`, `CloudUploadRecord` metadata/audit.

## 6. Primary Workflows

### 6.1 Task Scheduling & Execution
1. Tasks created/queued via API/UI (`tasks/views.py`, `Task` model).
2. `tasks/services.py:run_ga_dispatch` loads queued/pending tasks, gets Digital Twin states, runs selected algorithm via `engine/scheduler.py` (GA or baselines) which enforces eligibility through `PolicyEngine` and GA constraints.
3. Assignments dispatched to **LOCAL** (`execute_task_locally`), **MEC** (assigned to online non-revoked agent; polled/reported via `mec_manager` task endpoints), or **CLOUD** (`execute_task_cloud_simulation`, explicitly simulated tier).
4. Offline/revoked MEC handling requeues assigned/running tasks (`tasks.services.requeue_tasks_with_offline_agents`, `Task.requeue_if_offline`, `mec_manager.services.requeue_orphaned_tasks`).

### 6.2 Dataset ZIP Upload, Analysis, Allocation, Storage & Reporting
1. Upload via `datasets/views_pages.py` (`upload_dataset_view/api`, demo/sample loaders) -> `engine/dataset_analysis_service.process_zip_dataset_upload`.
2. Pipeline performs staged validation/safety checks, inventory/feature/privacy analysis, resource/twin snapshot, policy-aware destination selection and **deterministic heuristic allocation scoring** (`run_ai_scheduler_allocation`), physical replication/verification through `engine/storage_manager.py`, and persists `DatasetUpload`/`DatasetInventoryItem`/`DatasetAnalysisReport`.
3. Reports viewed/exported (JSON/CSV) via datasets pages/APIs; storage allocation and dashboard surfaces reflect DB state.

### 6.3 MEC Agent Lifecycle
1. One-time registration with pairing code (`PairingCode`) issues device ID/token (`mec_manager.services.register_mec`).
2. Authenticated heartbeats update telemetry and online/last-seen (`process_heartbeat`); online state derived by timeout (`refresh_mec_status`, configurable timeout) not single miss.
3. Device listing/detail, revoke/unrevoke, connected status/ping, next-task/report-result endpoints in `mec_manager/views.py`.

### 6.4 Digital Twin, Security & Analytics
1. `DigitalTwin` snapshots combine measured local hardware, measured (possibly stale) MEC heartbeats, and simulated cloud for scheduling/UI.
2. Virtual attacks/quarantine/mitigation via `engine/attack_simulator.py`, risk via `engine/risk_engine.py`, monitoring/overview via `engine/security_monitor.py` and digital twin/security APIs.
3. Analytics APIs aggregate DB/twin/heartbeat/task/cloud metrics; benchmark endpoints run comparative experiments and CSV export (`engine/benchmark_runner.py`, `tasks/views.py` benchmark routes, `analytics/views.py`, `digital_twin/views.py compare`).

## 7. UI Pages / Entry Points (observed)
Routed through `securedt/urls.py` and `datasets/views_pages.py`: dashboard, upload dataset, digital twin, storage allocation, dataset reports/report detail/CSV download, task history; plus REST APIs under `/api/tasks/`, `/api/mec/`, `/api/analytics/`, `/api/digital-twin/`, `/api/cloud/` and dataset-related APIs.

## 8. Assets & Documentation
- `sample_upload_datasets/`: 30 scenario ZIPs/suite/inventory artifacts for success/error/timeout cases.
- `docs/`: extensive guides, reports, and `base paper.pdf`; Phase 1 audit outputs added by this audit.
- `paper/`: IEEE-style paper PDF, generators, figures (separate from runtime system).
- `tests/`: automated tests present (scope to be validated in later phases).
