"""Scriptorium agent orchestrator — the reason path (DESIGN.md Section 7.4).

M2: single-shot grounded RAG behind POST /answer plus the retrieval eval
behind POST /eval/run (ADR-0004). The bounded tool-use loop lands in M3.
"""

import os
import uuid

from flask import Flask, Response, jsonify, request

SERVICE_NAME = "agent"


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


def _build_default_dependencies() -> tuple:
    from scriptorium_llm import create_provider

    from agent_service.rag import RagAnswerer
    from agent_service.retrieval_client import RetrievalClient

    retrieval = RetrievalClient(os.environ.get("RETRIEVAL_URL", "http://localhost:8080"))
    return RagAnswerer(retrieval, create_provider()), retrieval


def create_app(rag=None, retrieval=None) -> Flask:
    """App factory. Tests inject fakes; production builds from env."""
    if rag is None or retrieval is None:
        default_rag, default_retrieval = _build_default_dependencies()
        rag = rag or default_rag
        retrieval = retrieval or default_retrieval

    app = Flask(__name__)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": SERVICE_NAME}

    @app.post("/answer")
    def answer() -> tuple[Response, int]:
        body = request.get_json(silent=True) or {}
        tenant_id = body.get("tenant_id", "")
        question = (body.get("question") or "").strip()
        if not _is_uuid(tenant_id):
            return jsonify(error="tenant_id must be a UUID"), 400
        if not question or len(question) > 8000:
            return jsonify(error="question must be 1-8000 characters"), 400
        return jsonify(rag.answer(tenant_id, question)), 200

    @app.post("/eval/run")
    def eval_run() -> tuple[Response, int]:
        from agent_service.evaluation import LabeledQuery, evaluate_retrieval

        body = request.get_json(silent=True) or {}
        tenant_id = body.get("tenant_id", "")
        queries = body.get("queries", [])
        k = int(body.get("k", 5))
        if not _is_uuid(tenant_id):
            return jsonify(error="tenant_id must be a UUID"), 400
        if not queries or not (1 <= k <= 20):
            return jsonify(error="queries must be non-empty and k in 1..20"), 400
        labeled = [
            LabeledQuery(query=q["query"], expected_document_id=q["expected_document_id"])
            for q in queries
        ]
        return jsonify(evaluate_retrieval(retrieval, tenant_id, labeled, k)), 200

    return app
