#!/usr/bin/env python3
"""Create COMPLETE_INSTALLATION_AND_USAGE_GUIDE.pdf"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "SecureDT", "docs")
os.makedirs(OUT_DIR, exist_ok=True)

doc = SimpleDocTemplate(
    os.path.join(OUT_DIR, "COMPLETE_INSTALLATION_AND_USAGE_GUIDE.pdf"),
    pagesize=A4,
    leftMargin=20,
    rightMargin=20,
    topMargin=18,
    bottomMargin=18,
)

styles = getSampleStyleSheet()
h2 = ParagraphStyle('h2', fontName='Helvetica-Bold', fontSize=13, leading=16, textColor=colors.HexColor('#0a0e17'))
body = ParagraphStyle('b', fontName='Helvetica', fontSize=9.5, leading=13, textColor=colors.black)
mono = ParagraphStyle('m', fontName='Courier', fontSize=8, leading=11, textColor=colors.black)

story = []
story.append(Paragraph("SecureDT - Complete Installation and Usage Guide", h2))
story.append(Spacer(1, 6))
story.append(Paragraph("Version 1.0 | Django + MySQL + Groq AI + Genetic Algorithm", body))
story.append(Spacer(1, 4))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 1: PROJECT OVERVIEW", h2))
story.append(Paragraph("Problem: Efficient task scheduling across edge, MEC, and cloud resources with security risk optimization.", body))
story.append(Paragraph("Objective: Intelligent, secure task scheduling optimizing latency, energy, privacy, and security risk.", body))
story.append(Paragraph("Architecture: Django backend with REST API, MySQL database, GA scheduler, Digital Twin, AI risk engine (local RF + optional Groq LLM), attack simulation (safe software simulation), storage attack simulation, analytics, experiment frameworks.", body))
story.append(Paragraph("Technology Stack: Python 3.13, Django 5.2, MySQL, PyMySQL, numpy, pandas, scikit-learn, reportlab, fpdf2, Flask, Git, HTML5/CSS3/JQuery, Chart.js.", body))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 2: SOFTWARE REQUIREMENTS", h2))
story.append(Paragraph("Python: 3.10 or newer (64-bit recommended)", body))
story.append(Paragraph("Django: 5.2 LTS (or 4.x+)", body))
story.append(Paragraph("MySQL: 8.0+ with PyMySQL or mysql-connector-python", body))
story.append(Paragraph("Redis: Optional (for Celery fallback)", body))
story.append(Paragraph("Browser: Chrome, Edge, or Firefox (latest)", body))
story.append(Paragraph("Git: For version control and deployment", body))
story.append(Paragraph("Python Packages (from requirements.txt):", body))
story.append(Paragraph("Flask>=2.3,<4.0", body))
story.append(Paragraph("Flask-Cors>=4.0", body))
story.append(Paragraph("numpy>=2.0", body))
story.append(Paragraph("pandas>=2.0", body))
story.append(Paragraph("scikit-learn>=1.3", body))
story.append(Paragraph("reportlab>=4.0", body))
story.append(Paragraph("fpdf2>=2.7", body))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 3: PROJECT INSTALLATION", h2))
story.append(Paragraph("Step 1: Extract ZIP - Unzip the project archive to your desired location.", body))
story.append(Paragraph("Step 2: Open terminal - Navigate to the project directory: cd path/to/securedt", body))
story.append(Paragraph("Step 3: Create virtual environment - python -m venv .venv", body))
story.append(Paragraph("Step 4: Activate environment - Windows: .venv\\Scripts\\activate | Linux/macOS: source .venv/bin/activate", body))
story.append(Paragraph("Step 5: Install requirements - pip install -r requirements.txt", body))
story.append(Paragraph("Step 6: Configure .env - cp .env.example .env  Edit .env with your settings", body))
story.append(Paragraph("Step 7: Create MySQL database - CREATE DATABASE securedt; CREATE USER 'securedt'@'%' IDENTIFIED BY 'password'; GRANT ALL PRIVILEGES ON securedt.* TO 'securedt'@'%';", body))
story.append(Paragraph("Step 8: Configure MySQL - Update .env with DB settings: DB_ENGINE=django.db.backends.mysql, DB_NAME=securedt, DB_USER=securedt, DB_PASSWORD=password, DB_HOST=localhost, DB_PORT=3306", body))
story.append(Paragraph("Step 9: Run migrations - python manage.py makemigrations && python manage.py migrate", body))
story.append(Paragraph("Step 10: Create superuser - python manage.py createsuperuser", body))
story.append(Paragraph("Step 11: Run Django - python manage.py runserver  Open http://127.0.0.1:8000 in browser", body))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 4: MYSQL DATABASE", h2))
story.append(Paragraph("Database creation: securedt database, securedt user, configured password", body))
story.append(Paragraph("username: securedt (or your chosen username)", body))
story.append(Paragraph("password: your_secure_password (set in .env)", body))
story.append(Paragraph("host: localhost", body))
story.append(Paragraph("port: 3306 (default MySQL port)", body))
story.append(Paragraph("migration: python manage.py makemigrations && python manage.py migrate", body))
story.append(Paragraph("tables: auth_user, auth_group, auth_permission, django_admin_log, django_content_type, django_migrations, django_session, plus application tables: api_state, analytics_experiment, attacks_attack, storage_storage, tasks_task, digital_twin_resourcestate, ai_riskprediction, groq_status", body))
story.append(Paragraph("indexes: Primary keys on all ID columns; indexes on resource_type, task_status, attack_type, experiment_status for performance", body))
story.append(Paragraph("Example configuration with placeholders:", mono))
story.append(Paragraph("DEFAULT: ENGINE=django.db.backends.sqlite3 NAME=BASE_DIR/db.sqlite3 (development)", mono))
story.append(Paragraph("MYSQL: ENGINE=django.db.backends.mysql NAME=securedt USER=securedt PASSWORD=your_password HOST=localhost PORT=3306", mono))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 5: USER ACCOUNT", h2))
story.append(Paragraph("Register: New users can register via /register with username, password, and email.", body))
story.append(Paragraph("Login: Authenticated users access via /login with username and password.", body))
story.append(Paragraph("Logout: /logout ends the session.", body))
story.append(Paragraph("Password reset: Django built-in password reset flow via /password-reset.", body))
story.append(Paragraph("Profile: User profile accessible after login; displays role and preferences.", body))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 6: DATASET SYSTEM", h2))
story.append(Paragraph("Dataset sources: Synthetic datasets (seed-based reproducible) and optional live telemetry imports.", body))
story.append(Paragraph("Download: python scripts/generate_dataset.py --tasks 10000 --attack 5000 --resource 3000", body))
story.append(Paragraph("Import: CSV upload validated for type/size/rows; normalized to UnifiedEvent schema.", body))
story.append(Paragraph("Validation: Schema detection, missing value handling, type checking, label balance verification.", body))
story.append(Paragraph("Normalization: All datasets converted to canonical UnifiedEvent schema with consistent fields.", body))
story.append(Paragraph("Processing: Cleaning -> Feature Engineering -> Storage in unified format.", body))
story.append(Paragraph("Storage: CSV files in datasets/; quality reports in JSON/CSV export.", body))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 7: LARGE DATASET PROCESSING", h2))
story.append(Paragraph("The system supports datasets from 100K to 10M+ rows using chunking, streaming, Parquet, DuckDB, MySQL metadata, background processing via Celery (optional), and pagination so the browser never loads millions of rows.", body))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 8: AI", h2))
story.append(Paragraph("Dataset preparation: Features and labels extracted from UnifiedEvent schema CSV.", body))
story.append(Paragraph("Features: cpu, memory, latency, trust, security_risk, attack_severity, privacy, workload, storage_integrity, attack_exposure", body))
story.append(Paragraph("Training: RandomForestClassifier via sklearn RandomizedSearchCV on ai_training_10000.csv", body))
story.append(Paragraph("Validation: 80/20 train-test split; ROC-AUC, F1-score, feature importance reported", body))
story.append(Paragraph("Testing: /api/ai/analyze endpoint returns risk level + confidence", body))
story.append(Paragraph("Model saving: models/risk_model.pkl + models/risk_metrics.json", body))
story.append(Paragraph("Prediction: Risk level (safe/trained/critical) + confidence score (0-1)", body))
story.append(Paragraph("Explanation: Local SHAP values when available; deterministic rule fallback otherwise", body))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 9: GROQ", h2))
story.append(Paragraph("Local AI: scikit-learn Random Forest - works without any API key", body))
story.append(Paragraph("Groq AI: Optional LLM insight layer via Groq Cloud API", body))
story.append(Paragraph("Why Groq is optional: Core functionality works offline; Groq adds natural-language explanations only", body))
story.append(Paragraph("Where API key goes: .env file ONLY - never in source, HTML, JS, CSS, or database", body))
story.append(Paragraph("How backend calls Groq: /api/ai/explain and /api/ai/analyze endpoints forward requests via backend", body))
story.append(Paragraph("How frontend never sees the key: Backend-only; key read from environment at runtime", body))
story.append(Paragraph("Fallback mode: If Groq unavailable, app auto-falls back to local AI without crash", body))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 10: GENETIC ALGORITHM", h2))
story.append(Paragraph("Population: 40 chromosomes (task-to-resource assignments)", body))
story.append(Paragraph("Fitness: Weighted combination of latency (0.25), energy (0.15), privacy (0.20), security (0.30), deadline (0.10)", body))
story.append(Paragraph("Selection: Tournament selection (size 3)", body))
story.append(Paragraph("Crossover: Single-point crossover (rate 0.85)", body))
story.append(Paragraph("Mutation: Per-gene mutation (rate 0.12)", body))
story.append(Paragraph("Elitism: Top 4 chromosomes carried to next generation", body))
story.append(Paragraph("Generations: 50 iterations of optimization", body))
story.append(Paragraph("Output: Best chromosome (optimal resource assignment), fitness history chart", body))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 11: DIGITAL TWIN", h2))
story.append(Paragraph("Virtual resource state mirror of edge/MEC/cloud nodes (CPU, memory, latency, trust, security-risk). Real/simulated state synchronization with scheduler. Risk level updates dynamically. Attack events update risk scores and may quarantine nodes.", body))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 12: TASK SCHEDULING", h2))
story.append(Paragraph("Local: Default scheduler on Django server. MEC: Edge resource allocation with low latency targets. Cloud: Centralized scheduling with higher capacity but higher latency. Factors: latency, energy, privacy, security risk, deadline compliance.", body))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 13: ATTACK SIMULATION", h2))
story.append(Paragraph("This is a SAFE SOFTWARE SIMULATION: No real attack occurs. No network traffic is sent.", body))
story.append(Paragraph("Attacker: Simulated threat actor targeting a resource node. Target: Selected MEC or Cloud resource in the Digital Twin. Risk increase: Security risk score increases based on attack severity. Detection: Security monitor detects anomaly, raises alert. Digital Twin update: Resource state updated with new risk profile. AI analysis: Local AI provides risk explanation. GA reoptimization: Scheduler re-runs GA with updated risk weights. Rerouting: Tasks rerouted to healthier resources. Recovery: Mitigation stops attack, risk decreases, node recovered.", body))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 14: STORAGE ATTACK", h2))
story.append(Paragraph("Virtual storage: STORAGE-A, STORAGE-B, STORAGE-C in simulated environment. Simulated attacker attempts integrity violations. Attack event recorded in audit log; integrity risk score updated. Detection: Storage integrity monitoring detects anomalies. Protection: Virtual isolation and risk containment. Isolation: Affected storage quarantined; other storages unaffected. Safe storage: All data remains safe; simulation only. Rerouting: Tasks redirected to available storage. Recovery: Integrity restored; storage returned to normal state.", body))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 15: SECURITY", h2))
story.append(Paragraph("Authentication: Django built-in auth with session-based login/register/logout. Authorization: Role-based access control; superuser vs. regular user. CSRF: Protected on all state-changing API requests via token. XSS: Content Security Policy and output encoding prevent XSS. SQL injection defense: Parameterized queries; Django ORM prevents SQLi. File upload: CSV only, 8MB max, 100K row max, re-encoded on upload. Rate limiting: Per-IP limiter (default 60 requests/minute). Session security: Signed with SECRET_KEY; HttpOnly/SameSite cookies. Security headers: CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, HSTS. Audit logs: All events recorded with category, severity, and export capability.", body))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 16: EXPERIMENTS", h2))
story.append(Paragraph("Baseline: random, greedy, privacy-aware schedulers. Proposed: Security-aware Genetic Algorithm. Dataset size: Configurable from 100 to 1M+ tasks. AI: Risk model predictions integrated into fitness function. GA: Population, generations, crossover, mutation parameters. Metrics: Success rate, latency, energy, privacy exposure, security risk. Results: Comparison charts in /analytics and export to CSV/JSON/PDF.", body))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 17: PERFORMANCE", h2))
story.append(Paragraph("Latency: Typically < 200ms for API responses; GA optimization ~ 5-30 seconds. Processing time: Dataset import scales with chunking; 1M rows ~ 30-60 seconds. Energy: Optimized scheduling reduces energy consumption vs. random placement. Privacy: Feature engineering preserves privacy; no personal data transmitted. Security: Multi-layer defense; all secrets in environment variables. Scalability: Designed for 10K+ tasks; large datasets via chunking/streaming.", body))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 18: REPORT GENERATION", h2))
story.append(Paragraph("CSV: Experiment results, analytics data, task summaries. JSON: API responses, system state exports. PDF: Generated experiment reports with charts and metrics. Charts: Chart.js-based visualizations in dashboard and analytics pages. Experiment reports: /api/export/experiments generates full report.", body))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 19: TROUBLESHOOTING", h2))
story.append(Paragraph("MySQL not connecting: Verify .env DB settings, MySQL service running, port 3306 open.", body))
story.append(Paragraph("Migration error: Run makemigrations first; ensure models match.", body))
story.append(Paragraph("Django error: Check manage.py and settings.py consistency.", body))
story.append(Paragraph("Groq key missing: Set GROQ_API_KEY in .env; app falls back to local AI.", body))
story.append(Paragraph("Groq unavailable: Set AI_PROVIDER=localfeatures in .env.", body))
story.append(Paragraph("Model missing: Run scripts/train_ai.py to generate models/risk_model.pkl.", body))
story.append(Paragraph("Dataset missing: Generate with scripts/generate_dataset.py or upload CSV.", body))
story.append(Paragraph("Celery unavailable: System works in synchronous mode; optional Celery/Redis for async.", body))
story.append(Paragraph("Redis unavailable: Fallback to database queue or synchronous processing.", body))
story.append(Paragraph("WebGL unavailable: 3D infrastructure runs in Canvas2D fallback mode.", body))
story.append(Paragraph("PDF generation error: Ensure reportlab is installed; check write permissions.", body))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 20: HOW TO START", h2))
story.append(Paragraph("1. Extract ZIP", "Unzip the project archive to your desired location.", body))
story.append(Paragraph("2. Install Python", "Python 3.13+ from python.org", body))
story.append(Paragraph("3. Install MySQL", "MySQL 8.0+ from mysql.com", body))
story.append(Paragraph("4. Create database", "CREATE DATABASE securedt; CREATE USER 'securedt'@'%' IDENTIFIED BY 'password';", body))
story.append(Paragraph("5. Create .env", "cp .env.example .env  Edit with your DB, Groq, and app settings", body))
story.append(Paragraph("6. Add GROQ_API_KEY", "GROQ_API_KEY=YOUR_KEY_HERE (optional; local AI works without it)", body))
story.append(Paragraph("7. Install dependencies", "pip install -r requirements.txt", body))
story.append(Paragraph("8. Run migrations", "python manage.py makemigrations && python manage.py migrate", body))
story.append(Paragraph("9. Create superuser", "python manage.py createsuperuser", body))
story.append(Paragraph("10. Start server", "python manage.py runserver", body))
story.append(Paragraph("11. Open browser", "http://127.0.0.1:8000", body))
story.append(Paragraph("12. Register", "Create a new account or use: username=admin, password=admin123", body))
story.append(Paragraph("13. Login", "Access the dashboard and all features", body))
story.append(Paragraph("14. Run Demo", "Go to /experiments to compare schedulers, /attack to simulate attacks, /digital-twin to monitor resources", body))

doc.build(story)
print('COMPLETE_INSTALLATION_AND_USAGE_GUIDE.pdf generated')

pdf_path = os.path.join(OUT_DIR, 'COMPLETE_INSTALLATION_AND_USAGE_GUIDE.pdf')
print('File exists:', os.path.exists(pdf_path))
print('File size:', os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 'N/A')