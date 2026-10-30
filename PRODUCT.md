# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
- Prof. Leopoldo Calderón (Análisis Técnico Bursátil, Universidad Finis Terrae): evaluates the app in a live demo, uploading a new OHLC file he chooses; grades technical analysis, functioning, chart, AI use, judgment and defense.
- Grupo 12 (Tomás Aedo, Martín Tapia, Martín Moraga), master's finance students: present and defend the app, projected in class and opened on phones.

## Product Purpose
Upload a CSV/Excel of daily candles (Fecha, Apertura, Máximo, Mínimo, Cierre, Volumen) and the app detects, draws and interprets: pivots HH/HL/LH/LL, trend, trendline, support/resistance zones and candle patterns (only those in the professor's Patterns-2 list), then an AI (Gemini, rule-based fallback) writes a technical diagnosis with a confidence level. Success: the live demo runs on an unseen file and every conclusion is traceable to evidence on the chart.

## Positioning
Evidence-first: the AI only sees what the rules detected (shown in an "evidence" panel), never predicts with certainty, and states its confidence. No buy/sell advice.

## Constraints
- Python + Streamlit + Plotly on Streamlit Community Cloud; delivery Mon 2-nov-2026.
- Must work on PC (projector) and phone. Spanish UI.
- Brand asset: Universidad Finis Terrae logo (logo.png), institutional navy #063952.
- Functionality is frozen; design-only changes.
