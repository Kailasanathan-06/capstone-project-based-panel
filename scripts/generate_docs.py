"""
generate_docs.py
================
Builds the SecureDT PDF documentation set under docs/:
    INSTALLATION_GUIDE.pdf
    REVIEW_0_GUIDE.pdf
    DATASET_GUIDE.pdf
    USER_MANUAL.pdf
    DATASET_MANAGER_GUIDE.pdf   (registry, quality, normalize, big-data)
    SECURITY_GUIDE.pdf          (headers, CSRF, rate limits, audit lab)
    API_CONFIGURATION_GUIDE.pdf (config.yaml, keys, env vars)
    EXPERIMENT_GUIDE.pdf        (campaigns + baselines + export)
    AI_MODEL_GUIDE.pdf          (training, explainability, fallback)

Usage:
    python scripts/generate_docs.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

import config  # noqa: E402
from engine import bigdata, dataset_registry, scheduler, telemetry  # noqa: E402

OUT_DIR = os.path.join(config.BASE_DIR, "docs")
os.makedirs(OUT_DIR, exist_ok=True)

INK = colors.HexColor("#0a0e17")
ACCENT = colors.HexColor("#35e0ff")
SOFT = colors.whitesmoke


def _styles():
    styles = getSampleStyleSheet()

    def make(name, **kw):
        base = {
            "fontName": "Helvetica",
            "fontSize": 10,
            "leading": 14,
            "textColor": colors.black,
        }
        base.update(kw)
        return ParagraphStyle(name, **base)

    return {
        "h1": make(
            "Title",
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=26,
            textColor=INK,
            spaceAfter=6,
        ),
        "h2": make(
            "H2",
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=INK,
            spaceBefore=12,
            spaceAfter=6,
        ),
        "h3": make(
            "H3",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#0f1a33"),
            spaceBefore=10,
            spaceAfter=4,
        ),
        "body": make("Body", fontSize=10, leading=15),
        "bullet": make(
            "Bullet", fontSize=10, leading=15, leftIndent=12, bulletIndent=4
        ),
        "mono": make("Mono", fontName="Courier", fontSize=8.5, leading=12),
    }


def _title_table(doc_title, subtitle):
    inner = Table(
        [
            [
                Paragraph(
                    doc_title,
                    ParagraphStyle(
                        "t",
                        fontName="Helvetica-Bold",
                        fontSize=22,
                        leading=28,
                        textColor=colors.white,
                    ),
                )
            ],
            [
                Paragraph(
                    subtitle,
                    ParagraphStyle(
                        "s",
                        fontName="Helvetica",
                        fontSize=11,
                        leading=14,
                        textColor=colors.HexColor("#dce7ff"),
                    ),
                )
            ],
        ],
        colWidths=[165 * mm],
    )
    inner.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, 0), 14),
                ("TOPPADDING", (0, 1), (-1, 1), 4),
                ("BOTTOMPADDING", (0, -1), (-1, -1), 14),
            ]
        )
    )
    outer = Table([[inner]], colWidths=[170 * mm])
    outer.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), INK),
                ("BOX", (0, 0), (-1, -1), 0, colors.white),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return outer


def _section_table(rows):
    t = Table(rows, colWidths=[150 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SOFT),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c7d5ea")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return t


def _build(path, title, subtitle, blocks):
    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=title,
    )
    story = [_title_table(title, subtitle), Spacer(1, 8 * mm)]
    story.extend(blocks)
    doc.build(story)
    print(f"  {os.path.basename(path)} generated")


def _bullet(s, bullet="•"):
    st = _styles()
    return Paragraph(f"<bullet>{bullet}</bullet>{s}", st["bullet"], bulletText=bullet)


def build_installation():
    st = _styles()
    blocks = [
        Paragraph("1. System Prerequisites", st["h2"]),
        Paragraph(
            "• Python 3.10 or newer (64-bit)<br/>"
            "• pip (bundled with Python)<br/>"
            "• A web browser (Chrome / Edge / Firefox)",
            st["body"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("2. Install Dependencies", st["h2"]),
        Paragraph("From the project root:", st["body"]),
        Paragraph("python -m pip install -r requirements.txt", st["mono"]),
        Paragraph(
            "Key packages: Flask, Flask-Cors, pandas, numpy (>=2.0), "
            "scikit-learn, reportlab, fpdf2.",
            st["body"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("3. Generate Datasets & Train the AI Model", st["h2"]),
        Paragraph("python scripts/generate_dataset.py --tasks 10000", st["mono"]),
        Paragraph("python scripts/train_ai.py", st["mono"]),
        Paragraph(
            "Six synthetic datasets are written to datasets/ and the "
            "Random Forest model to models/risk_model.pkl.",
            st["body"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("4. Start the Application", st["h2"]),
        Paragraph("python app.py", st["mono"]),
        Paragraph("Open http://127.0.0.1:8000 in your browser.", st["body"]),
        Spacer(1, 4 * mm),
        Paragraph("5. Alternative One-Command Launchers", st["h2"]),
        Paragraph(
            "Windows:  run_windows.bat<br/>" "Linux/macOS: ./run.sh (chmod +x first)",
            st["body"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("6. Troubleshooting", st["h2"]),
        _section_table(
            [
                ["Symptom", "Resolution"],
                [
                    "numpy segfault (-1073741819) on read_csv",
                    "pip install --only-binary=:all: --force-reinstall --no-deps "
                    "numpy==2.2.1",
                ],
                ["Port 8000 in use", "Change config.PORT or set PORT in .env"],
                [
                    "No model metrics",
                    "Run scripts/train_ai.py; the engine falls back to rules "
                    "otherwise",
                ],
            ]
        ),
    ]
    _build(
        os.path.join(OUT_DIR, "INSTALLATION_GUIDE.pdf"),
        "SecureDT - Installation Guide",
        "Intelligent and Secure Task Scheduling for Digital Twin-Enabled "
        "Edge-Cloud Networks",
        blocks,
    )


def build_review0():
    st = _styles()
    blocks = [
        Paragraph("Deliverable status", st["h2"]),
        Paragraph(
            "SecureDT is a complete, runnable Flask prototype. The "
            "following defines what a review team should see and how to "
            "verify each claim.",
            st["body"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("A. Run the test suite", st["h2"]),
        Paragraph("python tests/run_all.py", st["mono"]),
        Paragraph(
            "Expect: 44+ tests passing covering datasets, digital twin, "
            "risk calibration, GA convergence, schedulers, attacks, "
            "storage, AI and API/security defence.",
            st["body"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("B. Verify risk calibration", st["h2"]),
        Paragraph(
            'python -c "from engine.digital_twin import DigitalTwin; '
            "print(DigitalTwin().apply_attack('MEC-2','DDoS',0.8)"
            "['after'])\"",
            st["mono"],
        ),
        Paragraph("Expect security_risk > 0.8 and status CRITICAL.", st["body"]),
        Spacer(1, 4 * mm),
        Paragraph("C. Verify GA convergence", st["h2"]),
        Paragraph("python engine/scheduler.py", st["mono"]),
        Paragraph(
            "Watch best-fitness decrease (improve) over generations.", st["body"]
        ),
        Spacer(1, 4 * mm),
        Paragraph("D. Verify the live dashboard", st["h2"]),
        _bullet("Start python app.py and open /"),
        _bullet(
            "Generate tasks, run GA, launch an attack on MEC-2, mitigate, "
            "then observe the security timeline update"
        ),
        _bullet(
            "Open /application-security and /system-health to confirm "
            "headers, CSRF and services are reported"
        ),
        Spacer(1, 4 * mm),
        Paragraph("E. Known limitations", st["h2"]),
        _bullet("Single-role / session-ready architecture (not multi-user auth)"),
        _bullet("AI model is offline and trained on synthetic data"),
        _bullet("All attacks are simulated; no external systems are contacted"),
    ]
    _build(
        os.path.join(OUT_DIR, "REVIEW_0_GUIDE.pdf"),
        "SecureDT - Review 0 Guide",
        "Verification checklist for reviewers",
        blocks,
    )


def build_dataset():
    st = _styles()
    blocks = [
        Paragraph(
            "The six synthetic datasets are produced under a fixed seed "
            "(config.DATASET_SEED) so generation is reproducible. They "
            "are labelled, schema-validated and never represent real "
            "individuals or systems.",
            st["body"],
        ),
        Spacer(1, 4 * mm),
        _section_table(
            [
                ["File", "Rows", "Purpose"],
                [
                    "tasks_10000.csv",
                    "10,000",
                    "Workloads: type, size, cpu, "
                    "memory, deadline, sensitivities, label",
                ],
                [
                    "attack_events_5000.csv",
                    "5,000",
                    "Attack events with severity, " "pre/post risk, mitigation",
                ],
                [
                    "resource_states_3000.csv",
                    "3,000",
                    "Resource telemetry: cpu, " "memory, trust, security risk",
                ],
                [
                    "experiment_results_2000.csv",
                    "2,000",
                    "Algorithm runs: " "latency, energy, privacy, security, success",
                ],
                [
                    "ai_training_10000.csv",
                    "10,000",
                    "Feature rows + label for the " "Random Forest",
                ],
                [
                    "storage_security_5000.csv",
                    "5,000",
                    "Storage integrity/risk " "lab rows",
                ],
            ]
        ),
        Spacer(1, 4 * mm),
        Paragraph("Validating the datasets", st["h2"]),
        Paragraph("python scripts/validate_dataset.py", st["mono"]),
        Paragraph("python scripts/dataset_check.py", st["mono"]),
    ]
    _build(
        os.path.join(OUT_DIR, "DATASET_GUIDE.pdf"),
        "SecureDT - Dataset Guide",
        "Synthetic dataset overview and validation",
        blocks,
    )


def build_user():
    st = _styles()
    blocks = [
        Paragraph("Dashboard", st["h2"]),
        Paragraph(
            "Shows current risk, active nodes, GA generation, attack "
            "counters, the live event feed, topology and resource cards. "
            "Auto-refreshes every few seconds.",
            st["body"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("Data Generation / Upload / Processing", st["h2"]),
        Paragraph(
            "Generate synthetic workloads or upload a CSV (validated "
            "for type/size/rows). The processing page walks the "
            "clean → type → feature-extract pipeline.",
            st["body"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("Digital Twin & Infrastructure", st["h2"]),
        Paragraph(
            "Inspect the live mirror of edge/MEC/cloud nodes, their "
            "risk, trust and load, and the three-tier map.",
            st["body"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("GA & AI", st["h2"]),
        Paragraph(
            "Configure population/generations and run the proposed "
            "security-aware GA, then inspect the offline AI risk "
            "analysis of any task with its reasons.",
            st["body"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("Attack & Storage Labs", st["h2"]),
        Paragraph(
            "Launch controlled attacks (DDoS, eavesdropping, tampering "
            "…) on any node, quarantine it, and stop the attack. The "
            "storage lab shows integrity/risk for virtual storages. All "
            "simulated; nothing is touched on your machine or network.",
            st["body"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("Security & Analytics", st["h2"]),
        Paragraph(
            "Review the security timeline, application-security posture "
            "(headers, CSRF, rate limiting, OWASP notes), run "
            "experiment campaigns, and compare the GA against random / "
            "greedy / privacy-aware baselines.",
            st["body"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("System Health & Presentation Mode", st["h2"]),
        Paragraph(
            "/system-health lists services and datasets; /presentation "
            "walks reviewers through the 5 core capabilities.",
            st["body"],
        ),
    ]
    _build(
        os.path.join(OUT_DIR, "USER_MANUAL.pdf"),
        "SecureDT - User Manual",
        "How to operate each module of the prototype",
        blocks,
    )


def build_dataset_manager():
    st = _styles()
    reg = dataset_registry.registry_payload()
    rows = [
        [r["name"], str(r["records_expected"] or ""), r["source"]]
        for r in reg["rows"][:12]
    ]
    blocks = [
        Paragraph(
            "The Dataset Manager page (/datasets) provides a registry "
            "of built-in synthetic datasets plus public IDS references, "
            "one-click big-data generation, and data toolkit pages for "
            "validation, normalisation and quality reports.",
            st["body"],
        ),
        Spacer(1, 4 * mm),
        Paragraph(
            f"Registry ({reg['synth_count']} synthetic, "
            f"{reg['public_count']} public)",
            st["h2"],
        ),
        _section_table([["Dataset", "Rows", "Source"]] + rows),
        Spacer(1, 4 * mm),
        Paragraph("Big-Data Generation", st["h2"]),
        Paragraph(
            f"Streams up to {bigdata.MAX_GENERATION_CAP:,} rows "
            f"deterministically into a chunked CSV (default "
            f"{config.BIGDATA_ROW_OPTIONS[-1]:,} rows). Sampling, "
            f"describe, aggregation and export are chunked so 1M+ rows "
            f"stay within normal memory. Lazy Parquet/SQLite conversion "
            f"is enabled when pyarrow/duckdb are installed.",
            st["body"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("Normalisation", st["h2"]),
        Paragraph(
            "Converts task/attack/storage CSVs into one UnifiedEvent "
            "schema so the timeline, analytics and exporter read a "
            "canonical shape from any source file.",
            st["body"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("Data Quality", st["h2"]),
        Paragraph(
            "Per-file quality reports (missing values, duplicates, "
            "invalid numerics, out-of-range, label balance) with a "
            "0-100 score + grade, cleaning to a new CSV, and "
            "JSON/CSV report export.",
            st["body"],
        ),
    ]
    _build(
        os.path.join(OUT_DIR, "DATASET_MANAGER_GUIDE.pdf"),
        "SecureDT - Dataset Manager Guide",
        "Registry, big-data, normalisation and quality toolkit",
        blocks,
    )


def build_security():
    st = _styles()
    blocks = [
        Paragraph("Runtime protections applied to every request:", st["body"]),
        _bullet(
            "CSRF token validation on all state-changing API calls "
            "(token obtained from /api/state)"
        ),
        _bullet("Per-IP rate limiting with 429 responses"),
        _bullet(
            "Security headers: X-Frame-Options, CSP, nosniff, "
            "referrer-policy, HSTS (HTTPS)"
        ),
        _bullet("Hardened JSON error envelope - no stack traces leaked"),
        _bullet("Upload validation: CSV only, size + row caps"),
        _bullet("Sessions signed with a per-process SECRET_KEY"),
        Spacer(1, 4 * mm),
        Paragraph("Application Security lab", st["h2"]),
        Paragraph(
            "/application-security runs a live posture check "
            f"({len(config.APP_CHECKS)} checks) and grades the result "
            f"A-F.",
            st["body"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("Audit log", st["h2"]),
        Paragraph(
            "The engine.audit_log module records INFO / WARNING / "
            "SECURITY / ERROR / AUDIT events in memory and appends to "
            "a CSV on disk. /audit-logs exposes the live feed with "
            "category filter and export.",
            st["body"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("Attack lab safety", st["h2"]),
        Paragraph(
            "All attacks are simulated inside the digital twin and "
            "virtual storages; nothing touches your network or "
            "machine. Mitigation quarantines the node and raises "
            "integrity/risk counters for demos only.",
            st["body"],
        ),
    ]
    _build(
        os.path.join(OUT_DIR, "SECURITY_GUIDE.pdf"),
        "SecureDT - Security Guide",
        "CSRF, rate limits, headers, audit logging and safe attack labs",
        blocks,
    )


def build_api_config():
    st = _styles()
    blocks = [
        Paragraph("No API keys required for offline/synthetic operation.", st["body"]),
        Spacer(1, 4 * mm),
        Paragraph("Configuration precedence", st["h2"]),
        _bullet("Environment variables: SECRET_KEY, PORT, ZEEK_LOGS_DIR"),
        _bullet("config.yaml next to config.py (see config.yaml.example)"),
        _bullet("Defaults inside config.py"),
        Spacer(1, 4 * mm),
        Paragraph("config.yaml example", st["h2"]),
        Paragraph(
            "server:  { port: 8080 }<br/>"
            "ga:      { population: 40, generations: 50 }<br/>"
            "security:{ rate_limit_per_min: 60, upload_max_rows: 100000 }"
            '<br/>data_source: { label: "SIMULATION DATA" }',
            st["mono"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("Optional live telemetry", st["h2"]),
        Paragraph(
            f"The {telemetry.TelemetryAdapter.__name__} reads Zeek "
            f"log dirs (conn/dns/http/...) when configured; otherwise "
            f"/api/telemetry/status reports simulation mode with a "
            f"clear message. The UI never fails on a missing adapter.",
            st["body"],
        ),
    ]
    _build(
        os.path.join(OUT_DIR, "API_CONFIGURATION_GUIDE.pdf"),
        "SecureDT - API & Configuration Guide",
        "config.yaml, environment variables and telemetry wiring",
        blocks,
    )


def build_experiment():
    st = _styles()
    blocks = [
        Paragraph(
            "Run all four schedulers on a shared workload to compare "
            "success rate, latency, energy, privacy exposure and "
            "security risk.",
            st["body"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("Algorithms", st["h2"]),
        _bullet("random - arbitrary placement"),
        _bullet("greedy - best local score per step"),
        _bullet("privacy_aware - most-trusted best-available node"),
        _bullet("proposed_ga - the security-aware GA in engine/scheduler"),
        Spacer(1, 4 * mm),
        Paragraph("How to read the results", st["h2"]),
        _bullet("Success rate dominates - dropped deadlines rule out a run"),
        _bullet(
            "privacy_aware and proposed_ga beat random/greedy on privacy "
            "exposure and security risk"
        ),
        _bullet("The GA should match or beat greedy on deadline success"),
        Spacer(1, 4 * mm),
        Paragraph("Reproducibility & export", st["h2"]),
        Paragraph(
            "Campaigns are seeded; results append to "
            "experiment_results_2000.csv and are visible in /analytics "
            "and via /api/export/experiments.",
            st["body"],
        ),
    ]
    _build(
        os.path.join(OUT_DIR, "EXPERIMENT_GUIDE.pdf"),
        "SecureDT - Experiment Guide",
        "Algorithm comparison campaigns and export",
        blocks,
    )


def build_ai_model():
    st = _styles()
    blocks = [
        Paragraph(
            "The risk model predicts the security level of an incoming "
            "scheduled task from labelled synthetic workloads.",
            st["body"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("Training", st["h2"]),
        Paragraph("python scripts/train_ai.py", st["mono"]),
        Paragraph(
            "Random Forest via RandomizedSearchCV on "
            "ai_training_10000.csv; writes models/risk_model.pkl and "
            "models/risk_metrics.json (ROC-AUC, F1, importances).",
            st["body"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("Runtime behaviour", st["h2"]),
        _bullet("Predicts level (safe/trained/critical) + confidence"),
        _bullet("Shap feature reasons when shap is installed"),
        _bullet("Deterministic rule fallback when the model file is missing"),
        _bullet("JSON-serialisable metrics via /api/ai/analyze and export"),
        Spacer(1, 4 * mm),
        Paragraph("Validation", st["h2"]),
        Paragraph(
            "tests/test_engine.py verifies schema and "
            "model-or-fallback; system-health reports model readiness.",
            st["body"],
        ),
    ]
    _build(
        os.path.join(OUT_DIR, "AI_MODEL_GUIDE.pdf"),
        "SecureDT - AI Model Guide",
        "Training, explainability and offline fallback",
        blocks,
    )


def main():
    print("Generating SecureDT documentation PDFs ...")
    build_installation()
    build_review0()
    build_dataset()
    build_user()
    build_dataset_manager()
    build_security()
    build_api_config()
    build_experiment()
    build_ai_model()
    print("Done. Files written to docs/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
