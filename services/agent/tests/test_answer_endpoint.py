import json
import uuid

from agent_service import create_app
from agent_service.loop import AgentEvent


class FakeLoop:
    def run(self, tenant_id: str, question: str):
        yield AgentEvent("run_start", {"run_id": "run-1"})
        yield AgentEvent("tool", {"name": "search_documents", "summary": "1 result(s)"})
        yield AgentEvent("token", {"text": "PTO is 25 days "})
        yield AgentEvent("token", {"text": "[ab12cd34-0]."})
        yield AgentEvent(
            "final",
            {
                "run_id": "run-1",
                "answer": "PTO is 25 days [ab12cd34-0].",
                "citations": [{"chunk_id": "ab12cd34-0", "document_id": "d", "snippet": "…"}],
                "grounded": True,
            },
        )


class FakeRetrieval:
    def retrieve(self, tenant_id: str, query: str, k: int) -> list[dict]:
        return [{"chunk_id": "c-0", "document_id": "doc-1", "text": "…", "score": 1.0}]


class FakeLLM:
    def chat(self, messages, tools=None, stream=False):
        raise AssertionError("judge should not be called without generation flag")


def client():
    return create_app(loop=FakeLoop(), retrieval=FakeRetrieval(), llm=FakeLLM()).test_client()


def test_answer_requires_valid_tenant_and_question() -> None:
    response = client().post("/answer", json={"tenant_id": "nope", "question": "hi"})
    assert response.status_code == 400

    response = client().post(
        "/answer", json={"tenant_id": str(uuid.uuid4()), "question": "  "}
    )
    assert response.status_code == 400


def test_answer_streams_sse_events_in_order() -> None:
    response = client().post(
        "/answer", json={"tenant_id": str(uuid.uuid4()), "question": "PTO?"}
    )

    assert response.status_code == 200
    assert response.mimetype == "text/event-stream"
    body = response.get_data(as_text=True)
    event_types = [
        line.split(": ", 1)[1] for line in body.splitlines() if line.startswith("event: ")
    ]
    assert event_types == ["run_start", "tool", "token", "token", "final"]
    final_payload = json.loads(body.strip().split("data: ")[-1])
    assert final_payload["grounded"] is True


def test_answer_json_mode_returns_the_final_event() -> None:
    response = client().post(
        "/answer",
        json={"tenant_id": str(uuid.uuid4()), "question": "PTO?", "stream": False},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["answer"] == "PTO is 25 days [ab12cd34-0]."
    assert body["run_id"] == "run-1"


def test_eval_run_returns_retrieval_metrics() -> None:
    response = client().post(
        "/eval/run",
        json={
            "tenant_id": str(uuid.uuid4()),
            "k": 5,
            "queries": [{"query": "q", "expected_document_id": "doc-1"}],
        },
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["retrieval"]["recall_at_k"] == 1.0
    assert "generation" not in body
