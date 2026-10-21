#!/usr/bin/env python3
"""Generate System Architecture PDF."""

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
        os.path.join(OUT_DIR, "SYSTEM_ARCHITECTURE.pdf"),
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

    story.append(Paragraph("SecureDT System Architecture", title_style))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Intelligent and Secure Task Scheduling for Digital Twin-Enabled Edge-Cloud Networks", body))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Version 1.0", body))
    story.append(PageBreak())

    # --- Frontend ---
    story.append(Paragraph("1. Frontend", style_h2()))
    story.append(Paragraph(
        "Jinja2 HTML templates rendered by Django backend. ~35 template files covering all "
        "UI pages (login, register, dashboard, GA, digital twin, attack simulation, storage "
        "attack, analytics, experiments, etc.). Static assets: CSS (style.css), JavaScript "
        "(app.js for UI interactions and API polling), fonts, and images. All client-side "
        "logic communicates with the backend via Django REST Framework API endpoints. No Groq "
        "API key exposed to browser - all Groq calls are backend-only.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- Django ---
    story.append(Paragraph("2. Django Backend", style_h2()))
    story.append(Paragraph(
        "Django 5.2.16 provides the web framework, authentication, admin interface, and REST "
        "API via Django REST Framework. URL routing in securedt/urls.py. Core logic in "
        "SecureDT/app.py (Flask-style route handlers adapted for Django) and engine modules. "
        "Database abstraction via Django ORM (MySQL in production, SQLite in development). "
        "Middleware: Security, Session, CSRF, Auth, Messages. Security headers automatically "
        "set (CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy). Session management "
        "with SECRET_KEY. All secrets (GROQ_API_KEY, SECRET_KEY) loaded from .env environment "
        "variable never hardcoded in source.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- MySQL ---
    story.append(Paragraph("3. MySQL Database", style_h2()))
    story.append(Paragraph(
        "Primary relational database for persistent data: user accounts, task schedules, "
        "attack logs, experiment results, Digital Twin state, analytics data, and model metrics. "
        "Django ORM models for: User (extended auth), Task, AttackEvent, ResourceState, "
        "Storage, Experiment, AI Prediction, Groq Status. Tables include indexes on resource_type, "
        "task_status, attack_type, and experiment_status for performance. Chunking and streaming "
        "for large dataset handling (100K-10M+ rows). MySQL connector (PyMySQL) configured via "
        "DATABASES setting in settings.py. Example configuration placeholders in .env:",
        body))
    story.append(Paragraph(
        "DB_ENGINE=django.db.backends.mysql\nDB_NAME=securedt\nDB_USER=securedt\nDB_PASSWORD=your_password\nDB_HOST=localhost\nDB_PORT=3306",
        mono))
    story.append(Spacer(1, 4 * mm))

    # --- AI ---
    story.append(Paragraph("4. AI Engine", style_h2()))
    story.append(Paragraph(
        "Two-tier AI architecture: Primary - Local scikit-learn Random Forest model "
        "(models/risk_model.pkl) for task risk prediction, explanation, and anomaly scoring. "
        "Optional enhancement - Groq Cloud LLM insight layer (when GROQ_API_KEY configured) "
        "provides natural-language explanations, experiment summaries, and risk commentary. "
        "Core security decisions remain deterministic and application-controlled regardless of "
        "Groq availability. AI features: risk level prediction (safe/trained/critical), confidence "
        "scores, feature importance, deterministic fallback when model file missing, JSON-serializable "
        "metrics via /api/ai/analyze. Training script: scripts/train_ai.py on ai_training_10000.csv.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- Genetic Algorithm ---
    story.append(Paragraph("5. Genetic Algorithm", style_h2()))
    story.append(Paragraph(
        "GA scheduler in engine/genetic_algorithm.py and engine/scheduler.py. Population: 40 "
        "chromosomes (task-to-resource assignments). Fitness function weighted sum: latency (0.25), "
        "energy (0.15), privacy (0.20), security (0.30), deadline (0.10). Tournament selection "
        "(size 3), single-point crossover (rate 0.85), per-gene mutation (rate 0.12), elitism "
        "(top 4 chromosomes). Generations: 50. Output: best chromosome (optimal resource assignment), "
        "fitness history. Baseline comparators: random, greedy, privacy-aware schedules. All "
        "optimization runs are deterministic with seed 42 (config.DATASET_SEED).",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- Digital Twin ---
    story.append(Paragraph("6. Digital Twin", style_h2()))
    story.append(Paragraph(
        "Virtual resource state tracker in engine/digital_twin.py. Tracks CPU, memory, latency, "
        "energy, active tasks, availability, trust, and security-risk for each virtual resource "
        "(LOCAL, MEC-1/2/3, CLOUD). Real/simulated state synchronization with the scheduler. "
        "Risk level property (SAFE/WARNING/HIGH/CRITICAL/QUARANTINED) updates dynamically. Attack "
        "events update resource risk scores and may trigger quarantine. Resource states stored in "
        "MySQL (digital_twin_resourcestate table) and in-memory for real-time access via /api/state. "
        "Three-tier topology: edge (LOCAL), MEC (MEC-1/2/3), cloud (CLOUD) with base nominal "
        "characteristics defined in config.py RESOURCES dict.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- Security ---
    story.append(Paragraph("7. Security", style_h2()))
    story.append(Paragraph(
        "Layered security architecture: Authentication (Django built-in auth, session-based, "
        "detailed in /api/auth/login/register). Authorization (role-based access, superuser vs. "
        "regular user). CSRF protection on all state-changing API requests. XSS prevention via "
        "CSP and output encoding. SQL injection defense via Django ORM parameterized queries. "
        "File upload validation (CSV only, 8MB max, 100K row max, re-encoded on upload). Rate "
        "limiting (per-IP, default 60 requests/minute). Security headers (CSP, X-Frame-Options, "
        "X-Content-Type-Options, Referrer-Policy, HSTS). Audit logging (all events recorded with "
        "category, severity, export to CSV). Groq key protection: key never exposed in browser, "
        "read-only from .env, exception handling, timeout (30s), response validation, logging "
        "without secrets. Attack sandbox: all simulations confined to digital twin and virtual "
        "stores; no real network attacks, filesystem commands, or database operations.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- Dataset Engine ---
    story.append(Paragraph("8. Dataset Engine", style_h2()))
    story.append(Paragraph(
        "Six synthetic datasets (seed 42): tasks_10000.csv, attack_events_5000.csv, "
        "resource_states_3000.csv, experiment_results_2000.csv, ai_training_10000.csv, "
        "storage_security_5000.csv. One-click big-data generation up to 10M+ rows via scripts/"
        "import_real_datasets.py with chunking and streaming. Dataset Manager page (/datasets) "
        "provides registry, validation, normalization to UnifiedEvent schema, quality reports "
        "(missing values, duplicates, invalid numerics, 0-100 score + grade), and JSON/CSV export. "
        "Big-data features: chunked CSV writing, Parquet/DuckDB conversion when pyarrow/duckdb "
        "installed, pagination for UI, background processing via Celery (optional).",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- Celery ---
    story.append(Paragraph("9. Celery & Redis (Optional)", style_h2()))
    story.append(Paragraph(
        "Optional background task queue for large dataset processing, experiment campaigns, and "
        "long-running GA optimizations. Celery with Redis as broker offloads tasks from the web "
        "worker. Fallback: all operations work synchronously in Django development mode when "
        "Celery/Redis unavailable. Not required for core functionality.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- Groq ---
    story.append(Paragraph("10. Groq Cloud LLM", style_h2()))
    story.append(Paragraph(
        "Optional enhancement layer for natural-language explanations, experiment summaries, and "
        "risk commentary. Backend-only integration: Browser <---> Django Backend <---> Groq API. "
        "Key stored exclusively in .env environment variable - never in frontend, source code, "
        "database, or Git. If GROQ_API_KEY missing: app shows 'Groq AI is not configured. Local "
        "AI mode is active.' and continues fully offline. Groq may be used for: AI explanations, "
        "experiment explanations, risk explanations, security-event summaries, natural-language "
        "analytics, research/project assistant. Groq must NOT control: attack execution, filesystem "
        "commands, network attacks, database deletion, system commands, or security bypasses. "
        "Configuration: GROQ_API_KEY, GROQ_MODEL, GROQ_ENABLED, GROQ_TIMEOUT in .env or Django "
        "settings. Default model: llama-3.3-70b-versatile.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- Telemetry ---
    story.append(Paragraph("11. Telemetry (Optional Zeek)", style_h2()))
    story.append(Paragraph(
        "Optional Zeek network security monitoring integration. When ZEEK_LOGS_DIR environment "
        "variable configured, /api/telemetry/status reports live telemetry data. When not configured, "
        "reports simulation mode with clear message. UI never fails on missing adapter. Provides "
        "additional context for security monitoring and attack correlation.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- API ---
    story.append(Paragraph("12. API Endpoints", style_h2()))
    story.append(Paragraph(
        "Django REST Framework API with ~50 endpoints. Core categories: state/health APIs, "
        "auth (login/register/reset), task management (generate, upload, list, retrieve), "
        "scheduling (GA, baselines), attack simulation (start/mitigate/stop), digital twin "
        "state, security monitor, storage attack, routing recalibration, analytics, experiments, "
        "AI analysis and explanation, Groq status, application security posture check (30+ OWASP "
        "checks), audit logs, experiment management. Consistent JSON error envelope - no stack "
        "traces leaked to client. Rate limiting on expensive endpoints. CSRF tokens on state-changing "
        "requests. All API responses follow standard envelope format.",
        body))

    doc.build(story)
    print(f"  SYSTEM_ARCHITECTURE.pdf generated")


if __name__ == "__main__":
    generate()