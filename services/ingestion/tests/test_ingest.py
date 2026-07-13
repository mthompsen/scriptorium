import io
import uuid

from ingestion_service import create_app


class FakeRegistry:
    def __init__(self, known: bool = True) -> None:
        self.known = known
        self.calls: list[tuple[str, str]] = []

    def mark_stored(self, tenant_id: str, document_id: str) -> bool:
        self.calls.append((tenant_id, document_id))
        return self.known


class FakeStore:
    def __init__(self) -> None:
        self.puts: list[dict] = []

    def put(self, **kwargs) -> None:
        self.puts.append(kwargs)


class FakeRunner:
    def __init__(self) -> None:
        self.jobs: list = []

    def submit(self, job) -> None:
        self.jobs.append(job)


def client(registry: FakeRegistry, store: FakeStore, runner: FakeRunner | None = None):
    return create_app(
        registry=registry, store=store, runner=runner or FakeRunner()
    ).test_client()


def multipart(document_id: str, tenant_id: str) -> dict:
    return {
        "document_id": document_id,
        "tenant_id": tenant_id,
        "file": (io.BytesIO(b"# Employee Handbook"), "handbook.md", "text/markdown"),
    }


def test_ingest_stores_bytes_marks_stored_and_schedules_pipeline() -> None:
    registry, store, runner = FakeRegistry(), FakeStore(), FakeRunner()
    document_id, tenant_id = str(uuid.uuid4()), str(uuid.uuid4())

    response = client(registry, store, runner).post(
        "/ingest", data=multipart(document_id, tenant_id), content_type="multipart/form-data"
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "document_id": document_id,
        "status": "stored",
        "pipeline": "scheduled",
    }
    assert store.puts[0]["content"] == b"# Employee Handbook"
    assert store.puts[0]["mime_type"] == "text/markdown"
    assert registry.calls == [(tenant_id, document_id)]
    assert len(runner.jobs) == 1
    assert runner.jobs[0].document_id == document_id
    assert runner.jobs[0].content == b"# Employee Handbook"


def test_ingest_rejects_non_uuid_identifiers() -> None:
    registry, store = FakeRegistry(), FakeStore()

    response = client(registry, store).post(
        "/ingest",
        data={"document_id": "not-a-uuid; DROP TABLE documents", "tenant_id": str(uuid.uuid4())},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert store.puts == []


def test_ingest_requires_a_file() -> None:
    registry, store = FakeRegistry(), FakeStore()

    response = client(registry, store).post(
        "/ingest",
        data={"document_id": str(uuid.uuid4()), "tenant_id": str(uuid.uuid4())},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400


def test_ingest_404s_for_unknown_document() -> None:
    registry, store = FakeRegistry(known=False), FakeStore()

    response = client(registry, store).post(
        "/ingest",
        data=multipart(str(uuid.uuid4()), str(uuid.uuid4())),
        content_type="multipart/form-data",
    )

    assert response.status_code == 404
