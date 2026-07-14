import pytest

from ingestion_service.indexer import OpenSearchIndex


class FakeResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")


def test_delete_document_retries_transient_503(monkeypatch: pytest.MonkeyPatch) -> None:
    statuses = iter([503, 503, 200])
    calls = {"count": 0}

    def fake_post(url, json, timeout):
        calls["count"] += 1
        return FakeResponse(next(statuses))

    monkeypatch.setattr("requests.post", fake_post)
    monkeypatch.setattr("time.sleep", lambda s: None)

    OpenSearchIndex("http://opensearch:9200").delete_document("tenant", "doc")

    assert calls["count"] == 3  # two 503s retried, then success


def test_delete_document_gives_up_after_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("requests.post", lambda url, json, timeout: FakeResponse(503))
    monkeypatch.setattr("time.sleep", lambda s: None)

    with pytest.raises(RuntimeError, match="http 503"):
        OpenSearchIndex("http://opensearch:9200").delete_document("tenant", "doc")


def test_delete_document_still_tolerates_missing_index(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("requests.post", lambda url, json, timeout: FakeResponse(404))

    OpenSearchIndex("http://opensearch:9200").delete_document("tenant", "doc")  # no raise
