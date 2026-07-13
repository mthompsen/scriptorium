"""seed roles and the demo tenant/user for laptop mode

Demo credentials (documented in the README; dev-only, never used in cloud
deployments): demo@scriptorium.local / scriptorium-demo

Revision ID: 0004
Revises: 0003
"""

import bcrypt
from alembic import op
from sqlalchemy import text

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

# Fixed UUIDs so scripts and tests can reference the demo principals.
DEMO_TENANT_ID = "11111111-1111-4111-8111-111111111111"
DEMO_USER_ID = "22222222-2222-4222-8222-222222222222"
DEMO_EMAIL = "demo@scriptorium.local"
DEMO_PASSWORD = "scriptorium-demo"


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("INSERT INTO roles (name) VALUES ('owner'), ('admin'), ('member'), ('viewer')"))
    conn.execute(
        text("INSERT INTO tenants (id, name) VALUES (:id, 'Demo Tenant')"),
        {"id": DEMO_TENANT_ID},
    )
    password_hash = bcrypt.hashpw(DEMO_PASSWORD.encode(), bcrypt.gensalt()).decode()
    conn.execute(
        text(
            "INSERT INTO users (id, tenant_id, email, password_hash) "
            "VALUES (:id, :tenant_id, :email, :password_hash)"
        ),
        {
            "id": DEMO_USER_ID,
            "tenant_id": DEMO_TENANT_ID,
            "email": DEMO_EMAIL,
            "password_hash": password_hash,
        },
    )
    conn.execute(
        text(
            "INSERT INTO user_roles (user_id, role_id, tenant_id) "
            "SELECT :user_id, id, :tenant_id FROM roles WHERE name = 'owner'"
        ),
        {"user_id": DEMO_USER_ID, "tenant_id": DEMO_TENANT_ID},
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("DELETE FROM user_roles WHERE user_id = :id"), {"id": DEMO_USER_ID})
    conn.execute(text("DELETE FROM users WHERE id = :id"), {"id": DEMO_USER_ID})
    conn.execute(text("DELETE FROM tenants WHERE id = :id"), {"id": DEMO_TENANT_ID})
    conn.execute(text("DELETE FROM roles"))
