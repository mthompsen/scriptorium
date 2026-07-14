"""agent run/step tracing (ARCHITECTURE.md Sections 8.1 and 9.5)

Revision ID: 0006
Revises: 0005
"""

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE agent_runs (
            id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            message_id    uuid REFERENCES chat_messages(id) ON DELETE SET NULL,
            tenant_id     uuid NOT NULL REFERENCES tenants(id),
            status        text NOT NULL DEFAULT 'running'
                          CHECK (status IN ('running', 'succeeded', 'refused', 'failed')),
            total_tokens  integer NOT NULL DEFAULT 0,
            latency_ms    integer,
            created_at    timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX agent_runs_tenant_idx ON agent_runs (tenant_id, created_at DESC);

        CREATE TABLE agent_steps (
            id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            run_id      uuid NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
            step_index  integer NOT NULL,
            kind        text NOT NULL CHECK (kind IN ('think', 'tool', 'final')),
            tool_name   text,
            input_json  jsonb NOT NULL DEFAULT '{}'::jsonb,
            output_json jsonb NOT NULL DEFAULT '{}'::jsonb,
            tokens      integer NOT NULL DEFAULT 0,
            created_at  timestamptz NOT NULL DEFAULT now(),
            UNIQUE (run_id, step_index)
        );
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE agent_steps; DROP TABLE agent_runs;")
