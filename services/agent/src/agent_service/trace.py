"""Run/step tracing to Postgres (DESIGN.md Sections 8.1 and 9.5)."""

import json

import psycopg


class TraceStore:
    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    def create_run(self, tenant_id: str) -> str:
        with psycopg.connect(self._database_url) as conn:
            row = conn.execute(
                "INSERT INTO agent_runs (tenant_id) VALUES (%s) RETURNING id",
                (tenant_id,),
            ).fetchone()
        return str(row[0])

    def add_step(
        self,
        run_id: str,
        step_index: int,
        kind: str,
        tool_name: str | None,
        input_json: dict,
        output_json: dict,
        tokens: int = 0,
    ) -> None:
        with psycopg.connect(self._database_url) as conn:
            conn.execute(
                "INSERT INTO agent_steps "
                "(run_id, step_index, kind, tool_name, input_json, output_json, tokens) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    run_id,
                    step_index,
                    kind,
                    tool_name,
                    json.dumps(input_json),
                    json.dumps(output_json),
                    tokens,
                ),
            )

    def finish_run(self, run_id: str, status: str, total_tokens: int, latency_ms: int) -> None:
        with psycopg.connect(self._database_url) as conn:
            conn.execute(
                "UPDATE agent_runs SET status = %s, total_tokens = %s, latency_ms = %s "
                "WHERE id = %s",
                (status, total_tokens, latency_ms, run_id),
            )
