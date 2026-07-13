"""OpenSearch adapter: one index per tenant (Section 8.4, ADR-0004)."""

import json

import requests


class OpenSearchIndex:
    def __init__(self, base_url: str, timeout_s: float = 30.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_s = timeout_s

    @staticmethod
    def index_name(tenant_id: str) -> str:
        return f"chunks-{tenant_id.lower()}"

    def ensure_index(self, tenant_id: str, dimension: int) -> None:
        body = {
            "settings": {"index.knn": True},
            "mappings": {
                "properties": {
                    "tenant_id": {"type": "keyword"},
                    "document_id": {"type": "keyword"},
                    "chunk_id": {"type": "keyword"},
                    "ordinal": {"type": "integer"},
                    "text": {"type": "text"},
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": dimension,
                        "method": {
                            "engine": "lucene",
                            "name": "hnsw",
                            "space_type": "cosinesimil",
                        },
                    },
                }
            },
        }
        response = requests.put(
            f"{self._base_url}/{self.index_name(tenant_id)}",
            json=body,
            timeout=self._timeout_s,
        )
        if response.status_code == 400 and "resource_already_exists" in response.text:
            return
        response.raise_for_status()

    def delete_document(self, tenant_id: str, document_id: str) -> None:
        """Idempotent re-ingest: drop any chunks from a previous version."""
        response = requests.post(
            f"{self._base_url}/{self.index_name(tenant_id)}/_delete_by_query",
            json={"query": {"term": {"document_id": document_id}}},
            timeout=self._timeout_s,
        )
        if response.status_code != 404:  # missing index is fine on first ingest
            response.raise_for_status()

    def bulk_index(
        self,
        tenant_id: str,
        document_id: str,
        chunk_ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
    ) -> None:
        lines: list[str] = []
        index = self.index_name(tenant_id)
        for ordinal, (chunk_id, text, embedding) in enumerate(
            zip(chunk_ids, texts, embeddings, strict=True)
        ):
            lines.append(json.dumps({"index": {"_index": index, "_id": chunk_id}}))
            lines.append(
                json.dumps(
                    {
                        "tenant_id": tenant_id,
                        "document_id": document_id,
                        "chunk_id": chunk_id,
                        "ordinal": ordinal,
                        "text": text,
                        "embedding": embedding,
                    }
                )
            )
        response = requests.post(
            # refresh so retrieval (and the eval) sees new chunks immediately
            f"{self._base_url}/_bulk?refresh=true",
            data="\n".join(lines) + "\n",
            headers={"Content-Type": "application/x-ndjson"},
            timeout=max(self._timeout_s, 60.0),
        )
        response.raise_for_status()
        body = response.json()
        if body.get("errors"):
            failed = [
                item["index"].get("error")
                for item in body.get("items", [])
                if item.get("index", {}).get("error")
            ]
            raise RuntimeError(f"bulk indexing reported errors: {failed[:3]}")
