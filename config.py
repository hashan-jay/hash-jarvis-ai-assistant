"""Application configuration for HASH-JARVIS."""

from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MEMORY_DIR = DATA_DIR / "memory"
CHATS_DIR = DATA_DIR / "chats"

# Identity
ASSISTANT_NAME = "HASH-JARVIS"

# Ollama
OLLAMA_HOST = "http://127.0.0.1:11434"
DEFAULT_MODEL = "llama3.2:3b"
EMBEDDING_MODEL = "nomic-embed-text"
FALLBACK_MODELS = [
    "llama3.2:3b",
    "qwen2.5:3b",
    "gemma2:2b",
    "mistral:7b",
    "llama3.1:8b",
]

# Generation defaults
DEFAULT_TEMPERATURE = 0.7
DEFAULT_SYSTEM_PROMPT = (
    "You are HASH-JARVIS, a highly capable local AI assistant inspired by J.A.R.V.I.S. "
    "Address the user with polished, confident courtesy — occasionally witty, never rude. "
    "Speak in a refined British-butler register: calm, precise, and efficient. "
    "Prefer clear, actionable answers; keep humor dry and brief. "
    "When useful, open or close with light JARVIS-style flourishes "
    "(e.g. 'Certainly.', 'Right away.', 'Shall I proceed?'), but do not overdo catchphrases. "
    "You run fully offline on the user's computer. If you lack information, say so honestly "
    "and offer the next best step. Never claim to control physical systems you cannot access."
)

# Memory / RAG
MEMORY_COLLECTION = "conversation_memory"
MEMORY_TOP_K = 4
ENABLE_MEMORY_BY_DEFAULT = True

# UI
APP_TITLE = "HASH-JARVIS // LOCAL NODE"
APP_GEOMETRY = "1180x760"
APPEARANCE_MODE = "dark"
# Resolved in gui.app against gui/themes/hash_tech.json
COLOR_THEME = "hash_tech"


def ensure_directories() -> None:
    """Create local data directories if they do not exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    CHATS_DIR.mkdir(parents=True, exist_ok=True)
