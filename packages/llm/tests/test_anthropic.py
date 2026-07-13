from dataclasses import dataclass, field
from types import SimpleNamespace

from scriptorium_llm.anthropic_api import AnthropicProvider, convert_tools_to_anthropic


def _ns(**kwargs) -> SimpleNamespace:
    return SimpleNamespace(**kwargs)


STREAM_EVENTS = [
    _ns(type="message_start", message=_ns(usage=_ns(input_tokens=120))),
    _ns(type="content_block_start", index=0, content_block=_ns(type="text")),
    _ns(type="content_block_delta", delta=_ns(type="text_delta", text="The answer ")),
    _ns(type="content_block_delta", delta=_ns(type="text_delta", text="is 25.")),
    _ns(type="content_block_stop", index=0),
    _ns(
        type="content_block_start",
        index=1,
        content_block=_ns(type="tool_use", id="toolu_1", name="search_documents"),
    ),
    _ns(type="content_block_delta", delta=_ns(type="input_json_delta", partial_json='{"que')),
    _ns(type="content_block_delta", delta=_ns(type="input_json_delta", partial_json='ry": "pto"}')),
    _ns(type="content_block_stop", index=1),
    _ns(type="message_delta", usage=_ns(output_tokens=42)),
    _ns(type="message_stop"),
]


@dataclass
class FakeMessagesApi:
    calls: list = field(default_factory=list)

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if kwargs.get("stream"):
            return iter(STREAM_EVENTS)
        return _ns(
            content=[_ns(type="text", text="grounded answer [ab12cd34-0]")],
            usage=_ns(input_tokens=100, output_tokens=30),
        )


def build_provider() -> tuple[AnthropicProvider, FakeMessagesApi]:
    api = FakeMessagesApi()
    return AnthropicProvider(client=_ns(messages=api)), api


FUNCTION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_documents",
            "description": "search",
            "parameters": {"type": "object", "properties": {"query": {"type": "string"}}},
        },
    }
]


def test_chat_converts_system_and_tools_and_parses_usage() -> None:
    provider, api = build_provider()

    response = provider.chat(
        [
            {"role": "system", "content": "answer only from context"},
            {"role": "user", "content": "PTO?"},
        ],
        tools=FUNCTION_TOOLS,
    )

    assert response.content == "grounded answer [ab12cd34-0]"
    assert response.usage == {"input": 100, "output": 30}
    call = api.calls[0]
    assert call["model"] == "claude-opus-4-8"
    assert call["system"] == "answer only from context"
    assert call["tools"] == [
        {
            "name": "search_documents",
            "description": "search",
            "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}},
        }
    ]
    assert call["messages"] == [{"role": "user", "content": "PTO?"}]


def test_chat_stream_yields_deltas_tool_calls_and_usage() -> None:
    provider, _ = build_provider()

    events = list(provider.chat_stream([{"role": "user", "content": "q"}]))

    assert [e.type for e in events] == [
        "content_delta",
        "content_delta",
        "tool_call",
        "done",
    ]
    assert "".join(e.text for e in events if e.type == "content_delta") == "The answer is 25."
    assert events[2].tool_name == "search_documents"
    assert events[2].tool_input == {"query": "pto"}  # accumulated from partial JSON
    assert events[3].usage == {"input": 120, "output": 42}


def test_tool_loop_messages_convert_to_tool_use_and_result_blocks() -> None:
    provider, api = build_provider()

    provider.chat(
        [
            {"role": "user", "content": "PTO?"},
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {"function": {"name": "search_documents", "arguments": {"query": "pto"}}}
                ],
            },
            {"role": "tool", "name": "search_documents", "content": '[{"chunk_id": "c0"}]'},
        ]
    )

    messages = api.calls[0]["messages"]
    assistant = messages[1]
    assert assistant["role"] == "assistant"
    tool_use = assistant["content"][0]
    assert tool_use["type"] == "tool_use"
    assert tool_use["input"] == {"query": "pto"}
    result = messages[2]
    assert result["role"] == "user"
    assert result["content"][0]["type"] == "tool_result"
    assert result["content"][0]["tool_use_id"] == tool_use["id"]  # ids pair up


def test_embed_is_explicitly_unsupported() -> None:
    provider, _ = build_provider()

    import pytest

    with pytest.raises(NotImplementedError, match="embeddings"):
        provider.embed(["text"])


def test_convert_tools_accepts_bare_definitions() -> None:
    bare = [{"name": "t", "parameters": {"type": "object"}}]

    assert convert_tools_to_anthropic(bare)[0]["input_schema"] == {"type": "object"}
