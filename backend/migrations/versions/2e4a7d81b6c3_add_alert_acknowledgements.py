"""add alert acknowledgement history

Revision ID: 2e4a7d81b6c3
Revises: 9c9c7c1262e5
Create Date: 2026-10-04 04:15:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "2e4a7d81b6c3"
down_revision: str | Sequence[str] | None = "9c9c7c1262e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "alert_acknowledgements",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("alert_id", sa.String(length=64), nullable=False),
        sa.Column("actor", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("alert_id", "actor", name="uq_alert_acknowledgement_actor"),
    )
    op.create_index(
        op.f("ix_alert_acknowledgements_alert_id"),
        "alert_acknowledgements",
        ["alert_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_alert_acknowledgements_alert_id"),
        table_name="alert_acknowledgements",
    )
    op.drop_table("alert_acknowledgements")
