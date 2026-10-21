#!/usr/bin/env python3
"""Generate Groq API Setup Guide PDF."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "SecureDT")
OUT_DIR = os.path.join(BASE_DIR, "docs")
os.makedirs(OUT_DIR, exist_ok=True)

INK = colors.HexColor("#0a0e0ff")
BG = colors.HexColor("#0a0e17")
ACCENT = colors.HexColor("#35e0ff")
WHITE = colors.white
BLACK = colors.black
SILVER = colors.HexColor("#c0c0c0")


def style_header(font_size=16, bold=True):
    return ParagraphStyle(
        "h",
        fontName="Helvetica-Bold" if bold else "Helvetica",
        fontSize=font_size,
        leading=22,
        textColor=INK,
    )


def style_body(size=10):
    return ParagraphStyle(
        "b", fontName="Helvetica", fontSize=size, leading=14, textColor=BLACK
    )


def style_mono():
    return ParagraphStyle(
        "m", fontName="Courier", fontSize=9, leading=13, textColor=BLACK
    )


def make_table(data, col_widths=[180 * mm]):
    t = Table(data, colWidths=col_widths)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), INK),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEADING", (0, 0), (-1, -1), 12),
                ("GRID", (0, 0), (-1, -1), 0.5, SILVER),
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
        os.path.join(OUT_DIR, "GROQ_API_SETUP_GUIDE.pdf"),
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
    story.append(Paragraph("SecureDT Groq API Setup Guide", title_style))
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("Intelligent and Secure Task Scheduling for Digital Twin-Enabled Edge-Cloud Networks", body))
    story.append(Spacer(1, 6 * mm))

    # --- 1. What is Groq Cloud? ---
    story.append(Paragraph("1. What is Groq Cloud?", h2))
    story.append(Paragraph(
        "Groq Cloud is a hosted inference service providing ultra-fast Large Language Model (LLM) "
        "access via a simple API. It offers some of the lowest-latency inference available for "
        "open-source models, making it ideal for real-time AI assistance, natural-language "
        "analytics, and experiment explanations within the SecureDT system.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- 2. Why Groq is used ---
    story.append(Paragraph("2. Why Groq is used?", h2))
    story.append(Paragraph(
        "Groq is used as an optional enhancement layer in SecureDT for AI explanations, experiment "
        "summaries, risk analysis, and natural-language analytics. It provides human-readable "
        "insights that complement the deterministic local AI (scikit-learn Random Forest) without "
        "making any security decisions. The core security logic remains application-controlled and "
        "deterministic at all times.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- 3. What part of the project uses Groq ---
    story.append(Paragraph("3. What part of the project uses Groq?", h2))
    story.append(Paragraph(
        "The AI engine (/engine/ai_engine.py) uses Groq when AI_PROVIDER is set to \"groq\" or "
        "\"hybrid\" and a valid GROQ_API_KEY is present. Specific endpoints that may call Groq:",
        body))
    story.append(Paragraph("• /api/ai/explain - natural-language explanations of task risk", body))
    story.append(Paragraph("• /api/ai/analyze - risk scoring with LLM insights", body))
    story.append(Paragraph("• Experiment report generation with narrative summaries", body))
    story.append(Paragraph("• Digital Twin state analysis and recommendations", body))
    story.append(Spacer(1, 4 * mm))

    # --- 4. What part does NOT depend on Groq ---
    story.append(Paragraph("4. What part does NOT depend on Groq?", h2))
    story.append(Paragraph(
        "The entire SecureDT core functions without Groq. All security decisions, attack simulation, "
        "scheduling, risk scoring, task routing, and Digital Twin state management are performed "
        "locally using scikit-learn models and deterministic algorithms. The application degrades "
        "gracefully to local AI mode when Groq is unavailable. No real attacks, filesystem commands, "
        "network attacks, or database operations are controlled by Groq.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- 5. How to create a Groq account ---
    story.append(Paragraph("5. How to create a Groq account?", h2))
    story.append(Paragraph(
        "1. Go to https://console.groq.com and click \"Sign Up\".<br/>"
        "2. Register with your email address and verify your account.<br/>"
        "3. Log in to the Groq Console.<br/>"
        "4. Navigate to the \"API Keys\" section to generate your first key.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- 6. How to create an API key ---
    story.append(Paragraph("6. How to create an API key?", h2))
    story.append(Paragraph(
        "1. In the Groq Console, go to \"API Keys\" → \"Create Key\".<br/>"
        "2. Enter a descriptive name (e.g., \"SecureDT\").<br/>"
        "3. Set appropriate restrictions if desired (IP limits, usage caps).<br/>"
        "4. Click \"Create\" and copy the key immediately - it will not be shown again.<br/>"
        "5. The key typically starts with \"gsk_\" followed by the secret key string.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- 7. Where to put the key ---
    story.append(Paragraph("7. Where to put the key?", h2))
    story.append(Paragraph(
        "The Groq API key must be placed ONLY in your local .env file at the project root:<br/>"
        "> create/open: .env<br/>"
        "> add: GROQ_API_KEY=YOUR_GROQ_API_KEY<br/>"
        "> add: GROQ_MODEL=YOUR_SELECTED_MODEL<br/>"
        "> The key must NEVER be committed to Git, included in source code, HTML, JavaScript, "
        "CSS, databases, PDFs, or README files. The official Groq security guidance recommends "
        "environment variables/secret management and warns against exposing keys in frontend/browser code.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- 8. How to configure .env ---
    story.append(Paragraph("8. How to configure .env?", h2))
    story.append(Paragraph(
        "Copy .env.example to .env and set your values:<br/>"
        "> cp .env.example .env<br/>"
        "> GROQ_API_KEY=your_key_here<br/>"
        "> GROQ_MODEL=llama-3.3-70b-versatile (or your preferred model)<br/>"
        "> AI_PROVIDER=groq (to enable) or AI_PROVIDER=localfeatures (default, offline)<br/>"
        "> The app will show \"Groq AI is not configured. Local AI mode is active.\" if the key "
        "is missing, and continue working fully offline.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- 9. How to test the key ---
    story.append(Paragraph("9. How to test the key?", h2))
    story.append(Paragraph(
        "1. Start the Django/Flaask server: python manage.py runserver (or python app.py)<br/>"
        "2. Visit the health endpoint or use the AI explain feature in the UI.<br/>"
        "3. If Groq is configured correctly, you will see LLM insights in the response.<br/>"
        "4. If the key is invalid or expired, the app will fall back to local AI and display a "
        "configuration warning (but will NOT crash).",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- 10. How to select the model ---
    story.append(Paragraph("10. How to select the model?", h2))
    story.append(Paragraph(
        "Model selection is configured via the GROQ_MODEL environment variable in .env:<br/>"
        "GROQ_MODEL=llama-3.3-70b-versatile<br/>"
        "GROQ_MODEL=mixtral-8x7b-32768<br/>"
        "GROQ_MODEL=gemma-7b-it<br/>"
        "The default is \"llama-3.3-70b-versatile\". If a configured model becomes unavailable, "
        "the app will show a clear configuration error and fall back to local AI mode.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- 11. How to start Django ---
    story.append(Paragraph("11. How to start Django?", h2))
    story.append(Paragraph(
        "1. Apply migrations: python manage.py migrate<br/>"
        "2. Create a superuser: python manage.py createsuperuser<br/>"
        "3. Start the server: python manage.py runserver<br/>"
        "4. Open your browser at http://127.0.0.1:8000<br/>"
        "5. Register a new account and log in to access all features.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- 12. How to verify Groq ---
    story.append(Paragraph("12. How to verify Groq?", h2))
    story.append(Paragraph(
        "1. Check the /api/ai/status endpoint - it will report \"llm\": \"online\" when Groq is "
        "configured.<br/>"
        "2. Use the setup_check.py script: python scripts/setup_check.py - it will report Groq SDK "
        "status.<br/>"
        "3. Look for the \"Groq AI is not configured. Local AI mode is active.\" message if the key "
        "is missing - this confirms the fallback is working correctly.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- 13. What happens if the key is missing ---
    story.append(Paragraph("13. What happens if the key is missing?", h2))
    story.append(Paragraph(
        "If GROQ_API_KEY is not set or is empty:<br/>"
        "• The application does NOT crash.<br/>"
        "• AI_PROVIDER falls back to \"localfeatures\" (offline Random Forest).<br/>"
        "• All core functionality continues working.<br/>"
        "• /api/ai/explain returns risk analysis without Groq insights.<br/>"
        "• The UI shows a notification that Groq is offline, and local AI mode is active.<br/>"
        "• No real API key is transmitted or logged anywhere.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- 14. Security precautions ---
    story.append(Paragraph("14. Security precautions?", h2))
    story.append(Paragraph(
        "• The GROQ_API_KEY is never logged, echoed, or exposed in any API response.<br/>"
        "• Keys are read exclusively from environment variables (.env) at runtime.<br/>"
        "• All Groq requests go through the backend only - the browser never sees the key.<br/>"
        "• Requests are timeout-protected (config.GROQ_TIMEOUT, default 30 seconds).<br/>"
        "• Exception handling ensures a single failed request does not bring down the service.<br/>"
        "• Rate limiting applies to Groq API calls per client.<br/>"
        "• Response validation ensures only expected fields are used from Groq responses.<br/>"
        "• The key is never stored in database, frontend code, or version control.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- 15. How to revoke/rotate the key ---
    story.append(Paragraph("15. How to revoke/rotate the key?", h2))
    story.append(Paragraph(
        "1. In the Groq Console, go to \"API Keys\" and select your key.<br/>"
        "2. Click \"Revoke\" to immediately invalidate the current key, or \"Rotate\" to generate "
        "a new one.<br/>"
        "3. Update your .env file with the new key: GROQ_API_KEY=new_key_here<br/>"
        "4. Restart the application to pick up the new key.<br/>"
        "5. The old key will be rejected by Groq Cloud after revocation.",
        body))
    story.append(Spacer(1, 4 * mm))

    # --- 16. Troubleshooting ---
    story.append(Paragraph("16. Troubleshooting?", h2))
    story.append(Paragraph(
        "Common issues and resolutions:<br/>"
        "• \"Groq API key missing\" - Add GROQ_API_KEY to your .env file.<br/>"
        "• \"Model not available\" - Change GROQ_MODEL to a supported model name.<br/>"
        "• Rate limit exceeded - Wait and retry, or reduce request frequency.<br/>"
        "• Slow response times - Groq offers different priority tiers; consider model selection.<br/>"
        "• Connection error - Verify internet access and that api.groq.com is reachable.<br/>"
        "• Key rejected - Ensure the key was copied correctly (no extra spaces or characters).<br/>"
        "If all else fails, set AI_PROVIDER=localfeatures in .env to run completely offline.",
        body))

    doc.build(story)
    print(f"  GROQ_API_SETUP_GUIDE.pdf generated")


if __name__ == "__main__":
    generate()