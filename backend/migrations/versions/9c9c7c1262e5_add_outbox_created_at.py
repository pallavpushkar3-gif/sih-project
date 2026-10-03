"""add outbox creation timestamp

Revision ID: 9c9c7c1262e5
Revises: 605fbc678b90
Create Date: 2026-10-04 03:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "9c9c7c1262e5"
down_revision: str | Sequence[str] | None = "605fbc678b90"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "outbox_events",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("outbox_events", "created_at")
