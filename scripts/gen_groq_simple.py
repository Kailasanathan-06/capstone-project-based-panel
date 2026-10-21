#!/usr/bin/env python3
"""Create GROQ_API_SETUP_GUIDE.pdf - minimal version."""

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

INK = colors.HexColor("#0a0e17")
ACCENT = colors.HexColor("#35e0ff")
SILVER = colors.HexColor("#c0c0c0")
WHITE = colors.white
BLACK = colors.black

styles = getSampleStyleSheet()
title_style = ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=INK)
h2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=INK)
body = ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, leading=13, textColor=BLACK)
mono = ParagraphStyle("mono", fontName="Courier", fontSize=8, leading=11, textColor=BLACK)

doc = SimpleDocTemplate(
    os.path.join(OUT_DIR, "GROQ_API_SETUP_GUIDE.pdf"),
    pagesize=A4,
    leftMargin=20 * mm,
    rightMargin=20 * mm,
    topMargin=18 * mm,
    bottomMargin=18 * mm,
)

story = []
story.append(Paragraph("SecureDT Groq API Setup Guide", title_style))
story.append(Spacer(1, 6 * mm))
story.append(Paragraph("Version 1.0", body))
story.append(Spacer(1, 4 * mm))

story.append(Paragraph("1. What is Groq Cloud?", h2))
story.append(Paragraph("Groq Cloud is a hosted inference service providing fast LLM access via API.", body))
story.append(Spacer(1, 3 * mm))

story.append(Paragraph("2. Why Groq is used?", h2))
story.append(Paragraph("Optional AI enhancement layer for natural-language explanations and risk commentary.", body))
story.append(Spacer(1, 3 * mm))

story.append(Paragraph("3. What part uses Groq?", h2))
story.append(Paragraph("AI engine explanations, experiment summaries, risk analysis via /api/ai/explain.", body))
story.append(Spacer(1, 3 * mm))

story.append(Paragraph("4. What does NOT depend on Groq?", h2))
story.append(Paragraph("Core security, scheduling, attack simulation, Digital Twin all work offline.", body))
story.append(Spacer(1, 3 * mm))

story.append(Paragraph("5. How to create an account?", h2))
story.append(Paragraph("Go to https://console.groq.com and sign up.", body))
story.append(Spacer(1, 3 * mm))

story.append(Paragraph("6. How to create an API key?", h2))
story.append(Paragraph("In Console → API Keys → Create Key. Copy the key (starts with gsk_).", body))
story.append(Spacer(1, 3 * mm))

story.append(Paragraph("7. Where to put the key?", h2))
story.append(Paragraph("ONLY in local .env file at project root. Never in source, HTML, JS, CSS, or database.", mono))
story.append(Spacer(1, 3 * mm))

story.append(Paragraph("8. What if key is missing?", h2))
story.append(Paragraph("Application falls back to local AI mode. No crash. Message: 'Groq AI is not configured. Local AI mode is active.'", body))

doc.build(story)
print(f"  GROQ_API_SETUP_GUIDE.pdf generated")