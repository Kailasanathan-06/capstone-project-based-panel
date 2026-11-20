# SecureDT 2.0 Implementation Roadmap (Phase 1)

**Status:** Proposed roadmap for approval. **No major implementation changes have been made** in Phase 1; existing functionality must be preserved and changes applied incrementally.

## 1. Guiding Principles
- **Preserve & extend:** reuse existing modules (`PolicyEngine`, GA/baselines, Digital Twin, MEC manager, storage manager, models/UI/APIs) rather than rebuilding.
- **Evidence over claims:** label all outputs/metrics as **measured**, **simulated**, or **model-based**; do not fabricate results.
- **Consistency:** align scheduling/allocation methodology and reporting across task and dataset pipelines.
- **Incremental validation:** validate each phase with targeted tests/scenarios before advancing; keep 30-case ZIP and 14-scenario assets runnable.
- **Security & privacy by constraint:** maintain hard policy enforcement (`LOCAL_ONLY/TRUSTED_EDGE/CLOUD_ALLOWED`) and auditability.

## 2. Phase Plan

### Phase 1 — Audit & Baseline (COMPLETED, pending approval)
**Objective:** Establish authoritative as-is understanding and gaps.  
**Deliverables (this audit):**
- `docs/SECUREDT_EXISTING_ARCHITECTURE.md`
- `docs/SECUREDT_CODE_AUDIT.md`
- `docs/EXISTING_FEATURE_INVENTORY.md`
- `docs/RESEARCH_GAP_ANALYSIS.md`
- `docs/IMPLEMENTATION_ROADMAP.md`

**Exit criteria:** User approval to proceed with major implementation changes.

### Phase 2 — Methodological Consistency & Provenance (first implementation priority)
**Objective:** Remove ambiguity/inconsistency in how decisions are made and reported.  
**Key tasks:**
1. **Unify allocation semantics:** reconcile dataset upload allocation (`engine/dataset_analysis_service.py:run_ai_scheduler_allocation`, heuristic) with task scheduling GA/baselines — either invoke/align with GA+`PolicyEngine` where appropriate or explicitly label as deterministic heuristic in code, DB, reports, and UI.
2. **Provenance tagging:** add/standardize measured-vs-simulated-vs-model-based flags for latency/energy/risk/trust/cloud execution across scheduler outputs, reports, analytics, and twin snapshots.
3. **Decision traceability:** ensure `SchedulingDecision`/report rationales record algorithm, policy, eligible candidates/rejections, objective components, and data source (measured/heartbeat/simulated).
4. **Non-regression checks:** verify existing dashboard/upload/report/task flows still function with corrected labels.

**Primary files:** `engine/dataset_analysis_service.py`, `engine/scheduler.py`, `engine/genetic_algorithm.py`, `engine/digital_twin.py`, `tasks/models.py`/`tasks/services.py`, `datasets/models.py`/views, analytics/report serializers/views.  
**Risk:** medium (touches reporting/decision paths); mitigate with side-by-side comparisons and tests.

### Phase 3 — Trust-Aware & Adaptive Scheduling Foundation
**Objective:** Introduce continuous, evidence-based trust and adaptive decision-making aligned with SecureDT 2.0.  
**Key tasks:**
1. **Trust model/service:** compute dynamic trust scores per resource/MEC from heartbeat freshness/stability, task outcomes, revocation/status, and security/audit/anomaly signals (with clear formula and bounds).
2. **Integrate trust into scheduling:** extend GA fitness and baseline scoring/eligibility to incorporate trust as explicit objective/penalty (configurable, documented), while preserving hard privacy policies via `PolicyEngine`.
3. **Adaptive tuning hooks:** enable feedback-driven adjustment (e.g., weight profiles, re-scheduling triggers) based on observed SLA/latency/energy/failure/trust trends; start rule-based/adaptive heuristics before complex learning.
4. **Twin synchronization improvements:** better use of heartbeat freshness, staleness penalties, and state provenance in candidate selection.

**Primary files:** `engine/digital_twin.py`, `engine/policy_engine.py`, `engine/genetic_algorithm.py`, `engine/scheduler.py`, `tasks/services.py`, `mec_manager/services.py`, new/extended trust module as needed.  
**Risk:** medium-high (core scheduling behavior); require controlled benchmarks and policy-compliance tests.

### Phase 4 — Security Intelligence & Anomaly-Driven Resilience
**Objective:** Move from purely virtual security effects toward telemetry- and behavior-informed risk/anomaly handling.  
**Key tasks:**
1. **Telemetry/anomaly signals:** derive anomaly indicators from heartbeat/task/storage/audit patterns (threshold/statistical baselines initially) and feed into risk/trust updates.
2. **Risk model calibration interface:** separate simulated attack scenarios from observed-signal risk paths; clearly label scenario-injected vs detected risk.
3. **Automated response policies:** define safe responses (quarantine/re-route/requeue/alert) triggered by trust/risk thresholds, integrated with existing revocation/requeue mechanisms.
4. **Audit completeness:** ensure security/privacy events (including pipeline and replication violations) are consistently recorded and surfaced.

**Primary files:** `engine/risk_engine.py`, `engine/security_monitor.py`, `engine/attack_simulator.py` (keep as simulation mode), `engine/ai_engine.py` (optional enhancement), `mec_manager/services.py`, `engine/storage_manager.py`, `datasets/models.py`.  
**Risk:** medium; must avoid false-positive disruption of valid workloads.

### Phase 5 — Digital Twin Fidelity, Measurement, and Cloud/MEC Realism
**Objective:** Improve accuracy and usefulness of twin-driven decisions.  
**Key tasks:**
1. **Refine LOCAL/MEC measurement paths:** standardize collection, smoothing/windowing, and freshness semantics; expose confidence/provenance.
2. **Cloud modeling clarity:** keep cloud as explicit simulation/emulation unless/until real integration is implemented; calibrate cost/latency models and document assumptions.
3. **Real MEC integration hardening:** validate agent protocol (register/heartbeat/task pull/report/result) against realistic agents and failure modes.
4. **Workload execution realism:** align image/hospital workload processing, timing, and checksum/result handling across local/MEC/cloud paths where supported.

**Primary files:** `engine/digital_twin.py`, `tasks/services.py`, `mec_manager/views.py`/services, `engine/hospital_workloads.py`, `engine/image_processor.py`, `engine/storage_manager.py`, cloud modules.  
**Risk:** medium; integration-dependent.

### Phase 6 — Evaluation, Reproducibility, and Research Reporting
**Objective:** Produce defensible, reproducible evidence for SecureDT 2.0 claims.  
**Key tasks:**
1. **Experiment protocol:** fixed seeds/configs, dataset/case manifests (14 scenarios, 30 ZIPs), and documented environment assumptions.
2. **Benchmark rigor:** run GA vs baselines under identical, provenance-labeled conditions; report metrics with measured/simulated breakdown and policy-compliance outcomes.
3. **Test & validation suite:** exercise existing `tests/` and add targeted tests for policy enforcement, trust updates, requeue/offline behavior, storage integrity/privacy blocks, and report consistency.
4. **Documentation alignment:** update technical docs/paper artifacts to reflect actual methods, limitations, and results (no fabricated numbers).

**Primary files:** `engine/benchmark_runner.py`, `tests/`, `sample_upload_datasets/`, `docs/*`, `paper/*` (only as needed and consistently).  
**Risk:** low-medium; mainly validation/reporting effort.

## 3. Component Reuse Map (preserve and build upon)
| Existing asset | Reuse in SecureDT 2.0 |
|---|---|
| `engine/policy_engine.py` | Authoritative hard privacy/eligibility constraints |
| `engine/genetic_algorithm.py`, `engine/scheduler.py` | Core multi-objective optimizer and baselines/comparators |
| `engine/digital_twin.py` | State abstraction; extend with trust/provenance/fidelity |
| `mec_manager/*` | Secure agent onboarding, heartbeat presence, revocation, task I/O |
| `engine/storage_manager.py` | Integrity-verified, policy-aware tiered storage substrate |
| `engine/dataset_analysis_service.py` | Pipeline/report framework; refactor allocation/provenance |
| `tasks/models.py`, `datasets/models.py` | Lifecycle/decision/experiment/audit persistence |
| `datasets/views_pages.py`, analytics/digital_twin/cloud APIs | UI/API surfaces for observability and control |
| `sample_upload_datasets/`, `engine/benchmark_runner.py` | Evaluation assets and comparative experiment harness |

## 4. First Components to Improve (recommended sequence after approval)
1. **Provenance + labeling correctness:** fix/align dataset allocation method labeling and add measured/simulated/model-based tagging in outputs (`engine/dataset_analysis_service.py`, reporting paths).
2. **Trust signal integration (minimal, explicit):** introduce a simple dynamic trust score from heartbeat freshness, online stability, and task outcomes into twin/scheduler inputs without breaking policies.
3. **GA/objective wiring for trust:** incorporate trust term/penalty into existing GA/scheduler cost model and expose in decision records.
4. **Targeted validation:** run/extend tests for policy compliance, offline requeue, and storage privacy blocking to lock behavior before deeper adaptation.

## 5. Dependencies, Risks, and Constraints
- **External dependencies:** real MEC agent software/hardware and any real cloud credentials/integration are outside pure codebase control; keep simulated modes explicit when unavailable.
- **Data/model dependencies:** `engine/ai_engine.py` RF training depends on available datasets/config; Groq features depend on env/config and should degrade gracefully.
- **Backward compatibility:** API/UI contract changes must be managed carefully; prefer additive fields/flags.
- **Performance/correctness tradeoff:** adaptive logic must not violate hard privacy constraints or starve eligible tasks; blocked/unassignable states must remain explicit.

## 6. Approval Gate
Proceed to Phase 2 implementation **only after explicit user approval** of this audit and roadmap. Upon approval, implement in small, verifiable increments with preserved functionality and evidence-backed reporting.
