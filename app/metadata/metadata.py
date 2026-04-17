"""사진 메타데이터(EXIF) 추출 및 위치·날짜 검증 모듈."""

from __future__ import annotations

import logging
import os
from datetime import datetime

from PIL import Image
from pillow_heif import register_heif_opener

logger = logging.getLogger(__name__)

# HEIC 포맷 지원 등록
register_heif_opener()

# 파주출판단지 BBox 경계 (위도/경도)
MIN_LAT = 37.704316
MAX_LAT = 37.719660
MIN_LON = 126.683397
MAX_LON = 126.690022


def extract_gps_coordinates(file_path: str) -> tuple[float, float] | None:
    """HEIC/JPEG 파일에서 GPS 좌표를 추출한다.

    Args:
        file_path: 이미지 파일 경로.

    Returns:
        (latitude, longitude) 튜플 또는 좌표가 없으면 None.
    """
    try:
        img = Image.open(file_path)
        exif = img.getexif()
        if not exif:
            return None

        gps_info = exif.get_ifd(0x8825)  # GPS IFD
        if not gps_info:
            return None

        def convert_to_degrees(value: tuple[float, float, float]) -> float:
            """DMS(도/분/초)를 십진수 좌표로 변환한다.

            Args:
                value: (도, 분, 초) 튜플.

            Returns:
                십진수 좌표값.
            """
            d, m, s = value
            return d + (m / 60.0) + (s / 3600.0)

        lat = gps_info.get(2)  # GPSLatitude
        lat_ref = gps_info.get(1)  # GPSLatitudeRef
        lon = gps_info.get(4)  # GPSLongitude
        lon_ref = gps_info.get(3)  # GPSLongitudeRef

        if lat and lon:
            latitude = convert_to_degrees(lat)
            if lat_ref == "S":
                latitude = -latitude

            longitude = convert_to_degrees(lon)
            if lon_ref == "W":
                longitude = -longitude

            return (latitude, longitude)

        return None
    except Exception as exc:
        logger.error("GPS 추출 오류: %s", exc)
        return None


def is_in_bbox(lat: float, lon: float) -> bool:
    """주어진 좌표가 파주출판단지 BBox 내부에 있는지 확인한다.

    Args:
        lat: 위도.
        lon: 경도.

    Returns:
        BBox 내부이면 True.
    """
    return (MIN_LAT <= lat <= MAX_LAT) and (MIN_LON <= lon <= MAX_LON)


def quick_photo_summary(file_path: str) -> bool:
    """사진의 촬영 시각·GPS·BBox 유효성·오늘 촬영 여부를 검사한다.

    Args:
        file_path: 검사할 이미지 파일 경로.

    Returns:
        오늘 촬영 AND 출판단지 내부일 때 True.
    """
    try:
        img = Image.open(file_path)
        exif = img.getexif()

        date_str: str | None = None
        if exif:
            from PIL.ExifTags import TAGS

            for tag_id, value in exif.items():
                tag_name = TAGS.get(tag_id, tag_id)
                if tag_name in ("DateTimeOriginal", "DateTime"):
                    date_str = value
                    break

        coords = extract_gps_coordinates(file_path)
        if not coords:
            logger.warning("GPS 정보 없음 (좌표 없음): %s", os.path.basename(file_path))
            return False

        lat, lon = coords
        inside = is_in_bbox(lat, lon)

        today_str = datetime.now().strftime("%Y:%m:%d")
        is_today = bool(date_str and date_str.startswith(today_str))

        logger.info(
            "파일명: %s | 촬영 시각: %s | 오늘 여부: %s | 좌표: %.6f, %.6f | 위치 판정: %s",
            os.path.basename(file_path),
            date_str or "(정보 없음)",
            "오늘 촬영" if is_today else "오늘 아님",
            lat,
            lon,
            "출판단지 내부" if inside else "출판단지 외부",
        )

        passed = is_today and inside
        if passed:
            logger.info("메타데이터 조건 통과: %s", file_path)

        return passed
    except Exception as exc:
        logger.error("처리 중 오류: %s", exc)
        return False
