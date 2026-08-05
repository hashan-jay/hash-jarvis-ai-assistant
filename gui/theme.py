"""Dark tech palette for HASH-JARVIS."""

from __future__ import annotations

from pathlib import Path

THEME_PATH = Path(__file__).resolve().parent / "themes" / "hash_tech.json"

# Surfaces
BG = "#070B12"
SIDEBAR = "#0A101A"
MAIN = "#070B12"
SURFACE = "#0D1420"
SURFACE_RAISED = "#121A28"
COMPOSER = "#0D1420"

# Borders / lines
BORDER = "#1E2D42"
BORDER_SOFT = "#243447"
ACCENT_LINE = "#00B4D8"

# Accents
ACCENT = "#00D4FF"
ACCENT_DIM = "#00B4D8"
ACCENT_HOVER = "#0096C7"
ACCENT_GLOW = "#164E63"

# Text
TEXT = "#E2E8F0"
TEXT_MUTED = "#64748B"
TEXT_SOFT = "#94A3B8"
TEXT_ON_ACCENT = "#041016"

# Status
ONLINE = "#34D399"
OFFLINE = "#F87171"
WARN = "#FBBF24"

# Chat bubbles (light, dark) — app stays dark-first
USER_BUBBLE = ("#D1FAE5", "#0B2530")
ASSISTANT_BUBBLE = ("#E2E8F0", "#111827")
USER_LABEL = ("#0E7490", "#67E8F9")
ASSISTANT_LABEL = ("#334155", "#22D3EE")
SYSTEM_NOTE = ("#475569", "#64748B")
TAGLINE = ("#64748B", "#475569")
SECTION = ("#64748B", "#475569")
