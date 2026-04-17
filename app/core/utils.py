"""Common utility functions for the PAZULE application."""

from __future__ import annotations


def normalize_mission_type(mission_type: str | None) -> str:
    """미션 타입을 내부 표준값으로 정규화한다.

    'photo'는 'atmosphere'로 변환하며, 지원하지 않는 값은 'location'으로 폴백한다.

    Args:
        mission_type: 클라이언트가 전달한 미션 타입 문자열.

    Returns:
        'location' 혹은 'atmosphere'.
    """
    m = (mission_type or "").strip().lower()
    if m == "photo":
        return "atmosphere"
    return m if m in {"location", "atmosphere"} else "location"


def to_legacy_mission_type(mission_type: str) -> str:
    """내부 표준값을 레거시 프론트엔드 표현('photo')으로 변환한다.

    Args:
        mission_type: 내부 표준 미션 타입 ('location' | 'atmosphere').

    Returns:
        레거시 표현 ('location' | 'photo').
    """
    return "photo" if mission_type == "atmosphere" else mission_type
