#!/usr/bin/env python3
"""Create GROQ_API_SETUP_GUIDE.pdf"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "SecureDT", "docs")
os.makedirs(OUT_DIR, exist_ok=True)

doc = SimpleDocTemplate(
    os.path.join(OUT_DIR, "GROQ_API_SETUP_GUIDE.pdf"),
    pagesize=A4,
    leftMargin=20,
    rightMargin=20,
    topMargin=18,
    bottomMargin=18,
)

styles = getSampleStyleSheet()
title_style = ParagraphStyle('t', fontName='Helvetica-Bold', fontSize=16, leading=20, textColor=colors.HexColor('#0a0e17'))
body_style = ParagraphStyle('b', fontName='Helvetica', fontSize=10, leading=14, textColor=colors.black)

story = [
    Paragraph('SecureDT Groq API Setup Guide', title_style),
    Spacer(1, 6),
    Paragraph('Version 1.0', body_style),
    Spacer(1, 4),
    Paragraph('1. What is Groq Cloud?', body_style),
    Paragraph('Groq Cloud is a hosted inference service providing fast LLM access via API.', body_style),
    Spacer(1, 3),
    Paragraph('2. Why Groq is used?', body_style),
    Paragraph('Optional AI enhancement layer for natural-language explanations and risk commentary.', body_style),
    Spacer(1, 3),
    Paragraph('3. What part uses Groq?', body_style),
    Paragraph('AI engine explanations via /api/ai/explain.', body_style),
    Spacer(1, 3),
    Paragraph('4. What does NOT depend on Groq?', body_style),
    Paragraph('Core security, scheduling, attack simulation, Digital Twin all work offline.', body_style),
    Spacer(1, 8),
]

doc.build(story)
print('GROQ_API_SETUP_GUIDE.pdf generated successfully')

pdf_path = os.path.join(OUT_DIR, 'GROQ_API_SETUP_GUIDE.pdf')
print('File exists:', os.path.exists(pdf_path))
print('File size:', os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 'N/A')