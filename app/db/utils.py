"""Shared datetime helpers for DB repositories and services."""

from __future__ import annotations

from datetime import datetime, timezone


def _utcnow() -> datetime:
    """현재 UTC 시각을 반환한다."""
    return datetime.now(timezone.utc)


def _iso(value: datetime | None) -> str | None:
    """datetime을 ISO 8601 문자열로 변환한다. None이면 None을 반환한다."""
    return value.isoformat() if value else None
