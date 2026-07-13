"""documents registry (DESIGN.md Section 8.1)

Revision ID: 0002
Revises: 0001
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE documents (
            id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id   uuid NOT NULL REFERENCES tenants(id),
            title       text NOT NULL,
            source_uri  text,
            mime_type   text NOT NULL,
            version     integer NOT NULL DEFAULT 1,
            status      text NOT NULL DEFAULT 'uploaded'
                        CHECK (status IN ('uploaded', 'stored', 'processing', 'indexed', 'failed')),
            checksum    text NOT NULL,
            created_at  timestamptz NOT NULL DEFAULT now(),
            indexed_at  timestamptz
        );
        CREATE INDEX documents_tenant_created_idx ON documents (tenant_id, created_at DESC);
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE documents;")
