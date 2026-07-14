"""chat sessions and messages (ARCHITECTURE.md Section 8.1)

Revision ID: 0003
Revises: 0002
"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE chat_sessions (
            id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id   uuid NOT NULL REFERENCES tenants(id),
            user_id     uuid NOT NULL REFERENCES users(id),
            title       text NOT NULL DEFAULT 'New session',
            created_at  timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX chat_sessions_tenant_user_idx
            ON chat_sessions (tenant_id, user_id, created_at DESC);

        CREATE TABLE chat_messages (
            id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id  uuid NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
            role        text NOT NULL CHECK (role IN ('user', 'assistant', 'tool')),
            content     text NOT NULL,
            created_at  timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX chat_messages_session_idx ON chat_messages (session_id, created_at);
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE chat_messages; DROP TABLE chat_sessions;")
