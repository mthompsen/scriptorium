"""Scriptorium ingestion service — the write path (DESIGN.md Section 7.2).

M0 stub: boots and serves /health. The ingestion pipeline lands in M2.
"""

from flask import Flask

SERVICE_NAME = "ingestion"


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": SERVICE_NAME}

    return app
