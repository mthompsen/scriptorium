from ingestion_service import create_app


def test_health_returns_200_with_service_name() -> None:
    client = create_app().test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "service": "ingestion"}
