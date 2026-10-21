"""
regenerate_guides.py
====================
Regenerates the user-facing SecureDT PDF guides so every guide matches the
current consolidated Django system (single-server, DRF API, MySQL).

Overwrites these docs:
    USER_MANUAL.pdf
    COMPLETE_INSTALLATION_AND_USAGE_GUIDE.pdf
    MEC_AGENT_INSTALLATION_AND_CONNECTION_GUIDE.pdf
    GOOGLE_DRIVE_CLOUD_SETUP_GUIDE.pdf
    DATASET_UPLOAD_AND_PROCESSING_GUIDE.pdf
    AI_MODEL_GUIDE.pdf

Usage:
    python scripts/regenerate_guides.py
"""

import os

from fpdf import FPDF

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DOCS = os.path.join(ROOT, "docs")


def make_pdf(title, sections, filename):
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.set_margins(10, 12, 10)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(15, 65, 130)
    pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(15, 65, 130)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    for heading, lines in sections:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(15, 65, 130)
        pdf.cell(0, 7, heading, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Courier", "", 9.5)
        for line in lines:
            pdf.set_text_color(0, 0, 0)
            pdf.set_x(10)
            pdf.multi_cell(190, 5.2, line, align="L")
        pdf.ln(3)

    path = os.path.join(DOCS, filename)
    pdf.output(path)
    print(f"wrote {filename}")


SYSTEM_INTRO = [
    ("System Summary", [
        "SecureDT is a Django REST Framework application that schedules tasks across",
        "edge/MEC/cloud resources using a security-aware Genetic Algorithm. A digital",
        "twin mirrors every registered device, a Random Forest model predicts risk",
        "levels, and unplanned storage/security attacks can be simulated live.",
        "",
        "Architecture at a glance:",
        "  - Web + REST API ....... Django 5, DRF, port 8000",
        "  - Database ............. MySQL (securetdb), at 127.0.0.1:3307",
        "  - MEC agents ........... Windows Python agent (MEC_Agent.exe)",
        "  - Cloud storage ........ Google Drive simulation module",
        "  - AI ................... Random Forest + local explainer",
    ]),
]

RUN_SYSTEM = [
    ("1. Start MySQL", [
        '  net start SecureDT_Mysql',
        "  (port 3307, database securetdb; credentials in .env)",
    ]),
    ("2. Install dependencies", [
        "  cd SecureDT",
        "  python -m pip install -r requirements.txt",
    ]),
    ("3. Migrate + create the admin user", [
        "  python manage.py migrate",
        '  python manage.py createsuperuser',
    ]),
    ("4. Create a pairing code, then start the server", [
        "  python manage.py shell -c \"from mec_manager.models import PairingCode; print(PairingCode.generate_new().code)\"",
        "  python manage.py runserver 0.0.0.0:8000",
    ]),
    ("5. Log in and explore", [
        "  Open http://127.0.0.1:8000/login",
        "  Pages: Dashboard, Task Routing, MEC Infrastructure, Digital Twin,",
        "  Genetic Algorithm, AI Intelligence, Security Monitor, Attack Simulation,",
        "  Storage Attack/Defense, Datasets, Cloud Storage, Data Flow, Analytics,",
        "  Performance, Energy Monitor.",
        "  Every page reads the live REST API; refresh polls state every 5 seconds.",
    ]),
]

MEC_GUIDE = [
    ("Requirements", [
        "  Python 3.10+ / Windows, or the prebuilt MEC_Agent.exe.",
        "  .env values on the agent: see mec_agent/.env.example",
    ]),
    ("Connect a device (pairing flow)", [
        "  1. Generate a pairing code on the server (see above).",
        "  2. Start the agent:",
        "       MEC_Agent.exe  (or: python mec_agent/agent.py --pairing CODE)",
        "  3. The agent auto-registers, then sends a heartbeat every 10s.",
        "  4. In the UI go to MEC Infrastructure - the new MEC-xxx node is ONLINE.",
    ]),
    ("Agent APIs it calls", [
        "  POST /api/mec/register/   (pairing_code, system_name, server_url)",
        "  POST /api/mec/heartbeat/   (mec_id, auth_token, cpu/ram/disk/latency...)",
        "  GET  /api/mec/<id>/next-task/        (assigned task, if any)",
        "  POST /api/mec/<id>/report-result/    (execution_time, success, metrics)",
        "  All authenticated by Authorization: Token <agent-token> + X-MEC-ID header.",
    ]),
    ("Revoking", [
        "  Admin can revoke a device (nav -> MEC Infrastructure -> Revoke);",
        "  revoked devices are blocked and never receive tasks.",
    ]),
]

CLOUD_GUIDE = [
    ("Cloud Storage page", [
        "  Nav -> Cloud Storage: view uploaded files, create folders, list files,",
        "  check quota from /api/cloud/status/.",
        "  Uploads: POST multipart to /api/cloud/upload/",
        "  Download: GET /api/cloud/download/<file_id>/",
    ]),
    ("Datasets workflow", [
        "  Nav -> Datasets: upload CSV/JSON/zip datasets into the cloud workspace",
        "  and sync them to the server's datasets/ folder for training.",
        "  Currently Google Drive runs in simulation mode (local folder emulation)",
        "  with the same upload/status/list API contract.",
    ]),
    ("API reference", [
        "  GET  /api/cloud/files/         list files (filter: ?category=dataset)",
        "  POST /api/cloud/upload/        multipart upload",
        "  GET  /api/cloud/status/        quota / storage usage",
        "  POST /api/cloud/folders/       create folder",
        "  GET  /api/cloud/download/<id>/ download a file",
    ]),
]

DATASET_GUIDE = [
    ("Purpose", [
        "The dataset manager feeds the AI risk-prediction model. Training data:",
        "  datasets/ai_training_10000.csv   (10,000 labelled samples)",
        "Fields: cpu, memory, latency, trust, security_risk, privacy, workload,",
        "        storage_integrity, attack_exposure, risk_level",
    ]),
    ("Retrain the model", [
        "  python scripts/train_ai.py        (trains + saves models/risk_model.pkl)",
        "  Or in AI Intelligence page press 'Retrain model' (POST /api/analytics/ai-status/).",
        "  Validated against a 20% held-out split; accuracy printed after training.",
    ]),
    ("Validate / inspect", [
        "  python scripts/validate_dataset.py",
        "  python scripts/dataset_check.py",
    ]),
]

AI_GUIDE = [
    ("Model", [
        "  Classifier: RandomForest (fallback to rules when unloaded).",
        "  Predicts per-task risk level: LOW / MEDIUM / HIGH / CRITICAL.",
        "  Endpoint: GET/POST /api/analytics/ai-status/",
    ]),
    ("Response payload", [
        "  status, model, features, metrics{accuracy, precision, recall, f1,",
        "  confusion_matrix, train_size, test_size}, samples, llm_backend",
        "  samples[] = per-task predicted level, confidence, recommended_priority,",
        "              reasons.",
    ]),
    ("Live dispatch integration", [
        "  The Genetic Algorithm scheduler combines cost (latency/energy) with",
        "  privacy-loss and security-risk so HIGH/CRITICAL tasks avoid weak nodes.",
    ]),
]

GA_GUIDE = [
    ("Inputs", [
        "  Live MEC resources from the digital twin (LOCAL, MEC-XXX*, CLOUD)",
        "  with cpu_usage, ram_usage, latency, energy besides per-device",
        "  security_risk / privacy_loss scores.",
        "  Only ONLINE, non-revoked MEC devices are eligible (OFFLINE / REVOKED",
        "  are never assigned tasks; their tasks are requeued automatically).",
    ]),
    ("Optimizer", [
        "  Scheduler.proposed_ga_schedule() - steady-state GA, population 40,",
        "  generations 30, multi-objective fitness:",
        "      fitness = w1*latency + w2*energy + w3*security_risk + w4*privacy_loss",
        "  Parents selected by tournament; children via crossover + mutation;",
        "  elitism keeps the best chromosome. Returns assignments + metrics",
        "  (best_fitness, generation, convergence_time).",
    ]),
    ("Dispatch", [
        "  POST /api/tasks/dispatch/  {population, generations}",
        "  run_ga_dispatch() marks each task ASSIGNED + creates history entries",
        "  (PENDING/QUEUED -> ASSIGNED). No ONLINE MEC => tasks stay QUEUED,",
        "  they are never routed to offline devices.",
    ]),
    ("Task lifecycle", [
        "  PENDING -> QUEUED -> ASSIGNED -> RUNNING -> (COMPLETED / FAILED)",
        "  Agents poll /api/mec/<id>/next-task/ and report results via",
        "  /api/mec/<id>/report-result/. Offline/revoked devices are requeued.",
    ]),
]

TWIN_GUIDE = [
    ("Concept", [
        "  engine/digital_twin.py builds a live mirror of every resource.",
        "  Each resource has a ResourceState: cpu_usage, ram_usage, latency,",
        "  energy, security_risk, privacy_loss, trust_level, available.",
    ]),
    ("Nodes", [
        "  - LOCAL  ............ the server itself (always present)",
        "  - MEC-001 ... MEC-0NN . every registered, non-revoked MEC device,",
        "                          ONLINE via heartbeat (10 s cadence)",
        "  - CLOUD  .............. the Google Drive / cloud node (always present)",
        "  Resource order: LOCAL, MEC-1.., CLOUD (config.RESOURCE_ORDER).",
    ]),
    ("Synchronous twins", [
        "  Heartbeat processing (process_heartbeat) updates the device twins in",
        "  real time; refresh_mec_status() flips offline devices after the",
        "  timeout so the scheduler never assigns to stale twins.",
    ]),
]

SECURITY_GUIDE = [
    ("Authentication", [
        "  Web UI ........... Django session login (/login/, /register/).",
        "  REST API ......... DRF TokenAuthentication (Authorization: Token)",
        "  MEC agents ....... MECAuthentication: DRF token + X-MEC-ID header;",
        "                     heartbeat body carries auth_token.",
    ]),
    ("Device lifecycle", [
        "  PairingCode (admin) -> register -> auto device_id (MEC-001...).",
        "  Revocation blocks a device instantly; ONLINE/REVOKED logic keeps",
        "  revoked twins out of the scheduler and requeues their tasks.",
    ]),
    ("Attack simulation (no real attacks)", [
        "  /api/security/attack/ runs fake attacker profiles against the DUAL",
        "  security model (cost + privacy + trust + SLA + risk):",
        "      benign, ddos, data_breach, ransomware, zero_day.",
        "  Dashboard + Security Monitor show live threat level + per-node flags.",
        "  Storage attack page: unauthorised encryption attempts on the cloud",
        "  simulator can be guarded (recover endpoint resets integrity).",
    ]),
]

DATAFLOW_GUIDE = [
    ("Path 1: task submission", [
        "  UI/API -> /api/tasks/ -> PENDING -> GA scheduler -> ASSIGNED ->",
        "  MEC agent polls next-task -> RUNNING -> report-result -> COMPLETED.",
    ]),
    ("Path 2: MEC telemetry", [
        "  Agent -> POST /api/mec/heartbeat/ -> process_heartbeat() ->",
        "  updates MECAgent row + digital twin ResourceState -> UI charts.",
    ]),
    ("Path 3: cloud data", [
        "  UI/API -> POST /api/cloud/upload/ -> GoogleDriveFile record +",
        "  (simulation/local bytes or Drive) -> GET /api/cloud/files/ -> UI.",
        "  Downloads stream via /api/cloud/download/<id>/.",
    ]),
    ("Path 4: data, not advertisements", [
        "  All dashboard/storage numbers are computed by the REST API from the",
        "  MySQL database and live agent heartbeats - nothing is hard-coded.",
    ]),
]

REVIEW0 = [
    ("Deliverables", [
        "  1. SecureDT Django/MySQL/DRF web app with 15 pages + session login.",
        "  2. Prebuilt Windows MEC agent ............ release/MEC_Agent.exe",
        "  3. Google Drive cloud module (simulation-compatible).",
        "  4. Automated tests ........................ tests/ (12 passing).",
        "  5. PDF documentation set (this folder).",
        "  6. Deployable ZIP ........................ Intelligent_Secure_",
        "     Task_Scheduling_Django_MySQL_FINAL.zip",
    ]),
    ("Verified behaviours", [
        "  - All pages render 200; endpoints authenticated via DRF/session.",
        "  - Task lifecycle: dispatch, next-task, report-result, requeue.",
        "  - Offline detection: stale MECs are marked OFFLINE and skipped.",
        "  - Multi-MEC scaling: dashboards adapt to any number of agents.",
        "  - Cloud upload/list/download round-trips to the simulator.",
        "  - AI model trains and predicts (RF, local fallback) - ai-status POST.",
    ]),
    ("Security notes", [
        "  - .env (secrets) is excluded from the release ZIP.",
        "  - Tokens + pairing codes = device identity; revocation is instant.",
        "  - Attack simulator is fully simulated; it never performs real attacks.",
    ]),
]


def build_all():
    os.makedirs(DOCS, exist_ok=True)
    make_pdf("SecureDT - User Manual", SYSTEM_INTRO + RUN_SYSTEM, "USER_MANUAL.pdf")
    make_pdf("SecureDT - Installation & Usage", RUN_SYSTEM + SYSTEM_INTRO, "COMPLETE_INSTALLATION_AND_USAGE_GUIDE.pdf")
    make_pdf("MEC Agent - Install & Connect", MEC_GUIDE, "MEC_AGENT_INSTALLATION_AND_CONNECTION_GUIDE.pdf")
    make_pdf("Google Drive / Cloud Storage Setup", CLOUD_GUIDE, "GOOGLE_DRIVE_CLOUD_SETUP_GUIDE.pdf")
    make_pdf("Dataset Upload & Processing", DATASET_GUIDE + AI_GUIDE, "DATASET_UPLOAD_AND_PROCESSING_GUIDE.pdf")
    make_pdf("AI Model - Installation & Usage", AI_GUIDE + DATASET_GUIDE, "AI_MODEL_INSTALLATION_AND_USAGE.pdf")
    make_pdf("Genetic Algorithm Guide", GA_GUIDE, "GENETIC_ALGORITHM_GUIDE.pdf")
    make_pdf("Digital Twin Architecture", TWIN_GUIDE, "DIGITAL_TWIN_ARCHITECTURE.pdf")
    make_pdf("Security Architecture", SECURITY_GUIDE, "SECURITY_ARCHITECTURE.pdf")
    make_pdf("Data Flow & Communication", DATAFLOW_GUIDE, "DATA_FLOW_AND_COMMUNICATION.pdf")
    make_pdf("Review 0 - Project Documentation", REVIEW0, "REVIEW_0_DOCUMENTATION.pdf")


if __name__ == "__main__":
    build_all()