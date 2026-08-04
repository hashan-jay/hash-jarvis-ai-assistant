"""Thin wrapper around the local Ollama HTTP API."""

from __future__ import annotations

from typing import Generator, Iterable

import httpx
import ollama

import config


class OllamaClient:
    """Talks to a locally running Ollama server (no internet required)."""

    def __init__(self, host: str = config.OLLAMA_HOST) -> None:
        self.host = host.rstrip("/")
        self.client = ollama.Client(host=self.host)

    def is_available(self) -> bool:
        try:
            with httpx.Client(timeout=2.0) as client:
                response = client.get(f"{self.host}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

    def list_models(self, include_embedding: bool = False) -> list[str]:
        if not self.is_available():
            return []
        try:
            payload = self.client.list()
            models = payload.get("models", []) if isinstance(payload, dict) else getattr(payload, "models", [])
            names: list[str] = []
            for model in models:
                if isinstance(model, dict):
                    name = model.get("name") or model.get("model")
                else:
                    name = getattr(model, "model", None) or getattr(model, "name", None)
                if not name:
                    continue
                lower = name.lower()
                if not include_embedding and ("embed" in lower or "nomic-embed" in lower):
                    continue
                names.append(name)
            return sorted(set(names))
        except Exception:
            return []

    def pull_model(self, model: str) -> Generator[dict, None, None]:
        """Stream pull progress events from Ollama."""
        for event in self.client.pull(model, stream=True):
            if isinstance(event, dict):
                yield event
            else:
                yield {
                    "status": getattr(event, "status", "pulling"),
                    "completed": getattr(event, "completed", None),
                    "total": getattr(event, "total", None),
                }

    def chat_stream(
        self,
        model: str,
        messages: Iterable[dict],
        temperature: float = config.DEFAULT_TEMPERATURE,
    ) -> Generator[str, None, None]:
        """Stream assistant tokens for a chat completion."""
        stream = self.client.chat(
            model=model,
            messages=list(messages),
            stream=True,
            options={"temperature": temperature},
        )
        for chunk in stream:
            if isinstance(chunk, dict):
                message = chunk.get("message", {})
                content = message.get("content", "") if isinstance(message, dict) else ""
            else:
                message = getattr(chunk, "message", None)
                content = getattr(message, "content", "") if message else ""
            if content:
                yield content
