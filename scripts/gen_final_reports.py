#!/usr/bin/env python3
"""
gen_final_reports.py
====================
Generates the two remaining final-deliverable PDFs into docs/:
    REVIEW_0_PRESENTATION_GUIDE.pdf
    PROJECT_FINAL_REPORT.pdf
"""

import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs"
)
os.makedirs(OUT_DIR, exist_ok=True)

INK = colors.HexColor("#0a0e17")
ACCENT = colors.HexColor("#35e0ff")


def _styles():
    styles = getSampleStyleSheet()

    def make(name, **kw):
        base = {
            "fontName": "Helvetica",
            "fontSize": 10,
            "leading": 15,
            "textColor": colors.black,
        }
        base.update(kw)
        return ParagraphStyle(name, **base)

    return {
        "h1": make("T", fontName="Helvetica-Bold", fontSize=20, leading=26, textColor=INK, spaceAfter=6),
        "h2": make("H2", fontName="Helvetica-Bold", fontSize=13, leading=17, textColor=INK, spaceBefore=10, spaceAfter=5),
        "body": make("B", fontSize=10, leading=15),
        "bullet": make("Bul", fontSize=10, leading=15, leftIndent=12, bulletIndent=4),
        "mono": make("M", fontName="Courier", fontSize=8.5, leading=12),
    }


def _title(doc_title, subtitle):
    from reportlab.platypus import Table as T
    inner = T(
        [
            [Paragraph(doc_title, ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=22, leading=28, textColor=colors.white))],
            [Paragraph(subtitle, ParagraphStyle("s", fontName="Helvetica", fontSize=11, leading=14, textColor=colors.HexColor("#dce7ff")))],
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
    outer = T([[inner]], colWidths=[170 * mm])
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
                ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c7d5ea")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
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
    doc.build([_title(title, subtitle), Spacer(1, 8 * mm)] + blocks)
    print(f"  {os.path.basename(path)} generated")


def _bullet(s, bullet="\u2022"):
    st = _styles()
    return Paragraph(f"<bullet>{bullet}</bullet>{s}", st["bullet"], bulletText=bullet)


def build_review_presentation():
    st = _styles()
    blocks = [
        Paragraph(
            "Suggested walk-through for a Review 0 demo. Start the app, then "
            "work through each capability below so reviewers can verify every "
            "claim live.",
            st["body"],
        ),
        Spacer(1, 5 * mm),
        Paragraph("1. Dashboard", st["h2"]),
        Paragraph(
            "Open / - shows current security risk, online MEC nodes, GA "
            "progress, attack counters, live event feed, topology and "
            "resource cards. Auto-refreshes via /api/state polling.",
            st["body"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("2. MEC Infrastructure", st["h2"]),
        Paragraph(
            "Open /mec-infrastructure. Show the MEC registry, pairing-code "
            "registration, heartbeat-based ONLINE/OFFLINE status and token "
            "rotation settings (HEARTBEAT_INTERVAL_SECONDS=10, "
            "HEARTBEAT_TIMEOUT_SECONDS=30, MAX_TOKEN_AGE_SECONDS=3600).",
            st["body"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("3. Digital Twin & Attack Response", st["h2"]),
        Paragraph(
            "Open /digital-twin and /attack-simulation. Launch a simulated "
            "attack (DDoS, Eavesdropping, Tampering, Data_Poisoning, "
            "Credential_Abuse) on a node, watch risk climb, quarantine the "
            "node, stop the attack and watch risk decay.",
            st["body"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("4. Genetic Algorithm Scheduling", st["h2"]),
        _bullet("Open /genetic-algorithm; configure population (40), "
                "generations (50), mutation (0.12), crossover (0.85)."),
        _bullet("Run the proposed security-aware GA and show best-fitness "
                "decreasing per generation."),
        _bullet("Open /task-routing to see placement and the "
                "OFFLINE-never-assignable rule."),
        Spacer(1, 4 * mm),
        Paragraph("5. AI Intelligence", st["h2"]),
        _bullet("Open /ai-intelligence and analyze a task -> risk level "
                "(safe/trained/critical) + confidence + feature reasons."),
        _bullet("Show models/risk_metrics.json and the deterministic rule "
                "fallback when the .pkl is absent."),
        _bullet("Optional: with GROQ_API_KEY + AI_PROVIDER=groq, LLM "
                "insight appears on the page."),
        Spacer(1, 4 * mm),
        Paragraph("6. Datasets, Analytics & Experiments", st["h2"]),
        _bullet("/datasets -> registry, big-data generation (up to 10M), "
                "quality, normalization."),
        _bullet("/analytics -> compare proposed_ga vs random / greedy / "
                "privacy_aware."),
        _bullet("/experiments-run documented in EXPERIMENT_GUIDE.pdf "
                "(campaigns append to experiment_results_2000.csv)."),
        Spacer(1, 4 * mm),
        Paragraph("7. Security Controls", st["h2"]),
        Paragraph(
            "Explain the enforced protections: Django CSRF, session + token "
            "auth on /api, headers set by Django middleware, upload "
            "validation (CSV only, max 8 MB / 100,000 rows), signed "
            "sessions, and audit logging to datasets/audit_log.csv.",
            st["body"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("Key numbers to state", st["h2"]),
        _section_table(
            [
                ["Item", "Value"],
                ["GA weights", "latency 0.25, energy 0.15, privacy 0.20, security 0.30, deadline 0.10"],
                ["GA operators", "tournament(3), crossover 0.85, mutation 0.12, elitism 4"],
                ["Heartbeat / timeout", "10 s / 30 s"],
                ["Token rotation", "enabled, max age 3600 s"],
                ["Risk levels", "LOW/MEDIUM/HIGH/CRITICAL at 0.00/0.30/0.60/0.80"],
                ["Upload cap", "8 MB, 100,000 rows"],
                ["MEC build", "PyInstaller -> dist/MEC_Agent.exe"],
            ]
        ),
    ]
    _build(
        os.path.join(OUT_DIR, "REVIEW_0_PRESENTATION_GUIDE.pdf"),
        "SecureDT - Review 0 Presentation Guide",
        "Live demo walk-through for reviewers",
        blocks,
    )


def build_final_report():
    st = _styles()
    blocks = [
        Paragraph(
            "SecureDT is a research prototype for intelligent and secure "
            "task scheduling in digital twin-enabled edge-cloud networks. "
            "This report summarises the delivered system, its engineering, "
            "and the evaluation evidence.",
            st["body"],
        ),
        Spacer(1, 5 * mm),
        Paragraph("1. Delivered System", st["h2"]),
        _bullet("Django 5.2 server exposing pages and a token-authenticated "
                "REST API (securedt project)."),
        _bullet("MEC agent (Python/PyInstaller) with pairing-code "
                "registration, heartbeat lifecycle, task execution and "
                "auto-reconnect."),
        _bullet("Core engines: digital twin, genetic algorithm scheduler, "
                "risk engine, attack simulator, security monitor, "
                "telemetry, AI (Random Forest + optional Groq LLM)."),
        _bullet("Cloud backend: Google Drive integration proxied through the "
                "Django cloud app."),
        _bullet("Data pipeline: dataset registry, generation, validation, "
                "quality, normalization, big-data streaming (up to 10M rows)."),
        Spacer(1, 4 * mm),
        Paragraph("2. Technical Stack", st["h2"]),
        _section_table(
            [
                ["Layer", "Technology"],
                ["Backend", "Django 5.2, Django REST Framework, CORS, channels (optional), MySQL 8 (securetdb)"],
                ["ML", "scikit-learn Random Forest (RandomizedSearchCV), shap/xgboost optional, Groq Cloud LLM (optional)"],
                ["Cloud", "Google Drive API via service account"],
                ["MEC agent", "psutil, requests, PyInstaller"],
                ["Frontend", "Vanilla ES6 + Pico.css, Chart.js, Three.js"],
            ]
        ),
        Spacer(1, 4 * mm),
        Paragraph("3. Scheduling & Optimization", st["h2"]),
        Paragraph(
            "The proposed scheduler is a security- and privacy-aware genetic "
            "algorithm minimizing latency, energy, privacy loss, security "
            "risk and a quadratic deadline penalty. OFFLINE MECs are never "
            "assignable. Baselines: random, greedy, privacy_aware.",
            st["body"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("4. Security Engineering", st["h2"]),
        _bullet("CSRF protection on state-changing calls; session + DRF token "
                "authentication on /api."),
        _bullet("Django security middleware; signed sessions; secrets kept in "
                ".env (never committed)."),
        _bullet("Upload validation: CSV only, 8 MB and 100,000-row caps."),
        _bullet("MEC auth with rotating bearer tokens (max age 3600 s)."),
        _bullet("Structured audit log (datasets/audit_log.csv)."),
        _bullet("All attack simulations are virtual; nothing external is "
                "touched."),
        Spacer(1, 4 * mm),
        Paragraph("5. Evaluation Method", st["h2"]),
        Paragraph(
            "Four schedulers are compared on shared seeded workloads via "
            "experiment campaigns, measuring success rate, average latency, "
            "energy, privacy exposure and security risk. Results append to "
            "datasets/experiment_results_2000.csv and are visualised in "
            "/analytics.",
            st["body"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("6. Reproducibility", st["h2"]),
        _bullet("Fixed seed config.DATASET_SEED = 42; deterministic GA RNG."),
        _bullet("python scripts/generate_dataset.py --tasks 10000, "
                "python scripts/train_ai.py."),
        _bullet("python tests/run_all.py runs the unit + integration suite."),
        Spacer(1, 4 * mm),
        Paragraph("7. Limitations", st["h2"]),
        _bullet("Single Django instance; not distributed."),
        _bullet("Energy is software-estimated; hardware meters needed for "
                "precise figures."),
        _bullet("Attack simulation is digital-twin-only."),
        _bullet("Rate limiting and CSP are configured as constants/report "
                "cards; a production deployment should add enforced limiter "
                "middleware."),
    ]
    _build(
        os.path.join(OUT_DIR, "PROJECT_FINAL_REPORT.pdf"),
        "SecureDT - Project Final Report",
        "Intelligent and Secure Task Scheduling for Digital Twin-Enabled Edge-Cloud Networks",
        blocks,
    )


def main():
    print("Generating final deliverables ...")
    build_review_presentation()
    build_final_report()
    print("Done.")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())