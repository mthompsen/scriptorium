"""MongoDB chunk store (DESIGN.md Section 8.2)."""

from pymongo import MongoClient

from ingestion_service.chunker import Chunk


class ChunkStore:
    def __init__(self, mongo_url: str, database: str = "scriptorium") -> None:
        self._collection = MongoClient(mongo_url)[database]["chunks"]

    def replace_document_chunks(
        self,
        tenant_id: str,
        document_id: str,
        source: str,
        chunk_ids: list[str],
        chunks: list[Chunk],
    ) -> None:
        """Idempotent per document: previous chunks are replaced wholesale."""
        self._collection.delete_many({"tenant_id": tenant_id, "document_id": document_id})
        self._collection.insert_many(
            [
                {
                    "_id": chunk_id,
                    "tenant_id": tenant_id,
                    "document_id": document_id,
                    "ordinal": chunk.ordinal,
                    "text": chunk.text,
                    "token_count": chunk.token_count,
                    "headings": chunk.headings,
                    "metadata": {"source": source},
                }
                for chunk_id, chunk in zip(chunk_ids, chunks, strict=True)
            ]
        )
