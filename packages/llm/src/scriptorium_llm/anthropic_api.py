"""Anthropic API adapter (official SDK). Requires the [anthropic] extra.

The strongest option for generation and judging quality; embeddings are not
offered by the Anthropic API — ingestion/retrieval keep their embedding
provider (Ollama locally, Titan on Bedrock).

The loop speaks the function-format message/tool dialect (assistant
`tool_calls`, `role: "tool"` results); this adapter converts to Anthropic
content blocks (`tool_use` / `tool_result`), synthesizing stable tool-use ids.
"""

import json
from collections.abc import Iterator
from typing import Any

from scriptorium_llm.base import ChatMessage, ChatResponse, StreamEvent

DEFAULT_CHAT_MODEL = "claude-opus-4-8"


class AnthropicProvider:
    def __init__(
        self,
        chat_model: str = DEFAULT_CHAT_MODEL,
        max_tokens: int = 8192,
        client: Any = None,
    ) -> None:
        if client is None:
            import anthropic

            client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
        self._client = client
        self._chat_model = chat_model
        self._max_tokens = max_tokens

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError(
            "the Anthropic API has no embeddings endpoint; keep EMBED via Ollama/Bedrock"
        )

    def chat(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None = None,
        stream: bool = False,
    ) -> ChatResponse:
        if stream:
            raise ValueError("use chat_stream() for streaming")
        response = self._client.messages.create(**self._request_kwargs(messages, tools))
        text = "".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        )
        return ChatResponse(
            content=text,
            usage={
                "input": response.usage.input_tokens,
                "output": response.usage.output_tokens,
            },
        )

    def chat_stream(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None = None,
    ) -> Iterator[StreamEvent]:
        events = self._client.messages.create(
            **self._request_kwargs(messages, tools), stream=True
        )
        usage = {"input": 0, "output": 0}
        tool_name: str | None = None
        tool_json_parts: list[str] = []
        for event in events:
            event_type = event.type
            if event_type == "message_start":
                usage["input"] = event.message.usage.input_tokens
            elif event_type == "content_block_start":
                block = event.content_block
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_json_parts = []
            elif event_type == "content_block_delta":
                delta = event.delta
                if delta.type == "text_delta":
                    yield StreamEvent(type="content_delta", text=delta.text)
                elif delta.type == "input_json_delta":
                    tool_json_parts.append(delta.partial_json)
            elif event_type == "content_block_stop":
                if tool_name is not None:
                    raw = "".join(tool_json_parts)
                    yield StreamEvent(
                        type="tool_call",
                        tool_name=tool_name,
                        tool_input=json.loads(raw) if raw else {},
                    )
                    tool_name = None
            elif event_type == "message_delta":
                usage["output"] = event.usage.output_tokens
        yield StreamEvent(type="done", usage=usage)

    def _request_kwargs(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None,
    ) -> dict[str, Any]:
        system, converted = _convert_messages(messages)
        kwargs: dict[str, Any] = {
            "model": self._chat_model,
            "max_tokens": self._max_tokens,
            "messages": converted,
        }
        if system:
            kwargs["system"] = system
        converted_tools = convert_tools_to_anthropic(tools)
        if converted_tools:
            kwargs["tools"] = converted_tools
        return kwargs


def convert_tools_to_anthropic(tools: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Function-format tool defs -> Anthropic {name, description, input_schema}."""
    converted = []
    for tool in tools or []:
        function = tool.get("function", tool)
        converted.append(
            {
                "name": function["name"],
                "description": function.get("description", ""),
                "input_schema": function["parameters"],
            }
        )
    return converted


def _convert_messages(messages: list[ChatMessage]) -> tuple[str, list[dict[str, Any]]]:
    system_parts: list[str] = []
    converted: list[dict[str, Any]] = []
    # Tool-use ids synthesized in call order; results are appended by the
    # loop in the same order, so a FIFO queue pairs them correctly.
    pending_tool_ids: list[str] = []

    for message in messages:
        role = message["role"]
        if role == "system":
            system_parts.append(str(message["content"]))
        elif role == "assistant" and message.get("tool_calls"):
            content: list[dict[str, Any]] = []
            if message.get("content"):
                content.append({"type": "text", "text": message["content"]})
            for index, call in enumerate(message["tool_calls"]):
                tool_id = f"toolu_local_{len(converted)}_{index}"
                pending_tool_ids.append(tool_id)
                function = call["function"]
                content.append(
                    {
                        "type": "tool_use",
                        "id": tool_id,
                        "name": function["name"],
                        "input": function.get("arguments") or {},
                    }
                )
            converted.append({"role": "assistant", "content": content})
        elif role == "tool":
            tool_id = pending_tool_ids.pop(0) if pending_tool_ids else "toolu_local_orphan"
            converted.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": str(message["content"]),
                        }
                    ],
                }
            )
        else:
            converted.append({"role": role, "content": message["content"]})
    return "\n\n".join(system_parts), converted
