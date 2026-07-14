"""Client for the retrieval service's /retrieve endpoint (internal)."""

import requests


class RetrievalClient:
    def __init__(self, base_url: str, timeout_s: float = 30.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_s = timeout_s

    def retrieve(self, tenant_id: str, query: str, k: int = 8) -> list[dict]:
        response = requests.post(
            f"{self._base_url}/retrieve",
            json={"tenant_id": tenant_id, "query": query, "k": k},
            timeout=self._timeout_s,
        )
        response.raise_for_status()
        return response.json()["results"]

    def fetch_chunks(
        self, tenant_id: str, document_id: str, from_ordinal: int, to_ordinal: int
    ) -> list[dict]:
        response = requests.get(
            f"{self._base_url}/document/{document_id}/chunks",
            params={"tenant_id": tenant_id, "from": from_ordinal, "to": to_ordinal},
            timeout=self._timeout_s,
        )
        response.raise_for_status()
        return response.json()["chunks"]

    def graph_search(self, tenant_id: str, query: str) -> list[dict]:
        response = requests.get(
            f"{self._base_url}/graph/search",
            params={"tenant_id": tenant_id, "q": query},
            timeout=self._timeout_s,
        )
        response.raise_for_status()
        return response.json()["entities"]

    def graph_neighborhood(self, tenant_id: str, entity_id: str) -> dict:
        response = requests.get(
            f"{self._base_url}/graph/entity/{entity_id}/neighborhood",
            params={"tenant_id": tenant_id},
            timeout=self._timeout_s,
        )
        response.raise_for_status()
        return response.json()
