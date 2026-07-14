"""seed a read-only viewer user in the demo tenant

Demonstrates the BFF role gate (ARCHITECTURE.md Section 11): this user holds
only the 'viewer' role and is denied write actions such as document upload,
while retaining read access. Dev-only credentials, documented in the README;
never used in cloud deployments: viewer@scriptorium.local / scriptorium-view

Revision ID: 0007
Revises: 0006
"""

import bcrypt
from alembic import op
from sqlalchemy import text

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

# Same demo tenant as 0004; fixed UUID so tests can reference the viewer.
DEMO_TENANT_ID = "11111111-1111-4111-8111-111111111111"
VIEWER_USER_ID = "33333333-3333-4333-8333-333333333333"
VIEWER_EMAIL = "viewer@scriptorium.local"
VIEWER_PASSWORD = "scriptorium-view"


def upgrade() -> None:
    conn = op.get_bind()
    password_hash = bcrypt.hashpw(VIEWER_PASSWORD.encode(), bcrypt.gensalt()).decode()
    conn.execute(
        text(
            "INSERT INTO users (id, tenant_id, email, password_hash) "
            "VALUES (:id, :tenant_id, :email, :password_hash)"
        ),
        {
            "id": VIEWER_USER_ID,
            "tenant_id": DEMO_TENANT_ID,
            "email": VIEWER_EMAIL,
            "password_hash": password_hash,
        },
    )
    conn.execute(
        text(
            "INSERT INTO user_roles (user_id, role_id, tenant_id) "
            "SELECT :user_id, id, :tenant_id FROM roles WHERE name = 'viewer'"
        ),
        {"user_id": VIEWER_USER_ID, "tenant_id": DEMO_TENANT_ID},
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("DELETE FROM user_roles WHERE user_id = :id"), {"id": VIEWER_USER_ID})
    conn.execute(text("DELETE FROM users WHERE id = :id"), {"id": VIEWER_USER_ID})
