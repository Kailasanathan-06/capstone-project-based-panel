#!/usr/bin/env python3
"""Generate Complete Installation and Usage Guide PDF."""

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
BG = colors.HexColor("#0a0e17")
ACCENT = colors.HexColor("#35e0ff")
WHITE = colors.white
BLACK = colors.black
SILVER = colors.HexColor("#c0c0c0")


def style_h1():
    return ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=INK)


def style_h2():
    return ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=INK)


def style_body():
    return ParagraphStyle("body", fontName="Helvetica", fontSize=10, leading=14, textColor=BLACK)


def style_mono():
    return ParagraphStyle("mono", fontName="Courier", fontSize=9, leading=13, textColor=BLACK)


def make_table(data, col_widths=[180 * mm]):
    t = Table(data, colWidths=col_widths)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), INK),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), 0.5, SILVER),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return t


def generate():
    doc = SimpleDocTemplate(
        os.path.join(OUT_DIR, "COMPLETE_INSTALLATION_AND_USAGE_GUIDE.pdf"),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "title", fontName="Helvetica-Bold", fontSize=20, leading=26, textColor=INK
    )
    h2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=INK)
    body = ParagraphStyle("body", fontName="Helvetica", fontSize=10, leading=14, textColor=BLACK)
    mono = ParagraphStyle("mono", fontName="Courier", fontSize=9, leading=13, textColor=BLACK)

    story = []

    # Title
    story.append(Paragraph("SecureDT - Complete Installation and Usage Guide", title_style))
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("Intelligent and Secure Task Scheduling for Digital Twin-Enabled Edge-Cloud Networks", body))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Version 1.0 | Django + MySQL + Groq AI + Genetic Algorithm", body))
    story.append(Spacer(1, 4 * mm))

    # SECTION 1: Project Overview
    story.append(Paragraph("SECTION 1: PROJECT OVERVIEW", style_h2()))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "Problem: Efficient task scheduling across edge, MEC, and cloud resources with security "
        "risk optimization.",
        body))
    story.append(Paragraph(
        "Objective: Provide an intelligent, secure task scheduling system that optimizes for "
        "latency, energy consumption, privacy preservation, and security risk while supporting "
        "deployment across Local, MEC, and Cloud environments.",
        body))
    story.append(Paragraph(
        "Architecture: Flask/Django backend with Django REST Framework API, MySQL database, "
        "Genetic Algorithm scheduler, Digital Twin resource tracker, AI risk engine (local RF + "
        "optional Groq LLM), attack simulation (safe software simulation), storage attack "
        "simulation, analytics, and experiment frameworks.",
        body))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "Technology Stack: Python 3.13, Django 5.2, MySQL, SQLite, PyMySQL, "
        "numpy, pandas, scikit-learn, reportlab, fpdf2, Flask, "
        "Git, HTML5/CSS3/JQuery, Chart.js for analytics visualizations.",
        body))
    story.append(Spacer(1, 8 * mm))

    # SECTION 2: Software Requirements
    story.append(Paragraph("SECTION 2: SOFTWARE REQUIREMENTS", style_h2()))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Python: 3.10 or newer (64-bit recommended)", body))
    story.append(Paragraph("Django: 5.2 LTS (or 4.x+)", body))
    story.append(Paragraph("MySQL: 8.0+ with PyMySQL or mysql-connector-python", body))
    story.append(Paragraph("Redis: Optional (for Celery fallback)", body))
    story.append(Paragraph("Node.js: Not required (all frontend in Django templates)", body))
    story.append(Paragraph("Browser: Chrome, Edge, or Firefox (latest)", body))
    story.append(Paragraph("Git: For version control and deployment", body))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Python Packages (from requirements.txt):", body))
    story.append(Paragraph("Flask>=2.3,<4.0", body))
    story.append(Paragraph("Flask-Cors>=4.0", body))
    story.append(Paragraph("numpy>=2.0", body))
    story.append(Paragraph("pandas>=2.0", body))
    story.append(Paragraph("scikit-learn>=1.3", body))
    story.append(Paragraph("reportlab>=4.0", body))
    story.append(Paragraph("fpdf2>=2.7", body))
    story.append(Spacer(1, 8 * mm))

    # SECTION 3: Project Installation
    story.append(Paragraph("SECTION 3: PROJECT INSTALLATION", style_h2()))
    story.append(Spacer(1, 4 * mm))
    installation_steps = [
        ("Step 1: Extract ZIP", "Unzip the project archive to your desired location."),
        ("Step 2: Open terminal", "Navigate to the project directory: cd path/to/securedt"),
        ("Step 3: Create virtual environment", "python -m venv .venv"),
        ("Step 4: Activate environment", "Windows: .venv\\Scripts\\activate  |  Linux/macOS: source .venv/bin/activate"),
        ("Step 5: Install requirements", "pip install -r requirements.txt"),
        ("Step 6: Configure .env", "cp .env.example .env  Edit .env with your settings"),
        ("Step 7: Create MySQL database", "CREATE DATABASE securedt; CREATE USER 'securedt'@'%' IDENTIFIED BY 'password'; GRANT ALL PRIVILEGES ON securedt.* TO 'securedt'@'%';"),
        ("Step 8: Configure MySQL", "Update .env with DB settings: DB_ENGINE=django.db.backends.mysql, DB_NAME=securedt, DB_USER=securedt, DB_PASSWORD=password, DB_HOST=localhost, DB_PORT=3306"),
        ("Step 9: Run migrations", "python manage.py makemigrations  python manage.py migrate"),
        ("Step 10: Create superuser", "python manage.py createsuperuser"),
        ("Step 11: Run Django", "python manage.py runserver  Open http://127.0.0.1:8000 in browser"),
    ]
    for i, (step, desc) in enumerate(installation_steps, 1):
        story.append(Paragraph(f"{i}. {step}", style_body()))
        story.append(Paragraph(f"   {desc}", style_mono()))
    story.append(Spacer(1, 8 * mm))

    # SECTION 4: MySQL Database
    story.append(Paragraph("SECTION 4: MYSQL DATABASE", style_h2()))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Database creation:", body))
    story.append(Paragraph("username: securedt (or your chosen username)", body))
    story.append(Paragraph("password: your_secure_password (set in .env)", body))
    story.append(Paragraph("host: localhost", body))
    story.append(Paragraph("port: 3306 (default MySQL port)", body))
    story.append(Paragraph("migration: python manage.py makemigrations && python manage.py migrate", body))
    story.append(Paragraph("tables: auth_user, auth_group, auth_permission, auth_user_contenttypes, django_admin_log, django_content_type, django_migrations, django_session, plus application tables: api_state, analytics_experiment, attacks_attack, storage_storage, tasks_task, digital_twin_resourcestate, ai_riskprediction, groq_status", body))
    story.append(Paragraph("indexes: Primary keys on all ID columns; indexes on resource_type, task_status, attack_type, experiment_status for performance", body))
    story.append(Paragraph("Example configuration with placeholders:", body))
    story.append(Paragraph(
        "DEFAULT: ENGINE=django.db.backends.sqlite3 NAME=BASE_DIR/db.sqlite3 (development)\n"
        "MYSQL: ENGINE=django.db.backends.mysql NAME=securedt USER=securedt PASSWORD=your_password HOST=localhost PORT=3306",
        mono))
    story.append(Spacer(1, 8 * mm))

    # SECTION 5: User Account
    story.append(Paragraph("SECTION 5: USER ACCOUNT", style_h2()))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Register: New users can register via /register with username, password, and email.", body))
    story.append(Paragraph("Login: Authenticated users access via /login with username and password.", body))
    story.append(Paragraph("Logout: /logout ends the session.", body))
    story.append(Paragraph("Password reset: Django built-in password reset flow via /password-reset.", body))
    story.append(Paragraph("Profile: User profile accessible after login; displays role and preferences.", body))
    story.append(Spacer(1, 8 * mm))

    # SECTION 6: Dataset System
    story.append(Paragraph("SECTION 6: DATASET SYSTEM", style_h2()))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Dataset sources: Synthetic datasets (seed-based reproducible) and optional live telemetry imports.", body))
    story.append(Paragraph("Download: python scripts/generate_dataset.py --tasks 10000 --attack 5000 --resource 3000", body))
    story.append(Paragraph("Import: CSV upload validated for type, size, and row count; normalized to UnifiedEvent schema.", body))
    story.append(Paragraph("Validation: Schema detection, missing value handling, type checking, label balance verification.", body))
    story.append(Paragraph("Normalization: All datasets converted to canonical UnifiedEvent schema with consistent fields.", body))
    story.append(Paragraph("Processing: Cleaning → Feature Engineering → Storage in unified format.", body))
    story.append(Paragraph("Storage: CSV files in datasets/; quality reports in JSON/CSV export.", body))
    story.append(Spacer(1, 8 * mm))

    # SECTION 7: Large Dataset Processing
    story.append(Paragraph("SECTION 7: LARGE DATASET PROCESSING", style_h2()))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("The system supports datasets from 100K to 10M+ rows using:", body))
    story.append(Paragraph("• Chunking: Data streamed in manageable chunks (default PAGE_SIZE=50)", body))
    story.append(Paragraph("• Streaming: Read-process-write pattern never loads all rows into memory", body))
    story.append(Paragraph("• Parquet: Optional pyarrow/duckdb conversion for columnar efficiency", body))
    story.append(Paragraph("• DuckDB: SQL query engine on CSVs for ad-hoc analysis without full import", body))
    story.append(Paragraph("• MySQL metadata: Key metrics cached in database for fast UI rendering", body))
    story.append(Paragraph("• Background processing: Long operations via Celery (optional) with Redis broker", body))
    story.append(Paragraph("• Pagination: Frontend never sends/receives millions of rows", body))
    story.append(Spacer(1, 8 * mm))

    # SECTION 8: AI
    story.append(Paragraph("SECTION 8: AI", style_h2()))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Dataset preparation: Features and labels extracted from UnifiedEvent schema CSV.", body))
    story.append(Paragraph("Features: cpu, memory, latency, trust, security_risk, attack_severity, privacy, workload, storage_integrity, attack_exposure", body))
    story.append(Paragraph("Training: RandomForestClassifier via sklearn RandomizedSearchCV on ai_training_10000.csv", body))
    story.append(Paragraph("Validation: 80/20 train-test split; ROC-AUC, F1-score, feature importance reported", body))
    story.append(Paragraph("Testing: /api/ai/analyze endpoint returns risk level + confidence", body))
    story.append(Paragraph("Model saving: models/risk_model.pkl + models/risk_metrics.json", body))
    story.append(Paragraph("Prediction: Risk level (safe/trained/critical) + confidence score (0-1)", body))
    story.append(Paragraph("Explanation: Local SHAP values when available; deterministic rule-based reasons otherwise", body))
    story.append(Spacer(1, 8 * mm))

    # SECTION 9: Groq
    story.append(Paragraph("SECTION 9: GROQ", style_h2()))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Local AI: scikit-learn Random Forest - works without any API key", body))
    story.append(Paragraph("Groq AI: Optional LLM insight layer via Groq Cloud API", body))
    story.append(Paragraph("Why Groq is optional: Core functionality works offline; Groq adds natural-language explanations only", body))
    story.append(Paragraph("Where API key goes: .env file ONLY - never in source, HTML, JS, CSS, or database", body))
    story.append(Paragraph("How backend calls Groq: /api/ai/explain and /api/ai/analyze endpoints forward requests via backend", body))
    story.append(Paragraph("How frontend never sees the key: Backend-only; key read from environment at runtime", body))
    story.append(Paragraph("Fallback mode: If Groq unavailable, app auto-falls back to local AI without crash", body))
    story.append(Spacer(1, 8 * mm))

    # SECTION 10: Genetic Algorithm
    story.append(Paragraph("SECTION 10: GENETIC ALGORITHM", style_h2()))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Population: 40 chromosomes (task-to-resource assignments)", body))
    story.append(Paragraph("Fitness: Weighted combination of latency (0.25), energy (0.15), privacy (0.20), security (0.30), deadline (0.10)", body))
    story.append(Paragraph("Selection: Tournament selection (size 3)", body))
    story.append(Paragraph("Crossover: Single-point crossover (rate 0.85)", body))
    story.append(Paragraph("Mutation: Per-gene mutation (rate 0.12)", body))
    story.append(Paragraph("Elitism: Top 4 chromosomes carried to next generation", body))
    story.append(Paragraph("Generations: 50 iterations of optimization", body))
    story.append(Paragraph("Output: Best chromosome (optimal resource assignment), fitness history chart", body))
    story.append(Spacer(1, 8 * mm))

    # SECTION 11: Digital Twin
    story.append(Paragraph("SECTION 11: DIGITAL TWIN", style_h2()))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Real/simulated state: Virtual mirror of edge/MEC/cloud resource states (CPU, memory, latency, trust, security_risk)", body))
    story.append(Paragraph("Synchronization: Digital Twin updated after each scheduling decision, attack, and mitigation", body))
    story.append(Paragraph("Monitoring: /api/state and /system-health endpoints report current topology and risk levels", body))
    story.append(Paragraph("State update: Automatic updates on task assignment, completion, attack events", body))
    story.append(Paragraph("Security event: Attack events update risk scores, may quarantine nodes", body))
    story.append(Spacer(1, 8 *mm))

    # SECTION 12: Task Scheduling
    story.append(Paragraph("SECTION 12: TASK SCHEDULING", style_h2()))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Local: Default scheduler on Django server", body))
    story.append(Paragraph("MEC: Edge resource allocation with low latency targets", body))
    story.append(Paragraph("Cloud: Centralized scheduling with higher capacity but higher latency", body))
    story.append(Paragraph("Factors: latency, energy, privacy, security risk, deadline compliance", body))
    story.append(Spacer(1, 8 * mm))

    # SECTION 13: Attack Simulation
    story.append(Paragraph("SECTION 13: ATTACK SIMULATION", style_h2()))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("This is a SAFE SOFTWARE SIMULATION: No real attack occurs. No network traffic is sent.", body))
    story.append(Paragraph("Attacker: Simulated threat actor targeting a resource node", body))
    story.append(Paragraph("Target: Selected MEC or Cloud resource in the Digital Twin", body))
    story.append(Paragraph("Risk increase: Security risk score increases based on attack severity", body))
    story.append(Paragraph("Detection: Security monitor detects anomaly, raises alert", body))
    story.append(Paragraph("Digital Twin update: Resource state updated with new risk profile", body))
    story.append(Paragraph("AI analysis: Local AI provides risk explanation", body))
    story.append(Paragraph("GA reoptimization: Scheduler re-runs GA with updated risk weights", body))
    story.append(Paragraph("Rerouting: Tasks rerouted to healthier resources", body))
    story.append(Paragraph("Recovery: Mitigation stops attack, risk decreases, node recovered", body))
    story.append(Spacer(1, 8 * mm))

    # SECTION 14: Storage Attack
    story.append(Paragraph("SECTION 14: STORAGE ATTACK", style_h2()))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Virtual storage: STORAGE-A, STORAGE-B, STORAGE-C in simulated environment", body))
    story.append(Paragraph("Simulated attacker: Attempts integrity violations on virtual storage", body))
    story.append(Paragraph("Attack event: Recorded in audit log; integrity risk score updated", body))
    story.append(Paragraph("Detection: Storage integrity monitoring detects anomalies", body))
    story.append(Paragraph("Protection: Virtual isolation and risk containment", body))
    story.append(Paragraph("Isolation: Affected storage quarantined; other storages unaffected", body))
    story.append(Paragraph("Safe storage: All data remains safe; simulation only", body))
    story.append(Paragraph("Rerouting: Tasks redirected to available storage", body))
    story.append(Paragraph("Recovery: Integrity restored; storage returned to normal state", body))
    story.append(Spacer(1, 8 * mm))

    # SECTION 15: Security
    story.append(Paragraph("SECTION 15: SECURITY", style_h2()))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Authentication: Django built-in auth with session-based login/register/logout", body))
    story.append(Paragraph("Authorization: Role-based access control; superuser vs. regular user", body))
    story.append(Paragraph("CSRF: Protected on all state-changing requests via token", body))
    story.append(Paragraph("XSS: Content Security Policy and output encoding prevent XSS", body))
    story.append(Paragraph("SQL injection defense: Parameterized queries; Django ORM prevents SQLi", body))
    story.append(Paragraph("File upload: CSV only, 8MB max, 100K row max, re-encoded on upload", body))
    story.append(Paragraph("Rate limiting: Per-IP limiter (default 60 requests/minute)", body))
    story.append(Paragraph("Session security: Signed with SECRET_KEY; HttpOnly/SameSite cookies", body))
    story.append(Paragraph("Security headers: CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, HSTS", body))
    story.append(Paragraph("Audit logs: All events recorded with category, severity, and export capability", body))
    story.append(Spacer(1, 8 * mm))

    # SECTION 16: Experiments
    story.append(Paragraph("SECTION 16: EXPERIMENTS", style_h2()))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Baseline: random, greedy, privacy-aware schedulers", body))
    story.append(Paragraph("Proposed: Security-aware Genetic Algorithm", body))
    story.append(Paragraph("Dataset size: Configurable from 100 to 1M+ tasks", body))
    story.append(Paragraph("AI: Risk model predictions integrated into fitness function", body))
    story.append(Paragraph("GA: Population, generations, crossover, mutation parameters", body))
    story.append(Paragraph("Metrics: Success rate, latency, energy, privacy exposure, security risk", body))
    story.append(Paragraph("Results: Comparison charts in /analytics and export to CSV/JSON/PDF", body))
    story.append(Spacer(1, 8 * mm))

    # SECTION 17: Performance
    story.append(Paragraph("SECTION 17: PERFORMANCE", style_h2()))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Latency: Typically < 200ms for API responses; GA optimization ~ 5-30 seconds", body))
    story.append(Paragraph("Processing time: Dataset import scales with chunking; 1M rows ~ 30-60 seconds", body))
    story.append(Paragraph("Energy: Optimized scheduling reduces energy consumption vs. random placement", body))
    story.append(Paragraph("Privacy: Feature engineering preserves privacy; no personal data transmitted", body))
    story.append(Paragraph("Security: Multi-layer defense; all secrets in environment variables", body))
    story.append(Paragraph("Scalability: Designed for 10K+ tasks; large datasets via chunking/streaming", body))
    story.append(Spacer(1, 8 * mm))

    # SECTION 18: Report Generation
    story.append(Paragraph("SECTION 18: REPORT GENERATION", style_h2()))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("CSV: Experiment results, analytics data, task summaries", body))
    story.append(Paragraph("JSON: API responses, system state exports", body))
    story.append(Paragraph("PDF: Generated experiment reports with charts and metrics", body))
    story.append(Paragraph("Charts: Chart.js-based visualizations in dashboard and analytics pages", body))
    story.append(Paragraph("Experiment reports: /api/export/experiments generates full report", body))
    story.append(Spacer(1, 8 * mm))

    # SECTION 19: Troubleshooting
    story.append(Paragraph("SECTION 19: TROUBLESHOOTING", style_h2()))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("MySQL not connecting: Verify .env DB settings, MySQL service running, port 3306 open", body))
    story.append(Paragraph("Migration error: Run makemigrations first; ensure models match", body))
    story.append(Paragraph("Django error: Check manage.py and settings.py consistency", body))
    story.append(Paragraph("Groq key missing: Set GROQ_API_KEY in .env; app falls back to local AI", body))
    story.append(Paragraph("Groq unavailable: Set AI_PROVIDER=localfeatures in .env", body))
    story.append(Paragraph("Model missing: Run scripts/train_ai.py to generate models/risk_model.pkl", body))
    story.append(Paragraph("Dataset missing: Generate with scripts/generate_dataset.py or upload CSV", body))
    story.append(Paragraph("Celery unavailable: System works in synchronous mode; optional Celery/Redis for async", body))
    story.append(Paragraph("Redis unavailable: Fallback to database queue or synchronous processing", body))
    story.append(Paragraph("WebGL unavailable: 3D infrastructure runs in Canvas2D fallback mode", body))
    story.append(Paragraph("PDF generation error: Ensure reportlab is installed; check write permissions", body))
    story.append(Spacer(1, 8 * mm))

    # SECTION 20: How to Start
    story.append(Paragraph("SECTION 20: HOW TO START", style_h2()))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("1. Extract ZIP", "Unzip the project archive to your desired location."))
    story.append(Paragraph("2. Install Python", "Python 3.13+ from python.org"))
    story.append(Paragraph("3. Install MySQL", "MySQL 8.0+ from mysql.com"))
    story.append(Paragraph("4. Create database", "CREATE DATABASE securedt; CREATE USER 'securedt'@'%' IDENTIFIED BY 'password';"))
    story.append(Paragraph("5. Create .env", "cp .env.example .env  Edit with your DB, Groq, and app settings"))
    story.append(Paragraph("6. Add GROQ_API_KEY", "GROQ_API_KEY=YOUR_KEY_HERE (optional; local AI works without it)"))
    story.append(Paragraph("7. Install dependencies", "pip install -r requirements.txt"))
    story.append(Paragraph("8. Run migrations", "python manage.py makemigrations && python manage.py migrate"))
    story.append(Paragraph("9. Create superuser", "python manage.py createsuperuser"))
    story.append(Paragraph("10. Start server", "python manage.py runserver"))
    story.append(Paragraph("11. Open browser", "http://127.0.0.1:8000"))
    story.append(Paragraph("12. Register", "Create a new account or use: username=admin, password=admin123"))
    story.append(Paragraph("13. Login", "Access the dashboard and all features"))
    story.append(Paragraph("14. Run Demo", "Go to /experiments to compare schedulers, /attack to simulate attacks, /digital-twin to monitor resources"))

    doc.build(story)
    print(f"  COMPLETE_INSTALLATION_AND_USAGE_GUIDE.pdf generated")


if __name__ == "__main__":
    generate()