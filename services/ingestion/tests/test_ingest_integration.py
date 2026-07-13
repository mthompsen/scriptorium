"""Integration test: real Postgres (with the real Alembic migrations) + real Mongo.

Uses Testcontainers (DESIGN.md Section 13); requires a Docker daemon.
"""

import io
import os
import pathlib
import subprocess
import sys
import uuid

import psycopg
import pytest
from pymongo import MongoClient
from testcontainers.mongodb import MongoDbContainer
from testcontainers.postgres import PostgresContainer

from ingestion_service import create_app
from ingestion_service.storage import DocumentRegistry, RawDocumentStore

SERVICE_DIR = pathlib.Path(__file__).resolve().parents[1]
DEMO_TENANT_ID = "11111111-1111-4111-8111-111111111111"


@pytest.fixture(scope="module")
def postgres_url():
    with PostgresContainer("postgres:16-alpine", driver=None) as pg:
        url = pg.get_connection_url()
        subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=SERVICE_DIR,
            env={**os.environ, "DATABASE_URL": url},
            check=True,
        )
        yield url


@pytest.fixture(scope="module")
def mongo_url():
    with MongoDbContainer("mongo:7") as mongo:
        yield mongo.get_connection_url()


def test_ingest_persists_raw_bytes_and_advances_registry(postgres_url, mongo_url) -> None:
    document_id = str(uuid.uuid4())
    with psycopg.connect(postgres_url) as conn:
        conn.execute(
            "INSERT INTO documents (id, tenant_id, title, mime_type, checksum) "
            "VALUES (%s, %s, 'handbook.md', 'text/markdown', 'abc123')",
            (document_id, DEMO_TENANT_ID),
        )

    app = create_app(
        registry=DocumentRegistry(postgres_url),
        store=RawDocumentStore(mongo_url, database="test"),
    )
    response = app.test_client().post(
        "/ingest",
        data={
            "document_id": document_id,
            "tenant_id": DEMO_TENANT_ID,
            "file": (io.BytesIO(b"# Employee Handbook"), "handbook.md", "text/markdown"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200

    raw = MongoClient(mongo_url)["test"]["raw_documents"].find_one({"_id": document_id})
    assert raw is not None
    assert bytes(raw["content"]) == b"# Employee Handbook"
    assert raw["tenant_id"] == DEMO_TENANT_ID

    with psycopg.connect(postgres_url) as conn:
        status = conn.execute(
            "SELECT status FROM documents WHERE id = %s", (document_id,)
        ).fetchone()[0]
    assert status == "stored"
