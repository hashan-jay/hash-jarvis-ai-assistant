"""Zyntaks.lk-aligned dark palette for ZYNTAKSgenAI."""

from __future__ import annotations

from pathlib import Path

THEME_PATH = Path(__file__).resolve().parent / "themes" / "zyntaks.json"

# Surfaces — from zyntaks.lk CSS tokens
BG = "#050505"
SIDEBAR = "#0C0C0C"
MAIN = "#050505"
SURFACE = "#0C0C0C"
SURFACE_RAISED = "#141414"
COMPOSER = "#0C0C0C"

# Borders / lines (approx --border: #ffffff1a)
BORDER = "#2A2A2A"
BORDER_SOFT = "#333333"
ACCENT_LINE = "#67E8F9"

# Accents — --brand-cyan / --accent-yellow on site
ACCENT = "#67E8F9"
ACCENT_DIM = "#22D3EE"
ACCENT_HOVER = "#A5F3FC"
ACCENT_GLOW = "#164E63"

# Text — --foreground / --muted
TEXT = "#F4F4F5"
TEXT_MUTED = "#71717A"
TEXT_SOFT = "#A1A1AA"
TEXT_ON_ACCENT = "#050505"
TEXT_ON_PRIMARY = "#050505"

# Status
ONLINE = "#67E8F9"
OFFLINE = "#F87171"
WARN = "#FBBF24"

# Chat bubbles (light, dark) — app stays dark-first
USER_BUBBLE = ("#E4E4E7", "#141414")
ASSISTANT_BUBBLE = ("#F4F4F5", "#0C0C0C")
USER_LABEL = ("#52525B", "#A1A1AA")
ASSISTANT_LABEL = ("#0891B2", "#67E8F9")
SYSTEM_NOTE = ("#71717A", "#A1A1AA")
TAGLINE = ("#71717A", "#A1A1AA")
SECTION = ("#71717A", "#71717A")
