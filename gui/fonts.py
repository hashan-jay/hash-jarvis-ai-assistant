"""Register bundled fonts for the CustomTkinter UI."""

from __future__ import annotations

import sys
from pathlib import Path

FONTS_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
SYNE_BOLD_PATH = FONTS_DIR / "Syne-Bold.ttf"
# Windows family name for Syne-Bold.ttf (style: Bold)
SYNE_BOLD = "Syne"

_loaded = False


def load_app_fonts() -> str:
    """Load bundled Syne Bold and return its Windows family name."""
    global _loaded
    if _loaded:
        return SYNE_BOLD

    if not SYNE_BOLD_PATH.is_file():
        return "Segoe UI"

    if sys.platform == "win32":
        try:
            from ctypes import windll

            FR_PRIVATE = 0x10
            windll.gdi32.AddFontResourceExW(str(SYNE_BOLD_PATH), FR_PRIVATE, 0)
        except Exception:
            return "Segoe UI"
    else:
        try:
            from tkinter import font as tkfont

            available = set(tkfont.families())
            if SYNE_BOLD not in available:
                return "Segoe UI"
        except Exception:
            return "Segoe UI"

    _loaded = True
    return SYNE_BOLD
