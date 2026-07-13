import json

import pytest

from scriptorium_llm import OllamaProvider


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self._payload


def test_embed_batches_inputs_of_sixteen(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict] = []

    def fake_post(url: str, json: dict, timeout: float) -> FakeResponse:
        calls.append(json)
        return FakeResponse({"embeddings": [[0.1, 0.2]] * len(json["input"])})

    monkeypatch.setattr("requests.post", fake_post)
    provider = OllamaProvider()

    embeddings = provider.embed([f"text {i}" for i in range(20)])

    assert len(embeddings) == 20
    assert [len(c["input"]) for c in calls] == [16, 4]
    assert calls[0]["model"] == "nomic-embed-text"


def test_chat_returns_content_and_usage(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    def fake_post(url: str, json: dict, timeout: float) -> FakeResponse:
        captured.update(json)
        return FakeResponse(
            {
                "message": {"role": "assistant", "content": "grounded answer [c1]"},
                "prompt_eval_count": 120,
                "eval_count": 42,
            }
        )

    monkeypatch.setattr("requests.post", fake_post)
    provider = OllamaProvider(chat_model="llama3.2:3b")

    response = provider.chat([{"role": "user", "content": "question?"}])

    assert response.content == "grounded answer [c1]"
    assert response.usage == {"input": 120, "output": 42}
    assert captured["model"] == "llama3.2:3b"
    assert captured["stream"] is False


def test_chat_rejects_stream_flag_in_favor_of_chat_stream() -> None:
    with pytest.raises(ValueError, match="chat_stream"):
        OllamaProvider().chat([{"role": "user", "content": "hi"}], stream=True)


class FakeStreamingResponse:
    def __init__(self, lines: list[dict]) -> None:
        self._lines = lines

    def raise_for_status(self) -> None:
        pass

    def iter_lines(self):
        for line in self._lines:
            yield json.dumps(line).encode()


def test_chat_stream_yields_deltas_tool_calls_and_done(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lines = [
        {"message": {"role": "assistant", "content": "Hel"}, "done": False},
        {"message": {"role": "assistant", "content": "lo"}, "done": False},
        {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {"function": {"name": "search_documents", "arguments": {"query": "pto"}}}
                ],
            },
            "done": False,
        },
        {
            "message": {"role": "assistant", "content": ""},
            "done": True,
            "prompt_eval_count": 100,
            "eval_count": 30,
        },
    ]
    monkeypatch.setattr(
        "requests.post", lambda *a, **k: FakeStreamingResponse(lines)
    )

    events = list(OllamaProvider().chat_stream([{"role": "user", "content": "q"}]))

    assert [e.type for e in events] == ["content_delta", "content_delta", "tool_call", "done"]
    assert "".join(e.text for e in events if e.type == "content_delta") == "Hello"
    assert events[2].tool_name == "search_documents"
    assert events[2].tool_input == {"query": "pto"}
    assert events[3].usage == {"input": 100, "output": 30}


def test_payload_is_json_serializable() -> None:
    # Guards against accidentally passing non-serializable structures.
    assert json.dumps([{"role": "user", "content": "hi"}])
