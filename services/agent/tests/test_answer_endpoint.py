import uuid

from agent_service import create_app


class FakeRag:
    def answer(self, tenant_id: str, question: str) -> dict:
        return {"answer": f"answer to: {question}", "citations": [], "grounded": True}


class FakeRetrieval:
    def retrieve(self, tenant_id: str, query: str, k: int) -> list[dict]:
        return [{"chunk_id": "c-0", "document_id": "doc-1", "text": "…", "score": 1.0}]


def client():
    return create_app(rag=FakeRag(), retrieval=FakeRetrieval()).test_client()


def test_answer_requires_valid_tenant_and_question() -> None:
    response = client().post("/answer", json={"tenant_id": "nope", "question": "hi"})
    assert response.status_code == 400

    response = client().post(
        "/answer", json={"tenant_id": str(uuid.uuid4()), "question": "  "}
    )
    assert response.status_code == 400


def test_answer_delegates_to_rag() -> None:
    response = client().post(
        "/answer", json={"tenant_id": str(uuid.uuid4()), "question": "PTO?"}
    )

    assert response.status_code == 200
    assert response.get_json()["answer"] == "answer to: PTO?"


def test_eval_run_returns_metrics() -> None:
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
    assert body["recall_at_k"] == 1.0
    assert body["mrr"] == 1.0
