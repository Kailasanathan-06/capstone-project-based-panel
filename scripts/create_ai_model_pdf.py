#!/usr/bin/env python3
"""Create AI_MODEL_INSTALLATION.pdf"""

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
    os.path.join(OUT_DIR, "AI_MODEL_INSTALLATION.pdf"),
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

doc = SimpleDocTemplate(
    os.path.join(OUT_DIR, "AI_MODEL_INSTALLATION.pdf"),
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

doc = SimpleDocTemplate(
    os.path.join(OUT_DIR, "AI_MODEL_INSTALLATION.pdf"),
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

doc = SimpleDocTemplate(
    os.path.join(OUT_DIR, "AI_MODEL_INSTALLATION.pdf"),
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

doc = SimpleDocTemplate(
    os.path.join(OUT_DIR, "AI_MODEL_INSTALLATION.pdf"),
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

doc = SimpleDocTemplate(
    os.path.join(OUT_DIR, "AI_MODEL_INSTALLATION.pdf"),
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

doc = SimpleDocTemplate(
    os.path.join(OUT_DIR, "AI_MODEL_INSTALLATION.pdf"),
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

doc = SimpleDocTemplate(
    os.path.join(OUT_DIR, "AI_MODEL_INSTALLATION.pdf"),
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

doc = SimpleDocTemplate(
    os.path.join(OUT_DIR, "AI_MODEL_INSTALLATION.pdf"),
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

doc = SimpleDocTemplate(
    os.path.join(OUT_DIR, "AI_MODEL_INSTALLATION.pdf"),
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

doc = SimpleDocTemplate(
    os.path.join(OUT_DIR, "AI_MODEL_INSTALLATION.pdf"),
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

doc = SimpleDocTemplate(
    os.path.join(OUT_DIR, "AI_MODEL_INSTALLATION.pdf"),
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
story.append(Paragraph("SecureDT AI Model Installation Guide", Heading1))
story.append(Spacer(1, 6))
story.append(Paragraph("Random Forest Risk Model for Task Security Risk Prediction", Normal))
story.append(Spacer(1, 4))
story.append(Spacer(1, 8))

story.append(Paragraph("REQUIRED MODELS", Heading2))
story.append(Paragraph("These models are required for the core functionality of SecureDT.", Normal))
story.append(Spacer(1, 4))

story.append(Paragraph("1. Risk Prediction Model (REQUIRED)", Heading2))
story.append(Paragraph("Purpose: Predicts the security level of an incoming scheduled task from labelled synthetic workloads.", Normal))
story.append(Paragraph("Package: scikit-learn RandomForestClassifier", Normal))
story.append(Paragraph("Install command: pip install scikit-learn>=1.3", Normal))
story.append(Paragraph("Training command: python scripts/train_ai.py", Normal))
story.append(Paragraph("Dataset: ai_training_10000.csv (synthetic, seed 42)", Normal))
story.append(Paragraph("Input features: cpu, memory, latency, trust, security_risk, attack_severity, privacy, workload, storage_integrity, attack_exposure (10 features)", Normal))
story.append(Paragraph("Output: Risk level (safe/trained/critical) + confidence score (0-1)", Normal))
story.append(Paragraph("Model path: models/risk_model.pkl", Normal))
story.append(Paragraph("CPU/GPU requirement: CPU-only; scikit-learn RandomForest trains efficiently on CPU. No GPU required.", Normal))
story.append(Spacer(1, 6))

story.append(Paragraph("OPTIONAL ENHANCEMENTS", Heading2))
story.append(Paragraph("These enhancements improve capabilities but are not required for core operation.", Normal))
story.append(Spacer(1, 4))

story.append(Paragraph("2. Groq Cloud LLM Enhancement (OPTIONAL)", Heading2))
story.append(Paragraph("Purpose: Natural-language explanations, experiment summaries, risk commentary via Groq Cloud API.", Normal))
story.append(Paragraph("Package: groq SDK (pip install groq)", Normal))
story.append(Paragraph("Install command: pip install groq", Normal))
story.append(Paragraph("Configuration: GROQ_API_KEY and GROQ_MODEL in .env file", Normal))
story.append(Paragraph("Model selection: GROQ_MODEL=llama-3.3-70b-versatile (default) or mixtral-8x7b-32768 or gemma-7b-it", Normal))
story.append(Paragraph("AI_PROVIDER=groq or hybrid in .env to enable", Normal))
story.append(Paragraph("Fallback: If key missing, app degrades to local AI mode without crash", Normal))
story.append(Paragraph("CPU/GPU requirement: Server-side inference on Groq Cloud; no local GPU needed.", Normal))
story.append(Spacer(1, 6))

story.append(Paragraph("3. SHAP Feature Explanations (OPTIONAL)", Heading2))
story.append(Paragraph("Purpose: Detailed feature importance explanations for risk predictions.", Normal))
story.append(Paragraph("Package: shap (pip install shap)", Normal))
story.append(Paragraph("Feature reasons: displayed in UI when shap installed", Normal))
story.append(Paragraph("Fallback: Deterministic rule-based reasons always available", Normal))
story.append(Paragraph("CPU/GPU requirement: Lightweight Python library; CPU only.", Normal))
story.append(Spacer(1, 6))

story.append(Paragraph("4. Risk Model Metrics (AUTOMATIC)", Heading2))
story.append(Paragraph("ROC-AUC, F1-score, feature importance, validation results written to models/risk_metrics.json", Normal))
story.append(Paragraph("Automatic with sklearn training", Normal))
story.append(Paragraph("Read via /api/ai/analyze and /api/export/experiments", Normal))
story.append(Spacer(1, 8))

story.append(Paragraph("INSTALLATION STEPS", Heading2))
story.append(Paragraph("Step 1: Install dependencies - pip install -r requirements.txt", Normal))
story.append(Paragraph("Step 2: Train the AI model - python scripts/train_ai.py", Normal))
story.append(Paragraph("Step 3: Verify model file exists - ls models/risk_model.pkl", Normal))
story.append(Paragraph("Step 4: Start the application - python manage.py runserver (or python app.py)", Normal))
story.append(Paragraph("Step 5: Test AI analysis - curl -X POST /api/ai/analyze", Normal))
story.append(Spacer(1, 6))

story.append(Paragraph("VERIFICATION", Heading2))
story.append(Paragraph("After installation, verify:", Normal))
story.append(Paragraph("• python manage.py check → no issues", Normal))
story.append(Paragraph("• python scripts/setup_check.py → AI dependencies OK", Normal))
story.append(Paragraph("• /api/ai/analyze endpoint returns risk level + confidence", Normal))
story.append(Paragraph("• models/risk_model.pkl exists and is loadable", Normal))
story.append(Paragraph("• Fallback works: delete model file, re-run analysis → rule-based", Normal))
story.append(Spacer(1, 8))

story.append(Paragraph("IMPORTANT NOTES", Heading2))
story.append(Paragraph("• The risk model is trained on synthetic data (seed 42) for demonstration purposes.", Normal))
story.append(Paragraph("• Model trains on CPU only; no GPU acceleration required.", Normal))
story.append(Paragraph("• If models/risk_model.pkl is deleted, the engine auto-falls back to deterministic rules.", Normal))
story.append(Paragraph("• Groq LLM enhancement is completely optional; core risk prediction works without it.", Normal))
story.append(Paragraph("• Model retraining: re-run scripts/train_ai.py with updated dataset if needed.", Normal))

doc.build(story)
print('AI_MODEL_INSTALLATION.pdf generated')

pdf_path = os.path.join(OUT_DIR, 'AI_MODEL_INSTALLATION.pdf')
print('File exists:', os.path.exists(pdf_path))
print('File size:', os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 'N/A')
PYEOF