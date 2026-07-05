"""create publications

Revision ID: 005
Revises: 004
Create Date: 2026-07-04 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "publications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("track_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("track_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("public_manifest_object_key", sa.Text(), nullable=False),
        sa.Column("public_latest_object_key", sa.Text(), nullable=True),
        sa.Column("public_transcript_object_key", sa.Text(), nullable=False),
        sa.Column("public_segments_object_key", sa.Text(), nullable=True),
        sa.Column("public_words_object_key", sa.Text(), nullable=True),
        sa.Column("published_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("unpublished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["published_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["track_id"], ["tracks.id"]),
        sa.ForeignKeyConstraint(["track_version_id"], ["track_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("track_id", "version", name="uq_publications_track_version"),
        sa.UniqueConstraint("track_version_id", name="uq_publications_track_version_id"),
    )
    op.create_index("ix_publications_track_status", "publications", ["track_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_publications_track_status", table_name="publications")
    op.drop_table("publications")
