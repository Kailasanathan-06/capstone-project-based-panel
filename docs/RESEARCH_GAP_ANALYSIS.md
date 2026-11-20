# Research Gap Analysis (Phase 1)

**Context:** Comparison of the *existing SecureDT implementation in this repository* against the stated SecureDT 2.0 objective: **“AI-Driven Adaptive and Trust-Aware Task Scheduling Framework for Secure Digital Twin-Enabled Edge–Cloud Networks.”**  
**Baseline references:** inspected codebase and existing project materials (`docs/base paper.pdf`, `paper/SecureDT_IEEE_Paper.pdf`, `README.md`, `docs/*`). This analysis distinguishes implemented, partial, simulated, and missing elements without fabricating experimental results.

## 1. Original/Current System Baseline (as evidenced)
- Multi-tier architecture (Local/MEC/Cloud) with Digital Twin representation (`engine/digital_twin.py`) mixing **measured** local hardware (psutil) and **measured heartbeat** MEC telemetry (with staleness) plus **simulated** cloud.
- Explicit privacy placement policies `LOCAL_ONLY`, `TRUSTED_EDGE`, `CLOUD_ALLOWED` enforced by `engine/policy_engine.py` and used by schedulers.
- Multi-objective GA scheduler and 5 baselines for task scheduling/comparison (`engine/genetic_algorithm.py`, `engine/scheduler.py`, `engine/benchmark_runner.py`).
- MEC lifecycle: pairing, token auth, heartbeat timeout-based presence, revocation, task reassignment hooks (`mec_manager/*`, `tasks/services.py`).
- Tri-tier storage (50/200/1000 GB) with SHA-256 verification, privacy-boundary checks, idempotent replication concepts, emulator-flagged cloud (`engine/storage_manager.py`).
- Dataset ZIP analysis pipeline, report persistence/CSV export, hospital workload scenarios and 30-case ZIP assets (`engine/dataset_analysis_service.py`, `datasets/*`, `sample_upload_datasets/`).
- Security/risk components: model-based risk (`engine/risk_engine.py`), virtual attack simulation (`engine/attack_simulator.py`), monitoring/audit logging (`engine/security_monitor.py`, `SecurityAuditEvent`).
- Basic AI risk classifier: offline RandomForest with rule fallback and optional cached LLM explanation (`engine/ai_engine.py`).

## 2. Gap Analysis by SecureDT 2.0 Goal

| SecureDT 2.0 Goal Area | Current State | Gap / Limitation | Evidence |
|---|---|---|---|
| **AI-driven scheduling (beyond static heuristics/weights)** | Real GA with fixed multi-objective fitness and offline RF risk classifier exist | Scheduling weights/objectives are largely static; no demonstrated online learning, adaptive weight tuning, or closed-loop policy optimization from runtime outcomes | `engine/genetic_algorithm.py` (config/weights), `engine/scheduler.py`, `engine/ai_engine.py` (offline train/predict, rule fallback) |
| **Adaptive behavior under dynamics** | Twin updates via ticks/heartbeats; requeue on MEC offline; stale detection | Limited evidence of proactive adaptation (e.g., predictive load/failure-aware rescheduling, feedback-driven reoptimization, SLA-aware adaptation loops) | `engine/digital_twin.py`, `mec_manager/services.py` timeout/requeue, `tasks/services.py` |
| **Trust-aware scheduling (continuous, evidence-based trust)** | Trust/risk fields in twin/resources; risk engine and attack simulation influence state; revocation/eligibility enforced | Trust appears coarse/model-driven; no unified, continuously updated trust score derived from longitudinal behavior, attestation, anomaly evidence, and integrated as first-class scheduling objective with provenance | `engine/digital_twin.py` (`trust`/risk), `engine/risk_engine.py`, `engine/attack_simulator.py`, `engine/policy_engine.py` (availability-based), `tasks/models.py` fields |
| **Secure Digital Twin fidelity** | Mixed measured (LOCAL psutil, MEC heartbeat) and simulated (CLOUD) states; explicit labels in twin | Fidelity gaps for cloud and some metrics; twin-to-physical synchronization guarantees, calibration, and uncertainty/provenance surfacing in decisions/reports need strengthening | `engine/digital_twin.py` (`MEASURED_HARDWARE`, `MEASURED_HEARTBEAT`, `SIMULATED_CLOUD`) |
| **Robust security (beyond simulation)** | Virtual attacks, model-based risk, audit events, privacy-boundary blocking | No evidence of real adversarial testing, intrusion detection on real telemetry streams, cryptographic trust/attestation, or hardened threat model validation; security mostly demonstrative | `engine/attack_simulator.py`, `engine/risk_engine.py`, `engine/security_monitor.py`, `engine/storage_manager.py` policy blocks |
| **Anomaly/fault detection & resilience intelligence** | Timeout/retry/error categories in models/workloads, heartbeat timeouts, requeue logic | Lacks systematic anomaly detection (behavioral/statistical/ML) over telemetry/tasks/storage events and automated mitigation policies informed by detections | `tasks/models.py` (retry/timeout/error fields), `mec_manager/services.py`, `engine/hospital_workloads.py` |
| **Consistent, verifiable scheduling methodology across pipelines** | Task path uses GA/baselines; upload path uses heuristic allocation | **Methodological inconsistency:** dataset upload allocation uses deterministic heuristic yet is labeled as GA in report metadata, weakening traceability of research claims | `tasks/services.py`/`engine/scheduler.py` vs `engine/dataset_analysis_service.py` (`run_ai_scheduler_allocation`, report method strings) |
| **Measured, reproducible evaluation** | Benchmark runner, experiment/decision persistence, CSV export, seeded runs | Quantitative validity limited by simulated cloud/execution components and unverified end-to-end runs in this audit; need standardized experiments, baselines on identical conditions, and clear measured-vs-simulated labeling in all outputs | `engine/benchmark_runner.py`, `tasks/models.py` (`ExperimentRun`, `SchedulingDecision`), `digital_twin/views.py` compare |
| **Scalability & heterogeneity validation** | MEC registration and multi-resource abstractions exist | Evidence of validation with many/heterogeneous real MEC nodes, network variability, and larger workloads is not demonstrated in inspected code/docs artifacts alone | `mec_manager/*`, `engine/digital_twin.py`, `sample_upload_datasets/` |
| **Explainability and auditability of decisions** | Decision/rationale fields, reports, audit events exist | Explanations partly descriptive/heuristic; need consistent, machine-readable rationale linking objectives, trust/risk, policy constraints, and measured inputs per decision | `tasks/models.py` (`SchedulingDecision`), `engine/dataset_analysis_service.py` reports, `engine/ai_engine.py` optional LLM explain |
| **Energy/latency realism** | psutil-based local measures and modeled costs/estimates elsewhere | Energy often model-based/estimated; cloud/MEC network and compute latencies partly parameterized/simulated; requires calibrated measurement methodology | `engine/digital_twin.py`, `engine/scheduler.py` cost model, `tasks/services.py` (estimated energy/sim cloud), analytics notes |
| **Deployment/security hardening** | Env-configurable settings, auth for MEC/APIs in places | Dev defaults/fallbacks and mixed permission postures (some APIs AllowAny) warrant review for secure deployment; not a research algorithm gap but impacts trustworthy evaluation environments | `securedt/settings.py`, `datasets/views_pages.py`, `tasks/views.py`, `digital_twin/views.py`, `cloud/views.py` |

## 3. Gap Prioritization (for SecureDT 2.0)
**High priority (directly tied to stated objective):**
1. **Trust-aware, adaptive scheduling core:** define and integrate dynamic trust scores (behavior/heartbeat/anomaly/security signals) into GA objectives/constraints with feedback-driven adaptation.
2. **Methodological consistency & provenance:** unify/clarify scheduling logic and labels (actual GA vs heuristic) across task and dataset pipelines; tag every metric/decision as measured/simulated/modeled.
3. **Digital Twin fidelity & synchronization:** improve MEC/cloud state accuracy, calibration hooks, and uncertainty handling to support adaptive decisions.
4. **Security/anomaly intelligence:** move from purely virtual attack effects to telemetry-driven anomaly/risk updates and response policies grounded in observed behavior.

**Medium priority:**
5. **Evaluation rigor:** reproducible experiment protocols, fixed seeds/configs, validated 30-case outcomes, and statistically meaningful comparisons under controlled conditions.
6. **Explainability:** structured, auditable decision rationales and traceable objective contributions per allocation.
7. **MEC/cloud realism:** stronger real-agent/cloud integration paths and performance characterization (where feasible) while preserving explicit simulation labels when not.

## 4. Reusable Foundations (to preserve)
- `PolicyEngine` hard-constraint model and privacy policies.
- GA and baseline scheduler implementations/evaluation framework.
- MEC pairing/auth/heartbeat/revocation and task lifecycle/history models.
- Digital Twin abstraction with measured-vs-simulated distinction.
- Storage manager integrity/privacy mechanisms and reporting/benchmark persistence scaffolding.
- Existing 14-scenario/30-case assets and UI/API surfaces for iterative enhancement.

**Conclusion:** The current system is a capable prototype for privacy/policy-constrained edge–cloud scheduling with mixed-fidelity twin and simulated security, but it falls short of *SecureDT 2.0* mainly in **adaptive, trust-aware intelligence grounded in continuous evidence**, **end-to-end methodological consistency/provenance**, and **measured, rigorously validated security/adaptation behavior**. These gaps should drive an incremental roadmap that reuses existing engines and avoids architectural rewrites without approval.
