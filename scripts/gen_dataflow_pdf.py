#!/usr/bin/env python3
"""Generate Data Flow and Implementation PDF."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, PageBreak

BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "SecureDT")
OUT_DIR = os.path.join(BASE_DIR, "docs")
os.makedirs(OUT_DIR, exist_ok=True)

INK = colors.HexColor("#0a0e17")
ACCENT = colors.HexColor("#35e0ff")
SILVER = colors.HexColor("#c0c0c0")
WHITE = colors.white
BLACK = colors.black


def style_h1():
    return ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=16, leading=20, textColor=INK)


def style_h2():
    return ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=INK)


def style_body():
    return ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, leading=13, textColor=BLACK)


def style_mono():
    return ParagraphStyle("mono", fontName="Courier", fontSize=8, leading=11, textColor=BLACK)


def make_table(data, col_widths=[180 * mm]):
    t = Table(data, colWidths=col_widths)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), INK),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEADING", (0, 0), (-1, -1), 12),
                ("GRID", (0, 0), (-1, -1), 0.5, SILVER),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return t


def generate():
    doc = SimpleDocTemplate(
        os.path.join(OUT_DIR, "DATA_FLOW_AND_IMPLEMENTATION.pdf"),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=INK)
    h2 = style_h2()
    body = style_body()
    mono = style_mono()

    story = []

    story.append(Paragraph("SecureDT Data Flow and Implementation Guide", title_style))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Intelligent and Secure Task Scheduling for Digital Twin-Enabled Edge-Cloud Networks", body))
    story.append(Spacer(1, 4 * mm))
    story.append(PageBreak())

    # --- User ---
    story.append(Paragraph("1. USER", style_h2()))
    story.append(Paragraph(
        "User interacts with the system through a web browser. All communication goes through "
        "the Django backend. User actions: login (session-based authentication), register "
        "(new account creation), dashboard (overview of system state), dataset manager "
        "(browse, upload, import datasets), data upload (CSV file upload), data processing "
        "(initiate processing pipeline), AI module (run risk analysis), genetic algorithm "
        "(configure and run scheduling), digital twin (view resource state), task routing "
        "(view/reconfigure task assignments), security monitor (view security events), attack "
        "simulation (launch controlled attacks), storage attack (simulate storage threats), "
        "analytics (view results and charts), experiments (run comparison campaigns), reports "
        "(generate PDF/CSV/JSON reports), system health (check service status), settings "
        "(configure application parameters).",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- Login ---
    story.append(Paragraph("2. LOGIN", style_h2()))
    story.append(Paragraph(
        "Purpose: Authenticate user and establish session.\n"
        "What user sees: Login form (username, password) or dashboard if already authenticated.\n"
        "What buttons do: Submit credentials, link to register password reset.\n"
        "Input: username, password.\n"
        "Output: Session cookie set, redirect to dashboard (or 401 if invalid).\n"
        "Expected result: Authenticated session; all protected endpoints require valid session.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- Dataset ---
    story.append(Paragraph("3. DATASET", style_h2()))
    story.append(Paragraph(
        "Purpose: Manage synthetic and real datasets for the system.\n"
        "What user sees: Dataset registry listing built-in datasets (tasks, attacks, resources, "
        "experiments, AI training, storage security), upload interface, big-data generation "
        "controls.\n"
        "What buttons do: Upload CSV, generate big-data (100K-10M+ rows), validate dataset, "
        "run quality report, normalize to UnifiedEvent schema, view quality score.\n"
        "Input: CSV file upload (max 8MB, max 100K rows, CSV only), dataset selection parameters.\n"
        "Output: Dataset added to registry, quality report generated, normalized schema written.\n"
        "Expected result: Dataset available for task generation, AI training, and analytics.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- Upload ---
    story.append(Paragraph("4. UPLOAD", style_h2()))
    story.append(Paragraph(
        "Purpose: Upload CSV datasets into the system.\n"
        "What user sees: File upload form with validation status.\n"
        "What buttons do: Select file, upload, cancel.\n"
        "Input: CSV file (MIME type validation, max 8MB, max 100K rows).\n"
        "Output: Uploaded file saved as _uploaded.csv, schema detection, quality report.\n"
        "Expected result: CSV validated and stored; non-CSV or oversized files rejected with "
        "error message. File re-encoded to secure format.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- Validate ---
    story.append(Paragraph("5. VALIDATE", style_h2()))
    story.append(Paragraph(
        "Purpose: Validate dataset schema and quality.\n"
        "What user sees: Validation results (missing values, duplicates, invalid numerics, "
        "out-of-range, label balance), quality score (0-100 + grade).\n"
        "What buttons do: Run validation, view details, export report (JSON/CSV).\n"
        "Input: Dataset from upload or registry.\n"
        "Output: Validation report with issues list and overall quality score.\n"
        "Expected result: Quality score displayed; issues categorized and fixable via cleaning "
        "pipeline. Invalid datasets rejected or marked for cleaning.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- Process ---
    story.append(Paragraph("6. PROCESS", style_h2()))
    story.append(Paragraph(
        "Purpose: Execute the data processing pipeline.\n"
        "What user sees: Pipeline stages visualized (Validation → Schema Detection → Cleaning → "
        "Normalization → Feature Engineering → Storage).\n"
        "What buttons do: Start processing, pause/stop, view progress.\n"
        "Input: Validated dataset.\n"
        "Output: Cleaned, normalized dataset in UnifiedEvent schema, stored in datasets/,\n"
        "quality metrics saved, features extracted for AI.\n"
        "Expected result: Processing completes; dataset ready for AI analysis, scheduling, and "
        "analytics. Large datasets processed via chunking/streaming.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- AI ---
    story.append(Paragraph("7. AI", style_h2()))
    story.append(Paragraph(
        "Purpose: Risk prediction and natural-language explanations.\n"
        "What user sees: Risk level (safe/trained/critical) + confidence score for tasks, "
        "explanation buttons, Groq LLM insights (if configured).\n"
        "What buttons do: Analyze task, request explanation, toggle Groq/local AI mode.\n"
        "Input: Task parameters (resource state, attack severity, workload features).\n"
        "Output: Risk prediction from local Random Forest model; if Groq enabled, natural-language "
        "explanation from Groq Cloud LLM.\n"
        "Expected result: Risk score and level displayed; Groq insights shown when available, "
        "local deterministic fallback otherwise. No crash if Groq unavailable.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- Risk ---
    story.append(Paragraph("8. RISK", style_h2()))
    story.append(Paragraph(
        "Purpose: Security risk assessment and monitoring.\n"
        "What user sees: Real-time risk levels per resource (SAFE/WARNING/HIGH/CRITICAL/QUARANTINED), "
        "security timeline, attack events, integrity scores for storage.\n"
        "What buttons do: View audit logs, filter by category/severity, export reports.\n"
        "Input: Digital Twin resource states, attack simulation events, security monitor data.\n"
        "Output: Risk dashboards, alert notifications, exportable reports.\n"
        "Expected result: Current risk state visible; historical trend tracking; audit log "
        "exportable for compliance.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- Digital Twin ---
    story.append(Paragraph("9. DIGITAL TWIN", style_h2()))
    story.append(Paragraph(
        "Purpose: Virtual mirror of edge/MEC/cloud resource states for monitoring and decision "
        "support.\n"
        "What user sees: Resource cards (CPU, memory, latency, trust, risk level), topology map, "
        "real-time state updates, attack impact visualization.\n"
        "What buttons do: Refresh state, apply attack, mitigate attack, quarantine node, "
        "reconfigure resources.\n"
        "Input: Task scheduling decisions, attack events, resource utilization updates.\n"
        "Output: Synchronized resource state; risk scores updated; topology reflected in UI.\n"
        "Expected result: Digital Twin stays in sync with scheduler and attack system; resource "
        "risk drives GA fitness function and rerouting decisions.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- GA ---
    story.append(Paragraph("10. GENETIC ALGORITHM", style_h2()))
    story.append(Paragraph(
        "Purpose: Security-aware task scheduling optimization.\n"
        "What user sees: Population parameters (population, generations, mutation/crossover rates), "
        "fitness history chart, best assignment results, comparison against baselines (random, "
        "greedy, privacy-aware).\n"
        "What buttons do: Run GA, pause, reset, adjust parameters, compare with baselines.\n"
        "Input: Task dataset, resource configuration, GA weights (latency/energy/privacy/security/deadline).\n"
        "Output: Best chromosome (task-to-resource assignment), fitness improvement over generations, "
        "success rate, latency, energy, privacy exposure, security risk metrics.\n"
        "Expected result: GA produces optimized schedule; proposed GA should match or beat greedy "
        "on deadline success and beat random/greedy on privacy exposure and security risk.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- Scheduler ---
    story.append(Paragraph("11. SCHEDULER", style_h2()))
    story.append(Paragraph(
        "Purpose: Task-to-resource assignment across Local, MEC, and Cloud.\n"
        "What user sees: Scheduler controls (algorithm selector: random/greedy/privacy-aware/GA), "
        "resource topology, latency/energy/privacy/security metrics.\n"
        "What buttons do: Select algorithm, run scheduling, view results, compare baselines.\n"
        "Input: Task dataset, current Digital Twin state, GA parameters (if selected).\n"
        "Output: Task assigned to resources; metrics displayed (success rate, latency, energy, "
        "privacy, security risk).\n"
        "Expected result: Scheduling completes; tasks placed; metrics compared against baselines.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- Attack Simulation ---
    story.append(Paragraph("12. ATTACK SIMULATION", style_h2()))
    story.append(Paragraph(
        "Purpose: Simulated attack events for testing detection and response.\n"
        "What user sees: Attack type selector (DDoS, Eavesdropping, Tampering, Data Poisoning, "
        "Credential Abuse), target node selector, severity slider.\n"
        "What buttons do: Launch attack, mitigate, stop, view timeline.\n"
        "Input: Attack type, target resource, severity (0-1).\n"
        "Output: Attack event recorded in audit log; resource risk increased; Digital Twin "
        "updated; security monitor alert triggered; GA reoptimization with new weights; tasks "
        "rerouted to healthier resources.\n"
        "Expected result: Safe software simulation only - no real network attacks, no filesystem "
        "commands, no database operations. All effects confined to digital twin and virtual storages. "
        "Mitigation stops attack, risk decreases, node recovered.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- Storage Attack ---
    story.append(Paragraph("13. STORAGE ATTACK", style_h2()))
    story.append(Paragraph(
        "Purpose: Simulated storage integrity attacks for testing protection and recovery.\n"
        "What user sees: Virtual storages (STORAGE-A: 1000GB encrypted, STORAGE-B: 2000GB encrypted, "
        "STORAGE-C: 500GB unencrypted), integrity risk scores, attack events.\n"
        "What buttons do: Simulate attack, isolate, recover, view integrity status.\n"
        "Input: Storage target, attack type.\n"
        "Output: Integrity risk score updated; attack recorded in audit log; affected storage "
        "isolated; other storages unaffected; tasks rerouted to available storage.\n"
        "Expected result: Safe storage simulation - virtual only, no real data touched. Integrity "
        "restored on recovery; all data remains safe.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- Analytics ---
    story.append(Paragraph("14. ANALYTICS", style_h2()))
    story.append(Paragraph(
        "Purpose: Results visualization and performance analysis.\n"
        "What user sees: Charts (success rate, latency, energy, privacy exposure, security risk) "
        "comparing scheduler algorithms, experiment campaigns, timeline graphs, risk heatmaps.\n"
        "What buttons do: Filter by dataset/algorithm/date range, export data, generate report.\n"
        "Input: Experiment results data, scheduler metrics, attack timeline.\n"
        "Output: Interactive charts (Chart.js), tabular data, export options (CSV, JSON, PDF).\n"
        "Expected result: Visual comparison of proposed GA vs. baselines; experiment campaign "
        "results stored in experiment_results_2000.csv and /api/export/experiments.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- Experiments ---
    story.append(Paragraph("15. EXPERIMENTS", style_h2()))
    story.append(Paragraph(
        "Purpose: Run comparison campaigns between scheduler algorithms with various dataset "
        "sizes and AI configurations.\n"
        "What user sees: Campaign configuration (algorithm selection, dataset size, AI enabled/"
        "disabled), run status, results summary.\n"
        "What buttons do: Start campaign, pause/stop, view results, export results.\n"
        "Input: Baseline algorithms (random, greedy, privacy-aware, proposed GA), dataset size, "
        "AI provider (local/Groq), GA parameters.\n"
        "Output: Experiment results appended to experiment_results_2000.csv; visible in /analytics "
        "and via /api/export/experiments; comparison charts.\n"
        "Expected result: Campaign runs all four schedulers on shared workload; results compare "
        "success rate, latency, energy, privacy exposure, security risk; proposed GA should "
        "outperform on privacy and security; reproducibility via fixed seed.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- Reports ---
    story.append(Paragraph("16. REPORTS", style_h2()))
    story.append(Paragraph(
        "Purpose: Generate documentation and export of results.\n"
        "What user sees: Report type selector (CSV, JSON, PDF), experiment report, system "
        "state report, analytics data.\n"
        "What buttons do: Generate CSV, Generate JSON, Generate PDF, download.\n"
        "Input: Selected data range, report type, experiment campaign ID.\n"
        "Output: Downloadable file in selected format.\n"
        "Expected result: CSV export of experiment metrics; JSON export of system state; PDF "
        "report with charts and metrics for presentations.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- System Health ---
    story.append(Paragraph("17. SYSTEM HEALTH", style_h2()))
    story.append(Paragraph(
        "Purpose: Monitor service status and component readiness.\n"
        "What user sees: List of monitored modules (backend, dataset, digital_twin, ga, ai, "
        "security, attack, storage, analytics), status indicators (online/offline), dataset "
        "counts, model readiness, Celery/Redis status.\n"
        "What buttons do: Refresh, reset, navigate to module pages.\n"
        "Input: System state from engine modules and Django database.\n"
        "Output: Health dashboard with green/yellow/red status for each module.\n"
        "Expected result: All critical modules reported; optional modules (Redis, Celery) shown "
        "with status; model readiness check; Groq configuration status.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- Settings ---
    story.append(Paragraph("18. SETTINGS", style_h2()))
    story.append(Paragraph(
        "Purpose: Configure application parameters.\n"
        "What user sees: AI provider selection (localfeatures/groq/hybrid), Groq model selection, "
        "GA parameters (population, generations, weights), resource configuration, upload limits, "
        "rate limiting, dataset seed, debug mode, data source label.\n"
        "What buttons do: Save configuration, reset to defaults, test Groq connection.\n"
        "Input: Environment variables (.env) and Django settings.\n"
        "Output: Configuration applied; restart may required for some changes.\n"
        "Expected result: Settings persist across restarts via .env; Groq key optional; local AI "
        "mode works without key; all secrets in .env not in source code.",
        body))

    doc.build(story)
    print(f"  DATA_FLOW_AND_IMPLEMENTATION.pdf generated")


if __name__ == "__main__":
    generate()