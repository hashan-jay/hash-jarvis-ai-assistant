"""High-level chat orchestration for the offline assistant."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generator, Optional
from uuid import uuid4

import config
from backend.memory import ConversationMemory
from backend.ollama_client import OllamaClient


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class ChatSession:
    session_id: str = field(default_factory=lambda: str(uuid4()))
    messages: list[ChatMessage] = field(default_factory=list)


class ChatService:
    """Coordinates Ollama generation and optional Chroma memory."""

    def __init__(self) -> None:
        config.ensure_directories()
        self.client = OllamaClient()
        self.memory = ConversationMemory()
        self.session = ChatSession()
        self.model = config.DEFAULT_MODEL
        self.temperature = config.DEFAULT_TEMPERATURE
        self.system_prompt = config.DEFAULT_SYSTEM_PROMPT
        self.use_memory = config.ENABLE_MEMORY_BY_DEFAULT

    def refresh_models(self) -> list[str]:
        models = self.client.list_models()
        if models and self.model not in models:
            self.model = models[0]
        return models

    def set_model(self, model: str) -> None:
        self.model = model

    def set_memory_enabled(self, enabled: bool) -> None:
        self.use_memory = enabled
        self.memory.set_enabled(enabled)

    def new_chat(self) -> None:
        self.session = ChatSession()

    def clear_memory(self) -> None:
        self.memory.clear()

    def status(self) -> dict:
        available = self.client.is_available()
        models = self.client.list_models() if available else []
        return {
            "ollama_available": available,
            "models": models,
            "selected_model": self.model,
            "memory_enabled": self.use_memory and self.memory.enabled,
            "memory_error": self.memory.init_error,
            "host": config.OLLAMA_HOST,
        }

    def _build_messages(self, user_text: str) -> list[dict]:
        messages: list[dict] = [{"role": "system", "content": self.system_prompt}]

        if self.use_memory and self.memory.enabled:
            memories = self.memory.recall(user_text)
            if memories:
                memory_block = "\n\n---\n".join(memories)
                messages.append(
                    {
                        "role": "system",
                        "content": (
                            "Relevant memories from earlier conversations:\n"
                            f"{memory_block}\n"
                            "Use them only when helpful."
                        ),
                    }
                )

        for message in self.session.messages:
            messages.append({"role": message.role, "content": message.content})

        messages.append({"role": "user", "content": user_text})
        return messages

    def stream_reply(self, user_text: str) -> Generator[str, None, None]:
        user_text = user_text.strip()
        if not user_text:
            return

        if not self.client.is_available():
            raise RuntimeError(
                "Ollama is not running. Start Ollama, then try again.\n"
                "Tip: open a terminal and run `ollama serve`."
            )

        models = self.client.list_models()
        if not models:
            raise RuntimeError(
                "No local models found. Pull one first, for example:\n"
                "`ollama pull llama3.2:3b`"
            )

        if self.model not in models:
            self.model = models[0]

        messages = self._build_messages(user_text)
        self.session.messages.append(ChatMessage(role="user", content=user_text))

        chunks: list[str] = []
        try:
            for token in self.client.chat_stream(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
            ):
                chunks.append(token)
                yield token
        except Exception as exc:
            # Roll back the user turn if generation failed before completion.
            if self.session.messages and self.session.messages[-1].role == "user":
                self.session.messages.pop()
            raise RuntimeError(f"Chat failed: {exc}") from exc

        assistant_text = "".join(chunks).strip()
        if assistant_text:
            self.session.messages.append(ChatMessage(role="assistant", content=assistant_text))
            if self.use_memory and self.memory.enabled:
                self.memory.add_exchange(user_text, assistant_text, self.session.session_id)

    def pull_model(self, model: str) -> Generator[dict, None, None]:
        yield from self.client.pull_model(model)
