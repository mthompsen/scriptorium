"""Scriptorium agent orchestrator — the reason path (DESIGN.md Section 7.4).

M0 stub: boots and serves /health. The tool-use agent loop lands in M3.
"""

from flask import Flask

SERVICE_NAME = "agent"


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": SERVICE_NAME}

    return app
