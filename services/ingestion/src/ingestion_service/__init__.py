"""Scriptorium ingestion service — the write path (DESIGN.md Section 7.2).

M1: accepts internal /ingest calls from the BFF, stores raw bytes in MongoDB,
and advances the Postgres document registry (ADR-0003). The full pipeline
(parse, chunk, embed, index) lands in M2.
"""

import os
import uuid

from flask import Flask, Response, jsonify, request

SERVICE_NAME = "ingestion"

MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # request size limit (Section 12)


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


def create_app(registry=None, store=None) -> Flask:
    """App factory. Tests inject fake adapters; production builds from env."""
    if registry is None or store is None:
        from ingestion_service.storage import DocumentRegistry, RawDocumentStore

        database_url = os.environ.get(
            "DATABASE_URL",
            "postgresql://scriptorium:scriptorium-dev@localhost:5432/scriptorium",
        )
        mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
        registry = registry or DocumentRegistry(database_url)
        store = store or RawDocumentStore(mongo_url)

    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": SERVICE_NAME}

    @app.post("/ingest")
    def ingest() -> tuple[Response, int]:
        document_id = request.form.get("document_id", "")
        tenant_id = request.form.get("tenant_id", "")
        file = request.files.get("file")
        if not (_is_uuid(document_id) and _is_uuid(tenant_id)):
            return jsonify(error="document_id and tenant_id must be UUIDs"), 400
        if file is None or not file.filename:
            return jsonify(error="multipart field 'file' is required"), 400

        store.put(
            tenant_id=tenant_id,
            document_id=document_id,
            filename=file.filename,
            mime_type=file.mimetype or "application/octet-stream",
            content=file.read(),
        )
        if not registry.mark_stored(tenant_id, document_id):
            return jsonify(error="unknown document for tenant"), 404
        return jsonify(document_id=document_id, status="stored"), 200

    return app
