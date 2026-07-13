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
