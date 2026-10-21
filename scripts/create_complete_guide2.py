#!/usr/bin/env python3
"""Create COMPLETE_INSTALLATION_AND_USAGE_GUIDE.pdf - simple version"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

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
Normal = styles['Normal']
Heading1 = styles['Heading1']
Heading2 = styles['Heading2']

story = []
story.append(Paragraph("SecureDT - Complete Installation and Usage Guide", Heading1))
story.append(Spacer(1, 6))
story.append(Paragraph("Version 1.0 | Django + MySQL + Groq AI + Genetic Algorithm", Normal))
story.append(Spacer(1, 4))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 1: PROJECT OVERVIEW", Heading2))
story.append(Paragraph("Problem: Efficient task scheduling across edge, MEC, and cloud resources with security risk optimization.", Normal))
story.append(Paragraph("Objective: Intelligent, secure task scheduling optimizing latency, energy, privacy, and security risk.", Normal))
story.append(Paragraph("Architecture: Django backend with REST API, MySQL database, GA scheduler, Digital Twin, AI risk engine (local RF + optional Groq LLM), attack simulation (safe software simulation), storage attack simulation, analytics, experiment frameworks.", Normal))
story.append(Paragraph("Technology Stack: Python 3.13, Django 5.2, MySQL, PyMySQL, numpy, pandas, scikit-learn, reportlab, fpdf2, Flask, Git, HTML5/CSS3/JQuery, Chart.js.", Normal))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 2: SOFTWARE REQUIREMENTS", Heading2))
story.append(Paragraph("Python: 3.10 or newer (64-bit recommended).", Normal))
story.append(Paragraph("Django: 5.2 LTS (or 4.x+).", Normal))
story.append(Paragraph("MySQL: 8.0+ with PyMySQL or mysql-connector-python.", Normal))
story.append(Paragraph("Redis: Optional (for Celery fallback).", Normal))
story.append(Paragraph("Browser: Chrome, Edge, or Firefox (latest).", Normal))
story.append(Paragraph("Git: For version control and deployment.", Normal))
story.append(Paragraph("Python Packages (from requirements.txt):", Normal))
story.append(Paragraph("Flask>=2.3,<4.0", Normal))
story.append(Paragraph("Flask-Cors>=4.0", Normal))
story.append(Paragraph("numpy>=2.0", Normal))
story.append(Paragraph("pandas>=2.0", Normal))
story.append(Paragraph("scikit-learn>=1.3", Normal))
story.append(Paragraph("reportlab>=4.0", Normal))
story.append(Paragraph("fpdf2>=2.7", Normal))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 3: PROJECT INSTALLATION", Heading2))
story.append(Paragraph("Step 1: Extract ZIP - Unzip the project archive to your desired location.", Normal))
story.append(Paragraph("Step 2: Open terminal - Navigate to the project directory: cd path/to/securedt", Normal))
story.append(Paragraph("Step 3: Create virtual environment - python -m venv .venv", Normal))
story.append(Paragraph("Step 4: Activate environment - Windows: .venv\\Scripts\\activate | Linux/macOS: source .venv/bin/activate", Normal))
story.append(Paragraph("Step 5: Install requirements - pip install -r requirements.txt", Normal))
story.append(Paragraph("Step 6: Configure .env - cp .env.example .env  Edit .env with your settings", Normal))
story.append(Paragraph("Step 7: Create MySQL database - CREATE DATABASE securedt; CREATE USER 'securedt'@'%' IDENTIFIED BY 'password'; GRANT ALL PRIVILEGES ON securedt.* TO 'securedt'@'%';", Normal))
story.append(Paragraph("Step 8: Configure MySQL - Update .env with DB settings.", Normal))
story.append(Paragraph("Step 9: Run migrations - python manage.py makemigrations && python manage.py migrate", Normal))
story.append(Paragraph("Step 10: Create superuser - python manage.py createsuperuser", Normal))
story.append(Paragraph("Step 11: Run Django - python manage.py runserver  Open http://127.0.0.1:8000 in browser", Normal))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 4: MYSQL DATABASE", Heading2))
story.append(Paragraph("Database: securedt database with securedt user.", Normal))
story.append(Paragraph("username: securedt", Normal))
story.append(Paragraph("password: your_secure_password (set in .env)", Normal))
story.append(Paragraph("host: localhost", Normal))
story.append(Paragraph("port: 3306 (default MySQL port)", Normal))
story.append(Paragraph("migration: python manage.py makemigrations && python manage.py migrate", Normal))
story.append(Paragraph("tables: auth_user, plus application tables for tasks, attacks, storage, digital twin, analytics, AI prediction, Groq status.", Normal))
story.append(Paragraph("Example (placeholders only):", Normal))
story.append(Paragraph("DEFAULT: ENGINE=django.db.backends.sqlite3 NAME=BASE_DIR/db.sqlite3 (development)", Normal))
story.append(Paragraph("MYSQL: ENGINE=django.db.backends.mysql NAME=securedt USER=securedt PASSWORD=your_password HOST=localhost PORT=3306", Normal))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 5: USER ACCOUNT", Heading2))
story.append(Paragraph("Register: via /register with username, password, and email.", Normal))
story.append(Paragraph("Login: via /login with username and password.", Normal))
story.append(Paragraph("Logout: /logout ends the session.", Normal))
story.append(Paragraph("Password reset: Django built-in flow via /password-reset.", Normal))
story.append(Paragraph("Profile: accessible after login; displays role and preferences.", Normal))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 6: DATASET SYSTEM", Heading2))
story.append(Paragraph("Synthetic datasets (seed-based reproducible) and optional live telemetry imports.", Normal))
story.append(Paragraph("Download: python scripts/generate_dataset.py --tasks 10000 --attack 5000 --resource 3000", Normal))
story.append(Paragraph("CSV upload validated for type/size/rows; normalized to UnifiedEvent schema.", Normal))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 7: LARGE DATASET PROCESSING", Heading2))
story.append(Paragraph("Supports 100K to 10M+ rows using chunking, streaming, Parquet, DuckDB, MySQL metadata, background processing via Celery (optional), and pagination so browser never loads millions of rows.", Normal))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 8: AI", Heading2))
story.append(Paragraph("Local AI: scikit-learn Random Forest - works without any API key.", Normal))
story.append(Paragraph("Groq AI: Optional LLM insight layer via Groq Cloud API. Core functionality works offline; Groq adds natural-language explanations only.", Normal))
story.append(Paragraph("Where API key goes: .env file ONLY - never in source, HTML, JS, CSS, or database.", Normal))
story.append(Paragraph("Fallback mode: If Groq unavailable, app auto-falls back to local AI without crash.", Normal))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 9: GENETIC ALGORITHM", Heading2))
story.append(Paragraph("Population: 40 chromosomes. Fitness weighted: latency (0.25), energy (0.15), privacy (0.20), security (0.30), deadline (0.10). Tournament selection (size 3), crossover (0.85), mutation (0.12), elitism (top 4). Generations: 50.", Normal))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 11: DIGITAL TWIN", Heading2))
story.append(Paragraph("Virtual resource state mirror of edge/MEC/cloud nodes (CPU, memory, latency, trust, security-risk). Risk level updates dynamically. Attack events update risk scores and may quarantine nodes.", Normal))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 13: ATTACK SIMULATION", Heading2))
story.append(Paragraph("SAFE SOFTWARE SIMULATION: No real attack occurs. No network traffic is sent.", Normal))
story.append(Paragraph("Attacker: Simulated threat actor. Target: Selected MEC or Cloud resource. Risk increase: Security risk score based on attack severity. Detection: Security monitor raises alert. Digital Twin update: Resource state updated. AI analysis: Local AI provides risk explanation. GA reoptimization: Scheduler re-runs with updated risk weights. Rerouting: Tasks rerouted to healthier resources. Recovery: Mitigation stops attack, risk decreases, node recovered.", Normal))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 14: STORAGE ATTACK", Heading2))
story.append(Paragraph("Virtual storages STORAGE-A (1000GB encrypted), STORAGE-B (2000GB encrypted), STORAGE-C (500GB unencrypted). Simulated attacker, integrity risk scores, detection, protection, isolation (affected storage quarantined; others unaffected), safe storage (simulation only), rerouting, recovery.", Normal))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 15: SECURITY", Heading2))
story.append(Paragraph("Authentication: Django built-in auth, session-based login/register/logout.", Normal))
story.append(Paragraph("Authorization: Role-based access control; superuser vs. regular user.", Normal))
story.append(Paragraph("CSRF: Protected on all state-changing API requests via token.", Normal))
story.append(Paragraph("XSS: Content Security Policy and output encoding prevent XSS.", Normal))
story.append(Paragraph("SQL injection defense: Parameterized queries; Django ORM prevents SQLi.", Normal))
story.append(Paragraph("File upload: CSV only, 8MB max, 100K row max, re-encoded on upload.", Normal))
story.append(Paragraph("Rate limiting: Per-IP limiter (default 60 requests/minute).", Normal))
story.append(Paragraph("Session security: Signed with SECRET_KEY; HttpOnly/SameSite cookies.", Normal))
story.append(Paragraph("Security headers: CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, HSTS.", Normal))
story.append(Paragraph("Audit logs: All events recorded with category, severity, and export capability.", Normal))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 16: EXPERIMENTS", Heading2))
story.append(Paragraph("Baseline: random, greedy, privacy-aware schedulers. Proposed: Security-aware Genetic Algorithm. Dataset size: 100 to 1M+ tasks. AI: Risk model predictions integrated into fitness function. Metrics: Success rate, latency, energy, privacy exposure, security risk. Results: Comparison charts in /analytics and export to CSV/JSON/PDF.", Normal))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 17: PERFORMANCE", Heading2))
story.append(Paragraph("Latency: Typically < 200ms for API responses; GA optimization ~ 5-30 seconds. Processing time: 1M rows ~ 30-60 seconds. Energy: Optimized scheduling reduces energy vs. random placement. Privacy: No personal data transmitted. Security: All secrets in environment variables. Scalability: Designed for 10K+ tasks; large datasets via chunking/streaming.", Normal))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 18: REPORT GENERATION", Heading2))
story.append(Paragraph("CSV: Experiment results, analytics data, task summaries. JSON: API responses, system state exports. PDF: Generated experiment reports with charts and metrics. Charts: Chart.js-based visualizations. Experiment reports: /api/export/experiments generates full report.", Normal))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 19: TROUBLESHOOTING", Heading2))
story.append(Paragraph("MySQL not connecting: Verify .env DB settings, MySQL service running, port 3306 open.", Normal))
story.append(Paragraph("Groq key missing: Set GROQ_API_KEY in .env; app falls back to local AI.", Normal))
story.append(Paragraph("Groq unavailable: Set AI_PROVIDER=localfeatures in .env.", Normal))
story.append(Paragraph("Model missing: Run scripts/train_ai.py to generate models/risk_model.pkl.", Normal))
story.append(Paragraph("Dataset missing: Generate with scripts/generate_dataset.py or upload CSV.", Normal))
story.append(Paragraph("Celery unavailable: System works in synchronous mode; optional Celery/Redis for async.", Normal))
story.append(Paragraph("Redis unavailable: Fallback to database queue or synchronous processing.", Normal))
story.append(Paragraph("PDF generation error: Ensure reportlab is installed; check write permissions.", Normal))
story.append(Spacer(1, 8))

story.append(Paragraph("SECTION 20: HOW TO START", Heading2))
story.append(Paragraph("1. Extract ZIP - Unzip the project archive to your desired location.", Normal))
story.append(Paragraph("2. Install Python - Python 3.13+ from python.org", Normal))
story.append(Paragraph("3. Install MySQL - MySQL 8.0+ from mysql.com", Normal))
story.append(Paragraph("4. Create database - CREATE DATABASE securedt; CREATE USER 'securedt'@'%' IDENTIFIED BY 'password';", Normal))
story.append(Paragraph("5. Create .env - cp .env.example .env  Edit with your DB, Groq, and app settings", Normal))
story.append(Paragraph("6. Add GROQ_API_KEY - GROQ_API_KEY=YOUR_KEY_HERE (optional; local AI works without it)", Normal))
story.append(Paragraph("7. Install dependencies - pip install -r requirements.txt", Normal))
story.append(Paragraph("8. Run migrations - python manage.py makemigrations && python manage.py migrate", Normal))
story.append(Paragraph("9. Create superuser - python manage.py createsuperuser", Normal))
story.append(Paragraph("10. Start server - python manage.py runserver", Normal))
story.append(Paragraph("11. Open browser - http://127.0.0.1:8000", Normal))
story.append(Paragraph("12. Register - Create a new account or use: username=admin, password=admin123", Normal))
story.append(Paragraph("13. Login - Access the dashboard and all features", Normal))
story.append(Paragraph("14. Run Demo - Go to /experiments to compare schedulers, /attack to simulate attacks, /digital-twin to monitor resources", Normal))

doc.build(story)
print('COMPLETE_INSTALLATION_AND_USAGE_GUIDE.pdf generated')

pdf_path = os.path.join(OUT_DIR, 'COMPLETE_INSTALLATION_AND_USAGE_GUIDE.pdf')
print('File exists:', os.path.exists(pdf_path))
print('File size:', os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 'N/A')