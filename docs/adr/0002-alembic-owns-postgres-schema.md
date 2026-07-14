# ADR-0002: Alembic, run from the ingestion service, owns the Postgres schema

- **Status:** Accepted
- **Date:** 2026-07-13

## Context

ARCHITECTURE.md Section 8.1 requires a single migration owner for the Postgres
schema and explicitly leaves the choice open: "Flyway for the JVM service's
schema, or a single migration owner such as Alembic driven from ingestion;
pick one owner and record it in an ADR." Multiple services touch Postgres
(BFF for identity/chat, ingestion for the document registry, agent for run
traces from M3), so split ownership would invite drift.

## Decision

We will use Alembic, living in `services/ingestion/migrations/`, as the sole
owner of the Postgres schema. Migrations run as a one-shot `migrate` container
in docker compose (`alembic upgrade head`) before dependent services start;
the same command runs in cloud deploys. No other service may alter schema.

Rationale: the ingestion service is the write path and the natural owner of
the system of record (Section 4); Python/Alembic keeps migrations executable
in laptop mode without a JVM; and the retrieval service — the Flyway
alternative — does not exist as a real service until M2/M4, while the schema
is needed in M1.

## Consequences

Schema changes always ship as ingestion-service commits, even when motivated
by BFF or agent features; reviewers look in one place for schema history. The
BFF consumes the schema without owning it, so its integration tests rely on
migrations having run (compose orders this via `depends_on`). If the JVM
service later needs schema it exclusively owns, that would be a new ADR.
