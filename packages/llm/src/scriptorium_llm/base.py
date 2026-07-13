from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

# A chat message: {"role": "system" | "user" | "assistant" | "tool", "content": str, ...}
ChatMessage = dict[str, Any]


@dataclass
class ChatResponse:
    content: str
    # Provider-reported token usage when available: {"input": int, "output": int}
    usage: dict[str, int] = field(default_factory=dict)


@dataclass
class StreamEvent:
    """Provider-neutral streaming event (ADR-0005).

    type: "content_delta" (text carries the delta) | "tool_call" (tool_name +
    tool_input) | "done" (usage totals).
    """

    type: str
    text: str = ""
    tool_name: str = ""
    tool_input: dict[str, Any] = field(default_factory=dict)
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

    def chat_stream(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None = None,
    ) -> Iterator[StreamEvent]: ...
