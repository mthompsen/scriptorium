"""Persistence adapters for the ingestion service (ports-and-adapters, Section 7).

The domain routes depend on these two small ports; tests substitute fakes.
"""

import datetime

import psycopg
from pymongo import MongoClient


class DocumentRegistry:
    """Postgres adapter for the tenant-scoped document registry (Section 8.1)."""

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    def mark_stored(self, tenant_id: str, document_id: str) -> bool:
        """Advance a document to 'stored'. Returns False if no such tenant-scoped row."""
        with psycopg.connect(self._database_url) as conn:
            cursor = conn.execute(
                "UPDATE documents SET status = 'stored' WHERE tenant_id = %s AND id = %s",
                (tenant_id, document_id),
            )
            return cursor.rowcount == 1


class RawDocumentStore:
    """MongoDB adapter for raw uploaded bytes (Section 8.2; M1 scope per ADR-0003)."""

    def __init__(self, mongo_url: str, database: str = "scriptorium") -> None:
        self._collection = MongoClient(mongo_url)[database]["raw_documents"]

    def put(
        self, tenant_id: str, document_id: str, filename: str, mime_type: str, content: bytes
    ) -> None:
        # Keyed by document id and replaced on retry: ingestion stays idempotent
        # per document version (Section 7.2).
        self._collection.replace_one(
            {"_id": document_id},
            {
                "tenant_id": tenant_id,
                "filename": filename,
                "mime_type": mime_type,
                "content": content,
                "stored_at": datetime.datetime.now(datetime.UTC),
            },
            upsert=True,
        )
