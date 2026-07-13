import io
import json

from scriptorium_llm.bedrock import BedrockProvider

STREAM_EVENTS = [
    {"contentBlockDelta": {"delta": {"text": "The answer "}}},
    {"contentBlockDelta": {"delta": {"text": "is 25."}}},
    {"contentBlockStart": {"start": {"toolUse": {"name": "search_documents"}}}},
    {"contentBlockDelta": {"delta": {"toolUse": {"input": '{"que'}}}},
    {"contentBlockDelta": {"delta": {"toolUse": {"input": 'ry": "pto"}'}}}},
    {"contentBlockStop": {}},
    {"metadata": {"usage": {"inputTokens": 50, "outputTokens": 20}}},
]


class FakeBedrockClient:
    def __init__(self) -> None:
        self.invocations: list[dict] = []
        self.conversations: list[dict] = []

    def converse_stream(self, **kwargs) -> dict:
        self.conversations.append(kwargs)
        return {"stream": iter(STREAM_EVENTS)}

    def invoke_model(self, modelId: str, body: str) -> dict:  # noqa: N803 (AWS API casing)
        self.invocations.append({"modelId": modelId, "body": json.loads(body)})
        return {"body": io.BytesIO(json.dumps({"embedding": [0.5, 0.25]}).encode())}

    def converse(self, **kwargs) -> dict:
        self.conversations.append(kwargs)
        return {
            "output": {"message": {"content": [{"text": "answer from bedrock"}]}},
            "usage": {"inputTokens": 10, "outputTokens": 5},
        }


def test_embed_invokes_titan_per_text() -> None:
    client = FakeBedrockClient()
    provider = BedrockProvider(client=client)

    embeddings = provider.embed(["alpha", "beta"])

    assert embeddings == [[0.5, 0.25], [0.5, 0.25]]
    assert [i["body"]["inputText"] for i in client.invocations] == ["alpha", "beta"]


def test_chat_maps_system_and_user_messages_to_converse() -> None:
    client = FakeBedrockClient()
    provider = BedrockProvider(client=client)

    response = provider.chat(
        [
            {"role": "system", "content": "answer only from context"},
            {"role": "user", "content": "what is the policy?"},
        ]
    )

    assert response.content == "answer from bedrock"
    assert response.usage == {"input": 10, "output": 5}
    call = client.conversations[0]
    assert call["system"] == [{"text": "answer only from context"}]
    assert call["messages"] == [
        {"role": "user", "content": [{"text": "what is the policy?"}]}
    ]


def test_chat_stream_accumulates_partial_tool_input() -> None:
    provider = BedrockProvider(client=FakeBedrockClient())

    events = list(provider.chat_stream([{"role": "user", "content": "q"}]))

    assert [e.type for e in events] == ["content_delta", "content_delta", "tool_call", "done"]
    assert "".join(e.text for e in events if e.type == "content_delta") == "The answer is 25."
    assert events[2].tool_name == "search_documents"
    assert events[2].tool_input == {"query": "pto"}  # parsed from split JSON parts
    assert events[3].usage == {"input": 50, "output": 20}
