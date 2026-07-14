"""Scriptorium agent orchestrator — the reason path (ARCHITECTURE.md Section 7.4).

M3: bounded tool-use loop with guardrails behind POST /answer (SSE stream or
JSON), full run/step tracing, and the eval harness behind POST /eval/run.
"""

import json
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

    from agent_service.catalog import DocumentsCatalog
    from agent_service.loop import AgentLoop
    from agent_service.pii import build_pii_filter
    from agent_service.retrieval_client import RetrievalClient
    from agent_service.tools import build_registry
    from agent_service.trace import TraceStore

    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://scriptorium:scriptorium-dev@localhost:5432/scriptorium",
    )
    retrieval = RetrievalClient(os.environ.get("RETRIEVAL_URL", "http://localhost:8080"))
    llm = create_provider()
    loop = AgentLoop(
        llm=llm,
        registry=build_registry(retrieval, DocumentsCatalog(database_url)),
        trace=TraceStore(database_url),
        pii_filter=build_pii_filter(os.environ.get("PII_FILTER", "basic")),
        max_steps=int(os.environ.get("AGENT_MAX_STEPS", "6")),
        timeout_s=float(os.environ.get("AGENT_TIMEOUT_S", "240")),
    )
    # The groundedness judge may run on a different (stronger) model than the
    # loop: JUDGE_LLM_PROVIDER / JUDGE_CHAT_MODEL override; default = main LLM.
    judge_env = dict(os.environ)
    if os.environ.get("JUDGE_LLM_PROVIDER"):
        judge_env["LLM_PROVIDER"] = os.environ["JUDGE_LLM_PROVIDER"]
    if os.environ.get("JUDGE_CHAT_MODEL"):
        judge_env["CHAT_MODEL"] = os.environ["JUDGE_CHAT_MODEL"]
    judge = create_provider(judge_env)
    return loop, retrieval, judge


def _sse(event_type: str, data: dict) -> str:
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


def create_app(loop=None, retrieval=None, llm=None) -> Flask:
    """App factory. Tests inject fakes; production builds from env."""
    if loop is None or retrieval is None or llm is None:
        default_loop, default_retrieval, default_llm = _build_default_dependencies()
        loop = loop or default_loop
        retrieval = retrieval or default_retrieval
        llm = llm or default_llm

    app = Flask(__name__)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": SERVICE_NAME}

    @app.post("/answer")
    def answer():
        body = request.get_json(silent=True) or {}
        tenant_id = body.get("tenant_id", "")
        question = (body.get("question") or "").strip()
        stream = bool(body.get("stream", True))
        if not _is_uuid(tenant_id):
            return jsonify(error="tenant_id must be a UUID"), 400
        if not question or len(question) > 8000:
            return jsonify(error="question must be 1-8000 characters"), 400

        if not stream:
            final: dict = {}
            for event in loop.run(tenant_id, question):
                if event.type == "final":
                    final = event.data
            return jsonify(final), 200

        def generate():
            for event in loop.run(tenant_id, question):
                yield _sse(event.type, event.data)

        return Response(
            generate(),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.post("/eval/run")
    def eval_run():
        from agent_service.evaluation import (
            LabeledQuery,
            evaluate_generation,
            evaluate_retrieval,
        )

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
        result = {"retrieval": evaluate_retrieval(retrieval, tenant_id, labeled, k)}
        if body.get("generation"):
            subset = labeled[: int(body.get("generation_subset", 5))]
            result["generation"] = evaluate_generation(loop, llm, tenant_id, subset)
        return jsonify(result), 200

    return app
