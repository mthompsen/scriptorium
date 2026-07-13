import uuid

from ingestion_service.pipeline import IngestJob, Pipeline


class FakeRegistry:
    def __init__(self) -> None:
        self.statuses: list[str] = []
        self.indexed = False

    def set_status(self, tenant_id: str, document_id: str, status: str) -> bool:
        self.statuses.append(status)
        return True

    def mark_indexed(self, tenant_id: str, document_id: str) -> bool:
        self.indexed = True
        self.statuses.append("indexed")
        return True


class FakeChunkStore:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def replace_document_chunks(self, tenant_id, document_id, source, chunk_ids, chunks) -> None:
        self.calls.append({"chunk_ids": chunk_ids, "chunks": chunks})


class FakeIndex:
    def __init__(self) -> None:
        self.ensured: list[int] = []
        self.deleted: list[str] = []
        self.indexed: list[dict] = []

    def ensure_index(self, tenant_id: str, dimension: int) -> None:
        self.ensured.append(dimension)

    def delete_document(self, tenant_id: str, document_id: str) -> None:
        self.deleted.append(document_id)

    def bulk_index(self, tenant_id, document_id, chunk_ids, texts, embeddings) -> None:
        self.indexed.append({"chunk_ids": chunk_ids, "texts": texts, "embeddings": embeddings})


class FakeEmbedder:
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


class ExplodingEmbedder:
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise ConnectionError("ollama is down")


def job() -> IngestJob:
    return IngestJob(
        tenant_id=str(uuid.uuid4()),
        document_id=str(uuid.uuid4()),
        filename="handbook.md",
        mime_type="text/markdown",
        content=b"# Handbook\n\n## Leave\n\nPTO is 25 days.\n",
    )


def test_happy_path_stores_embeds_indexes_and_marks_indexed() -> None:
    registry, chunk_store, index = FakeRegistry(), FakeChunkStore(), FakeIndex()
    pipeline = Pipeline(registry, chunk_store, index, FakeEmbedder())
    the_job = job()

    pipeline.run(the_job)

    assert registry.statuses == ["processing", "indexed"]
    assert index.ensured == [3]  # dimension from the embedder, not hardcoded
    assert index.deleted == [the_job.document_id]  # idempotent re-ingest
    chunk_ids = index.indexed[0]["chunk_ids"]
    assert chunk_store.calls[0]["chunk_ids"] == chunk_ids
    prefix = uuid.UUID(the_job.document_id).hex[:8]
    assert all(cid.startswith(f"{prefix}-") for cid in chunk_ids)
    assert "PTO is 25 days." in index.indexed[0]["texts"][0]


def test_failure_marks_document_failed_not_indexed() -> None:
    registry, chunk_store, index = FakeRegistry(), FakeChunkStore(), FakeIndex()
    pipeline = Pipeline(registry, chunk_store, index, ExplodingEmbedder())

    pipeline.run(job())

    assert registry.statuses == ["processing", "failed"]
    assert registry.indexed is False
    assert index.indexed == []


def test_empty_document_fails_rather_than_indexing_nothing() -> None:
    registry = FakeRegistry()
    pipeline = Pipeline(registry, FakeChunkStore(), FakeIndex(), FakeEmbedder())
    empty = job()
    empty.content = b"   \n\n   "

    pipeline.run(empty)

    assert registry.statuses == ["processing", "failed"]
