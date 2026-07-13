"""Postgres adapter for the list_recent tool (AGT → PG, Section 4)."""

import psycopg


class DocumentsCatalog:
    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    def list_recent(self, tenant_id: str, limit: int) -> list[dict]:
        with psycopg.connect(self._database_url) as conn:
            rows = conn.execute(
                "SELECT id, title, status, created_at FROM documents "
                "WHERE tenant_id = %s ORDER BY created_at DESC LIMIT %s",
                (tenant_id, limit),
            ).fetchall()
        return [
            {
                "id": str(row[0]),
                "title": row[1],
                "status": row[2],
                "created_at": row[3].isoformat(),
            }
            for row in rows
        ]
