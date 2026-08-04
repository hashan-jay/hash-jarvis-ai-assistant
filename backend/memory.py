"""Local conversation memory backed by ChromaDB + LangChain."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

import config


class ConversationMemory:
    """Persist and retrieve relevant past exchanges offline."""

    def __init__(
        self,
        embedding_model: str = config.EMBEDDING_MODEL,
        persist_directory: Optional[str] = None,
    ) -> None:
        self.embedding_model = embedding_model
        self.persist_directory = persist_directory or str(config.MEMORY_DIR)
        self._vectorstore: Optional[Chroma] = None
        self._enabled = True
        self._init_error: Optional[str] = None
        self._initialize()

    @property
    def enabled(self) -> bool:
        return self._enabled and self._vectorstore is not None

    @property
    def init_error(self) -> Optional[str]:
        return self._init_error

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def _initialize(self) -> None:
        try:
            embeddings = OllamaEmbeddings(
                model=self.embedding_model,
                base_url=config.OLLAMA_HOST,
            )
            self._vectorstore = Chroma(
                collection_name=config.MEMORY_COLLECTION,
                embedding_function=embeddings,
                persist_directory=self.persist_directory,
            )
            self._init_error = None
        except Exception as exc:
            self._vectorstore = None
            self._init_error = str(exc)

    def rebind_embedding_model(self, embedding_model: str) -> None:
        """Point memory at a different local embedding model."""
        self.embedding_model = embedding_model
        self._initialize()

    def add_exchange(self, user_text: str, assistant_text: str, session_id: str) -> None:
        if not self.enabled or not user_text.strip() or not assistant_text.strip():
            return
        assert self._vectorstore is not None
        stamp = datetime.now(timezone.utc).isoformat()
        docs = [
            Document(
                page_content=f"User: {user_text.strip()}\nAssistant: {assistant_text.strip()}",
                metadata={
                    "session_id": session_id,
                    "timestamp": stamp,
                    "role": "exchange",
                },
            )
        ]
        try:
            self._vectorstore.add_documents(docs, ids=[str(uuid4())])
        except Exception as exc:
            self._init_error = (
                f"Memory write failed (is `{self.embedding_model}` pulled?): {exc}"
            )

    def recall(self, query: str, k: int = config.MEMORY_TOP_K) -> list[str]:
        if not self.enabled or not query.strip():
            return []
        assert self._vectorstore is not None
        try:
            docs = self._vectorstore.similarity_search(query, k=k)
            return [doc.page_content for doc in docs if doc.page_content.strip()]
        except Exception as exc:
            self._init_error = (
                f"Memory recall failed (pull `{self.embedding_model}`): {exc}"
            )
            return []

    def clear(self) -> None:
        if self._vectorstore is None:
            return
        try:
            self._vectorstore.delete_collection()
        except Exception:
            pass
        self._initialize()
