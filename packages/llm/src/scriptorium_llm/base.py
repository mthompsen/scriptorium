from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

# A chat message: {"role": "system" | "user" | "assistant", "content": str}
ChatMessage = dict[str, str]


@dataclass
class ChatResponse:
    content: str
    # Provider-reported token usage when available: {"input": int, "output": int}
    usage: dict[str, int] = field(default_factory=dict)


@runtime_checkable
class LLMProvider(Protocol):
    """The port every provider adapter implements (Section 9.3)."""

    def embed(self, texts: list[str]) -> list[list[float]]: ...

    def chat(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None = None,
        stream: bool = False,
    ) -> ChatResponse: ...
