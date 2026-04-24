"""SQLAlchemy ORM models for the B2B platform data model."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

try:
    from sqlalchemy import (
        Boolean,
        DateTime,
        Float,
        ForeignKey,
        JSON,
        String,
        Text,
        UniqueConstraint,
    )
    from sqlalchemy.dialects.postgresql import UUID
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
except ModuleNotFoundError as exc:  # pragma: no cover - dependency guard
    raise RuntimeError(
        "SQLAlchemy is not installed. Run `uv sync --dev` before importing DB models."
    ) from exc


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class MemberRole(str, Enum):
    OWNER = "owner"
    MANAGER = "manager"
    VIEWER = "viewer"
    PARTNER_STAFF = "partner_staff"


class MissionType(str, Enum):
    LOCATION = "location"
    ATMOSPHERE = "atmosphere"


class MissionSessionStatus(str, Enum):
    CREATED = "created"
    SUBMITTED = "submitted"
    COUPON_ISSUED = "coupon_issued"
    FAILED = "failed"
    EXPIRED = "expired"


class CouponStatus(str, Enum):
    ISSUED = "issued"
    REDEEMED = "redeemed"
    EXPIRED = "expired"


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    sites: Mapped[list["Site"]] = relationship(back_populates="organization")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    display_name: Mapped[str | None] = mapped_column(String(120))
    email: Mapped[str | None] = mapped_column(String(320), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )


class OrganizationMember(Base):
    __tablename__ = "organization_members"
    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_member"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("user_profiles.id"), nullable=False)
    role: Mapped[str] = mapped_column(
        String(40), nullable=False, default=MemberRole.VIEWER.value
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    radius_meters: Mapped[int] = mapped_column(nullable=False, default=300)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    organization: Mapped[Organization] = relationship(back_populates="sites")


class Mission(Base):
    __tablename__ = "missions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id"), nullable=False)
    mission_type: Mapped[str] = mapped_column(String(40), nullable=False)
    answer: Mapped[str] = mapped_column(String(160), nullable=False)
    hint: Mapped[str] = mapped_column(Text, nullable=False)
    vqa_hints: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )


class MissionSession(Base):
    __tablename__ = "mission_sessions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    legacy_mission_id: Mapped[str | None] = mapped_column(String(80), unique=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("user_profiles.id"), nullable=False)
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id"), nullable=False)
    mission_type: Mapped[str] = mapped_column(String(40), nullable=False)
    answer: Mapped[str] = mapped_column(String(160), nullable=False)
    hint: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(40), nullable=False, default=MissionSessionStatus.CREATED.value
    )
    latest_judgment: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class Coupon(Base):
    __tablename__ = "coupons"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    mission_session_id: Mapped[str | None] = mapped_column(
        ForeignKey("mission_sessions.id")
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("user_profiles.id"), nullable=False)
    status: Mapped[str] = mapped_column(
        String(40), nullable=False, default=CouponStatus.ISSUED.value
    )
    discount_rule: Mapped[str] = mapped_column(String(120), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    redeemed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    partner_pos_id: Mapped[str | None] = mapped_column(String(120))


class MissionEvent(Base):
    __tablename__ = "mission_events"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    mission_session_id: Mapped[str | None] = mapped_column(
        ForeignKey("mission_sessions.id")
    )
    user_id: Mapped[str | None] = mapped_column(ForeignKey("user_profiles.id"))
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )


class LeadSubmission(Base):
    __tablename__ = "lead_submissions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    organization_name: Mapped[str] = mapped_column(String(160), nullable=False)
    contact_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
