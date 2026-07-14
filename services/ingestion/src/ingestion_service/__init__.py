"""Scriptorium ingestion service — the write path (ARCHITECTURE.md Section 7.2).

M2: /ingest stores raw bytes (ADR-0003), then a background worker runs the
RAG pipeline — parse, chunk, embed, index (Section 9.1, ADR-0004).
"""

import os
import uuid

from flask import Flask, Response, jsonify, request

from ingestion_service.pipeline import IngestJob

SERVICE_NAME = "ingestion"

MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # request size limit (Section 12)


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


def _build_default_dependencies() -> tuple:
    from scriptorium_llm import create_provider

    from ingestion_service.chunk_store import ChunkStore
    from ingestion_service.indexer import OpenSearchIndex
    from ingestion_service.pipeline import Pipeline, PipelineRunner
    from ingestion_service.storage import DocumentRegistry, RawDocumentStore

    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://scriptorium:scriptorium-dev@localhost:5432/scriptorium",
    )
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    opensearch_url = os.environ.get("OPENSEARCH_URL", "http://localhost:9200")

    registry = DocumentRegistry(database_url)
    store = RawDocumentStore(mongo_url)

    extractor = graph = None
    if os.environ.get("GRAPH_EXTRACTION", "on").lower() != "off":
        from ingestion_service.extraction import EntityExtractor
        from ingestion_service.graph_store import Neo4jGraphStore

        extractor = EntityExtractor(create_provider())
        graph = Neo4jGraphStore(
            uri=os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
            user=os.environ.get("NEO4J_USER", "neo4j"),
            password=os.environ.get("NEO4J_PASSWORD", "scriptorium-dev"),
        )

    pipeline = Pipeline(
        registry=registry,
        chunk_store=ChunkStore(mongo_url),
        index=OpenSearchIndex(opensearch_url),
        embedder=create_provider(),
        extractor=extractor,
        graph=graph,
    )
    return registry, store, PipelineRunner(pipeline)


def create_app(registry=None, store=None, runner=None) -> Flask:
    """App factory. Tests inject fake adapters; production builds from env."""
    if registry is None or store is None or runner is None:
        default_registry, default_store, default_runner = _build_default_dependencies()
        registry = registry or default_registry
        store = store or default_store
        runner = runner or default_runner

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

        mime_type = file.mimetype or "application/octet-stream"
        content = file.read()
        store.put(
            tenant_id=tenant_id,
            document_id=document_id,
            filename=file.filename,
            mime_type=mime_type,
            content=content,
        )
        if not registry.mark_stored(tenant_id, document_id):
            return jsonify(error="unknown document for tenant"), 404
        runner.submit(
            IngestJob(
                tenant_id=tenant_id,
                document_id=document_id,
                filename=file.filename,
                mime_type=mime_type,
                content=content,
            )
        )
        return jsonify(document_id=document_id, status="stored", pipeline="scheduled"), 200

    return app
