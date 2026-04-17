"""이미지 EXIF 메타데이터 유효성 검증 모듈."""

from __future__ import annotations

import logging

from app.metadata.metadata import quick_photo_summary

logger = logging.getLogger(__name__)


def validate_metadata(image_path: str) -> bool:
    """사진 메타데이터 유효성 검사를 실행한다.

    촬영일이 오늘인지, 파주출판단지 BBox 내부인지 확인하여
    둘 다 만족해야 True를 반환한다.

    Args:
        image_path: 검증할 이미지 파일의 절대 경로.

    Returns:
        촬영일·위치 조건을 모두 만족하면 True, 그렇지 않으면 False.
    """
    logger.debug("[metadata] 메타데이터 검증 중: %s", image_path)
    try:
        result = bool(quick_photo_summary(image_path))
        if not result:
            logger.warning("[metadata] 검증 실패 (오늘 촬영 or 위치 조건 불만족)")
        return result
    except Exception as exc:
        logger.error("[metadata] 검증 예외 발생: %s", exc)
        return False
