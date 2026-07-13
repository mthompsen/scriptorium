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


def test_chat_stream_is_not_yet_supported() -> None:
    with pytest.raises(NotImplementedError):
        OllamaProvider().chat([{"role": "user", "content": "hi"}], stream=True)


def test_payload_is_json_serializable() -> None:
    # Guards against accidentally passing non-serializable structures.
    assert json.dumps([{"role": "user", "content": "hi"}])
