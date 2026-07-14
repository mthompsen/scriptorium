"""The RAG write path (ARCHITECTURE.md Section 9.1): parse → chunk → store →
embed → index → mark indexed. Runs on a background worker after /ingest
accepts the raw bytes (ADR-0004)."""

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Protocol

from ingestion_service.chunker import chunk as make_chunks
from ingestion_service.parsers import parse

logger = logging.getLogger(__name__)


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


@dataclass
class IngestJob:
    tenant_id: str
    document_id: str
    filename: str
    mime_type: str
    content: bytes


class Pipeline:
    def __init__(
        self,
        registry,
        chunk_store,
        index,
        embedder: Embedder,
        extractor=None,
        graph=None,
    ) -> None:
        self._registry = registry
        self._chunk_store = chunk_store
        self._index = index
        self._embedder = embedder
        # Optional graph stage (M4, ADR-0006): both must be present to run.
        self._extractor = extractor
        self._graph = graph

    def run(self, job: IngestJob) -> None:
        try:
            self._registry.set_status(job.tenant_id, job.document_id, "processing")
            blocks = parse(job.mime_type, job.content)
            chunks = make_chunks(blocks)
            if not chunks:
                raise ValueError("document produced no text chunks")
            chunk_ids = [_chunk_id(job.document_id, c.ordinal) for c in chunks]
            texts = [c.text for c in chunks]

            self._chunk_store.replace_document_chunks(
                job.tenant_id, job.document_id, job.filename, chunk_ids, chunks
            )
            embeddings = self._embedder.embed(texts)
            self._index.ensure_index(job.tenant_id, dimension=len(embeddings[0]))
            self._index.delete_document(job.tenant_id, job.document_id)
            self._index.bulk_index(job.tenant_id, job.document_id, chunk_ids, texts, embeddings)
            if self._extractor is not None and self._graph is not None:
                self._extract_graph(job, chunk_ids, chunks)
            self._registry.mark_indexed(job.tenant_id, job.document_id)
            logger.info(
                "indexed document %s (%d chunks) for tenant %s",
                job.document_id,
                len(chunks),
                job.tenant_id,
            )
        except Exception:
            logger.exception("pipeline failed for document %s", job.document_id)
            self._registry.set_status(job.tenant_id, job.document_id, "failed")

    def _extract_graph(self, job: IngestJob, chunk_ids: list[str], chunks) -> None:
        """Graph enrichment (Section 9.1). Per-chunk extraction failures are
        logged and skipped — the graph enriches a document, it must never
        fail one that already indexed."""
        chunk_rows: list[dict] = []
        entity_types: dict[str, str] = {}
        all_relations: list = []
        for chunk_id, chunk in zip(chunk_ids, chunks, strict=True):
            try:
                entities, relations = self._extractor.extract(chunk.text)
            except Exception:
                logger.exception("extraction failed for chunk %s; skipping", chunk_id)
                continue
            for entity in entities:
                entity_types[entity.name.lower()] = entity.type
            chunk_rows.append(
                {"chunk_id": chunk_id, "ordinal": chunk.ordinal, "entities": entities}
            )
            all_relations.extend(relations)
        if not chunk_rows:
            return
        self._graph.replace_document_graph(
            job.tenant_id,
            job.document_id,
            job.filename,
            chunk_rows,
            all_relations,
            entity_types,
        )
        logger.info(
            "graph updated for document %s (%d entities, %d relations)",
            job.document_id,
            len(entity_types),
            len(all_relations),
        )


class PipelineRunner:
    """In-process async execution (ADR-0004); the durable queue arrives with M6."""

    def __init__(self, pipeline: Pipeline, max_workers: int = 2) -> None:
        self._pipeline = pipeline
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="ingest"
        )

    def submit(self, job: IngestJob) -> None:
        self._executor.submit(self._pipeline.run, job)


def _chunk_id(document_id: str, ordinal: int) -> str:
    prefix = uuid.UUID(document_id).hex[:8]
    return f"{prefix}-{ordinal}"
