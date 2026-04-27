"""runtime storage parity columns

Revision ID: 20260426_0002
Revises: 20260425_0001
Create Date: 2026-04-26
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260426_0002"
down_revision = "20260425_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "mission_sessions",
        sa.Column("max_submissions", sa.Integer(), nullable=False, server_default="3"),
    )
    op.add_column("mission_sessions", sa.Column("coupon_code", sa.String(length=32)))
    op.alter_column("mission_sessions", "max_submissions", server_default=None)

    op.create_table(
        "mission_submissions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("mission_session_id", sa.String(), nullable=False),
        sa.Column("image_hash", sa.String(length=128), nullable=False),
        sa.Column("result_summary", sa.JSON(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["mission_session_id"], ["mission_sessions.id"]),
    )
    op.create_index(
        "ix_mission_submission_session_hash",
        "mission_submissions",
        ["mission_session_id", "image_hash"],
    )

    op.add_column(
        "coupons",
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "coupons",
        sa.Column(
            "mission_type", sa.String(length=40), nullable=False, server_default=""
        ),
    )
    op.add_column(
        "coupons",
        sa.Column("answer", sa.String(length=160), nullable=False, server_default=""),
    )
    op.add_column("coupons", sa.Column("partner_id", sa.String(length=120)))
    op.alter_column("coupons", "description", server_default=None)
    op.alter_column("coupons", "mission_type", server_default=None)
    op.alter_column("coupons", "answer", server_default=None)
    op.create_unique_constraint(
        "uq_coupon_mission_session", "coupons", ["mission_session_id"]
    )
    op.create_index(
        "uq_coupon_user_answer_active",
        "coupons",
        ["user_id", "answer"],
        unique=True,
        postgresql_where=sa.text("status in ('issued', 'redeemed')"),
        sqlite_where=sa.text("status in ('issued', 'redeemed')"),
    )


def downgrade() -> None:
    op.drop_index("uq_coupon_user_answer_active", table_name="coupons")
    op.drop_constraint("uq_coupon_mission_session", "coupons", type_="unique")
    op.drop_column("coupons", "partner_id")
    op.drop_column("coupons", "answer")
    op.drop_column("coupons", "mission_type")
    op.drop_column("coupons", "description")
    op.drop_index(
        "ix_mission_submission_session_hash", table_name="mission_submissions"
    )
    op.drop_table("mission_submissions")
    op.drop_column("mission_sessions", "coupon_code")
    op.drop_column("mission_sessions", "max_submissions")
