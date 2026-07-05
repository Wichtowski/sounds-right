"""create review workflow

Revision ID: 004
Revises: 003
Create Date: 2026-07-04 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "track_versions",
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "track_versions",
        sa.Column("approved_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "track_versions",
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "track_versions",
        sa.Column("rejected_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "track_versions",
        sa.Column("rejection_reason", sa.Text(), nullable=True),
    )
    op.create_foreign_key(
        "fk_track_versions_approved_by_user_id_users",
        "track_versions",
        "users",
        ["approved_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_track_versions_rejected_by_user_id_users",
        "track_versions",
        "users",
        ["rejected_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_table(
        "review_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("track_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewer_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["reviewer_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["track_version_id"], ["track_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_review_events_track_version_created_at",
        "review_events",
        ["track_version_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_review_events_track_version_created_at", table_name="review_events")
    op.drop_table("review_events")
    op.drop_constraint(
        "fk_track_versions_rejected_by_user_id_users",
        "track_versions",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_track_versions_approved_by_user_id_users",
        "track_versions",
        type_="foreignkey",
    )
    op.drop_column("track_versions", "rejection_reason")
    op.drop_column("track_versions", "rejected_by_user_id")
    op.drop_column("track_versions", "rejected_at")
    op.drop_column("track_versions", "approved_by_user_id")
    op.drop_column("track_versions", "approved_at")
