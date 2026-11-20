# SecureDT Code Audit (Phase 1)

**Audit date:** 2026-11-20 (repo state)  
**Branch/HEAD:** `feature/hospital-workload-extension` @ `38aff2d`  
**Method:** Static inspection of key modules, models, APIs, configuration, docs/assets. No runtime benchmark claims fabricated; no major code changes made.

## 1. Component Audit Matrix

| Component | Status | Evidence | Notes |
|---|---|---|---|
| Django project config & app wiring | **Fully implemented** | `securedt/settings.py`, `securedt/urls.py`, `config.py`, `requirements.txt` | SQLite default, optional MySQL env; DRF/cors/channels configured; `.env` secrets loading |
| Placement policy engine | **Fully implemented (core rules)** | `engine/policy_engine.py` (`PolicyEngine.get_eligible_resources`, `validate_dispatch`) | Enforces `LOCAL_ONLY/TRUSTED_EDGE/CLOUD_ALLOWED`, availability/online/stale, memory, supported workloads; explicit non-legal-compliance note in docstring |
| Genetic Algorithm optimizer | **Fully implemented** | `engine/genetic_algorithm.py` (`GeneticAlgorithm`, `optimize`, operators, fitness, blocked genes) | Real GA with policy-aware eligible indices, penalties, elitism/history; filters offline/ineligible before selection logic |
| Multi-algorithm scheduler (task path) | **Fully implemented** | `engine/scheduler.py` (`Scheduler`, baselines, `proposed_ga_schedule`, `run_all_baselines`, `_evaluate_solution`) | Consistent cost model; policy-filtered candidates; computes latency/energy/privacy/risk/deadline/blocked/compliance metrics |
| Task dispatch & execution (LOCAL/MEC/CLOUD) | **Partially implemented** | `tasks/services.py` (`build_task_dict`, `run_ga_dispatch`, `execute_task_locally`, `execute_task_cloud_simulation`), `tasks/models.py`, `tasks/views.py` | LOCAL/MEC/CLOUD dispatch paths present; LOCAL does real processing/timing/checksum logic for supported workloads; CLOUD path explicitly simulated; end-to-end MEC remote execution depends on agent behavior/integration |
| Task model/lifecycle/history/experiments | **Fully implemented (data model)** | `tasks/models.py` (`Task`, `TaskQueueHistory`, `SchedulingDecision`, `ExperimentRun`) | Rich statuses, policy/tier/node, scenario/error/timeout/retry, timing/checksums, decision/experiment records; requeue-if-offline helpers |
| Digital Twin (resource modeling) | **Partially implemented / mixed measured+simulated** | `engine/digital_twin.py` (`DigitalTwin`, `ResourceState`) | `LOCAL` = `MEASURED_HARDWARE` via `psutil`; MEC = `MEASURED_HEARTBEAT` with stale detection; `CLOUD` = `SIMULATED_CLOUD`; natural drift/tick for simulated aspects |
| MEC registration, auth, heartbeat, lifecycle | **Fully implemented** | `mec_manager/models.py`, `mec_manager/services.py` (`register_mec`, `process_heartbeat`, `refresh_mec_status`, `requeue_orphaned_tasks`), `mec_manager/views.py` | One-time pairing, token+device auth, timeout-based online/offline, revoke/unrevoke, task pull/report endpoints; IP treated as diagnostic |
| 10-stage dataset ZIP analysis pipeline | **Partially implemented** | `engine/dataset_analysis_service.py` (`process_zip_dataset_upload`, inventory/validation/storage/report helpers), `datasets/views_pages.py` | Structured staged pipeline with ZIP safety checks, SHA-256, policy-aware flow and report persistence; stage completeness/robustness across all 30 cases requires runtime validation (deferred) |
| Dataset upload allocation decision (pipeline path) | **Implemented but methodologically inconsistent** | `engine/dataset_analysis_service.py` (`run_ai_scheduler_allocation`, report labels "Genetic Algorithm & Multi-Constraint Policy Engine") | Uses **deterministic multi-objective heuristic scoring**, not `engine/genetic_algorithm.py`; labeling can overstate GA use in this path |
| Tri-tier storage manager & replication | **Fully implemented (core) with emulator aspects** | `engine/storage_manager.py` (`STORAGE_DESTINATION_SPECS`, `ensure_storage_destinations_initialized`, `replicate_file`, SHA-256) | LOCAL/MEC/CLOUD 50/200/1000 GB, outside-webroot dirs, verification, idempotency, privacy-boundary blocking/audit; CLOUD is emulator-flagged tier |
| Hospital workload scenarios & processing | **Partially implemented** | `engine/hospital_workloads.py` (scenario defs/handlers observed), `datasets/models.py` (`WorkloadScenario`), `sample_upload_datasets/` | 14-scenario structure and 30 ZIP assets present; genuine processing/defensive behavior claims in docs/README need case-by-case runtime verification |
| AI risk classification (RF) | **Partially implemented** | `engine/ai_engine.py` (`AIEngine`, train/load/predict, rule-based fallback) | Offline/batch-style RF risk labels {safe,warning,high_risk}; not adaptive online trust learning; optional Groq explanation is config-gated/cached |
| Risk computation model | **Implemented (model-based)** | `engine/risk_engine.py` (`RiskEngine.compute_risk`, `risk_level`) | Continuous normalized risk `[0,1]` from configured factors; model-based/simulated inputs in practice |
| Attack simulation & security monitoring | **Implemented (simulation-only)** | `engine/attack_simulator.py`, `engine/security_monitor.py`, `digital_twin/views.py` security endpoints | Virtual in-process perturbations/kill-chain/logging/threat overview; no real network attacks or host compromise |
| Analytics & dashboard APIs | **Partially implemented** | `analytics/views.py`, `datasets/views_pages.py` (`get_real_dashboard_metrics`, dashboard/reports/storage/task views) | Aggregates DB/twin/heartbeat/task/cloud data; some metrics estimated or derived from simulated components; labeling varies by endpoint |
| Comparative benchmarking & CSV export | **Implemented** | `engine/benchmark_runner.py`, `tasks/views.py` hospital benchmark APIs, `digital_twin/views.py compare`, `tasks/models.py` ExperimentRun/SchedulingDecision | Runs GA+5 baselines, records decisions/runs, exports 14-column CSV; results depend on twin/task inputs and include simulated cloud/execution aspects |
| Cloud/Drive integration | **Partially implemented / simulated-fallback capable** | `cloud/models.py`, `cloud/views.py`, `cloud/storage_manager.py`, storage emulator in `engine/storage_manager.py` | Metadata and API flows present; real external cloud behavior depends on configuration/credentials and includes simulated/emulated modes |
| Dataset/report/storage UI pages | **Implemented** | `datasets/views_pages.py`, templates referenced by views, `datasets/urls.py` | Dashboard, upload, digital twin, storage allocation, reports/detail/CSV, task history pages implemented |
| Automated tests | **Present, coverage unverified in this phase** | `tests/` directory | Tests exist but not executed/comprehensively reviewed here; pass/fail and coverage not claimed |

## 2. Key Architectural Findings
1. **Two scheduling decision contexts exist:**  
   - **Task scheduling path** uses real GA/baselines in `tasks/services.py` -> `engine/scheduler.py`/`engine/genetic_algorithm.py` with `PolicyEngine`.  
   - **Dataset upload allocation path** uses deterministic heuristic scoring in `engine/dataset_analysis_service.run_ai_scheduler_allocation`, while report metadata names GA+policy engine. This should be treated as a **correctness/traceability gap** for research claims.
2. **Measured vs simulated telemetry is mixed but explicit in twin:** LOCAL `MEASURED_HARDWARE` (psutil), MEC `MEASURED_HEARTBEAT` with staleness, CLOUD `SIMULATED_CLOUD` (`engine/digital_twin.py`). Downstream metrics may blend these sources.
3. **CLOUD execution tier is simulated:** `tasks/services.py:execute_task_cloud_simulation` and cloud storage emulator indicate cloud is not a verified real multi-region/public cloud execution substrate.
4. **Security/attacks are virtualized:** attack effects mutate twin state in-process (`engine/attack_simulator.py`), appropriate for testbed demonstration but not evidence of real adversarial hardening.
5. **Policy enforcement is strong in design (hard constraints) but must be validated end-to-end:** `PolicyEngine` blocks ineligible resources/dispatch; replication blocks privacy violations in storage manager; dataset/task paths both need runtime conformance verification.

## 3. Strengths Observed
- Clear modular separation: scheduling/policy/twin/storage/analysis/risk/benchmark engines.
- Explicit privacy policy model (`LOCAL_ONLY`, `TRUSTED_EDGE`, `CLOUD_ALLOWED`) integrated into scheduling eligibility.
- Real GA implementation with multi-objective fitness, constraints, and baseline comparators.
- Digital Twin distinguishes measured hardware/heartbeat vs simulated cloud in core model.
- Storage design includes SHA-256 verification, capacity tracking, privacy-boundary checks, idempotent replication concepts, and outside-webroot paths.
- MEC lifecycle includes pairing, token auth, heartbeat timeout-based presence, revocation, and task reassignment hooks.
- Experiment/decision persistence and CSV export support reproducible reporting workflows (subject to input determinism/config).

## 4. Risks, Inconsistencies, and Technical Debt (as-is)
- **Method labeling mismatch:** heuristic upload allocation labeled as GA in dataset analysis reports (`engine/dataset_analysis_service.py`).
- **Simulation reliance:** cloud execution/emulation, modeled energy/latency/risk in parts, virtual attacks; can be misinterpreted without strict labeling in outputs/UI.
- **Potential configuration/security hygiene:** default secret-key fallback and dev-oriented settings patterns in `securedt/settings.py` (env-based but defaults exist); needs production-hardening review if deployed.
- **State consistency complexity:** multiple sources of truth (DB tasks/heartbeats, twin snapshots, storage filesystem/DB replicas) require careful synchronization and audit.
- **Unverified runtime behavior in this audit:** test pass rate, 30-case ZIP outcomes, benchmark numeric claims, UI correctness, and MEC agent interoperability not executed here.

## 5. Audit Conclusion
The repository contains a **substantial, working-oriented research prototype** with real implementations for GA/baseline scheduling, policy enforcement primitives, MEC auth/heartbeat management, a mixed-fidelity digital twin, tri-tier storage management, dataset analysis/reporting pipeline, and virtual security/benchmark tooling. However, several elements are **partially implemented, simulated, or inconsistently labeled** (notably upload-path GA labeling and cloud/some metric fidelity). These gaps define the priority targets for SecureDT 2.0 evolution; no major implementation changes are made in this phase pending approval.
