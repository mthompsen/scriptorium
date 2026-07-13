"""identity: tenants, users, roles, user_roles (DESIGN.md Section 8.1)

Revision ID: 0001
Revises:
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE tenants (
            id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            name        text NOT NULL UNIQUE,
            created_at  timestamptz NOT NULL DEFAULT now()
        );

        CREATE TABLE users (
            id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id      uuid NOT NULL REFERENCES tenants(id),
            email          text NOT NULL,
            password_hash  text NOT NULL,
            created_at     timestamptz NOT NULL DEFAULT now()
        );
        CREATE UNIQUE INDEX users_tenant_email_uq ON users (tenant_id, lower(email));

        CREATE TABLE roles (
            id    integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            name  text NOT NULL UNIQUE
                  CHECK (name IN ('owner', 'admin', 'member', 'viewer'))
        );

        CREATE TABLE user_roles (
            user_id    uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role_id    integer NOT NULL REFERENCES roles(id),
            tenant_id  uuid NOT NULL REFERENCES tenants(id),
            PRIMARY KEY (user_id, role_id, tenant_id)
        );
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE user_roles; DROP TABLE roles; DROP TABLE users; DROP TABLE tenants;")
