"""Ollama adapter — the laptop-mode default (no cloud account, no API cost)."""

from typing import Any

import requests

from scriptorium_llm.base import ChatMessage, ChatResponse

_EMBED_BATCH_SIZE = 16


class OllamaProvider:
    def __init__(
        self,
        host: str = "http://localhost:11434",
        embed_model: str = "nomic-embed-text",
        chat_model: str = "llama3.2:3b",
        timeout_s: float = 300.0,
    ) -> None:
        self._host = host.rstrip("/")
        self._embed_model = embed_model
        self._chat_model = chat_model
        self._timeout_s = timeout_s

    def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for start in range(0, len(texts), _EMBED_BATCH_SIZE):
            batch = texts[start : start + _EMBED_BATCH_SIZE]
            response = requests.post(
                f"{self._host}/api/embed",
                json={"model": self._embed_model, "input": batch},
                timeout=self._timeout_s,
            )
            response.raise_for_status()
            embeddings.extend(response.json()["embeddings"])
        return embeddings

    def chat(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None = None,
        stream: bool = False,
    ) -> ChatResponse:
        if stream:
            raise NotImplementedError("streaming arrives with the agent loop (M3)")
        payload: dict[str, Any] = {
            "model": self._chat_model,
            "messages": messages,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools
        response = requests.post(
            f"{self._host}/api/chat", json=payload, timeout=self._timeout_s
        )
        response.raise_for_status()
        body = response.json()
        return ChatResponse(
            content=body["message"]["content"],
            usage={
                "input": body.get("prompt_eval_count", 0),
                "output": body.get("eval_count", 0),
            },
        )
