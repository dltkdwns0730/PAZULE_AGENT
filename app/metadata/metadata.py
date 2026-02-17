import os
from datetime import datetime

from PIL import Image
from pillow_heif import register_heif_opener

# HEIC 포맷 지원 등록
register_heif_opener()

# 파주출판단지 BBox 경계 (위도/경도)
MIN_LAT = 37.704316
MAX_LAT = 37.719660
MIN_LON = 126.683397
MAX_LON = 126.690022


def extract_gps_coordinates(file_path):
    """HEIC/JPEG 파일에서 GPS 좌표를 추출한다.

    Returns:
        (latitude, longitude) 튜플 또는 좌표가 없으면 None
    """
    try:
        img = Image.open(file_path)
        exif = img.getexif()
        if not exif:
            return None

        gps_info = exif.get_ifd(0x8825)  # GPS IFD
        if not gps_info:
            return None

        def convert_to_degrees(value):
            """DMS(도/분/초)를 십진수 좌표로 변환"""
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
    except Exception as e:
        print(f"GPS 추출 오류: {e}")
        return None


def is_in_bbox(lat, lon):
    """주어진 좌표가 파주출판단지 BBox 내부에 있으면 True"""
    return (MIN_LAT <= lat <= MAX_LAT) and (MIN_LON <= lon <= MAX_LON)


def quick_photo_summary(file_path):
    """사진의 촬영 시각 + GPS + BBox 유효성 + 오늘 촬영 여부를 검사한다.

    Returns:
        오늘 촬영 AND 출판단지 내부일 때 True
    """
    try:
        img = Image.open(file_path)
        exif = img.getexif()

        # 촬영 날짜 추출
        date_str = None
        if exif:
            from PIL.ExifTags import TAGS

            for tag_id, value in exif.items():
                tag_name = TAGS.get(tag_id, tag_id)
                if tag_name in ("DateTimeOriginal", "DateTime"):
                    date_str = value
                    break

        # GPS 좌표 추출
        coords = extract_gps_coordinates(file_path)
        if not coords:
            print("\n⚠️ GPS 정보 없음 (좌표 없음)")
            return False

        lat, lon = coords
        inside = is_in_bbox(lat, lon)

        # 오늘 날짜 비교
        today_str = datetime.now().strftime("%Y:%m:%d")
        is_today = date_str and date_str.startswith(today_str)

        # 결과 출력
        print("\n" + "=" * 60)
        print(f"📸 파일명: {os.path.basename(file_path)}")
        print(f"🕒 촬영 시각: {date_str if date_str else '(정보 없음)'}")
        print(f"📅 오늘 여부: {'✅ 오늘 촬영' if is_today else '❌ 오늘 아님'}")
        print(f"📍 좌표: {lat:.6f}, {lon:.6f}")
        print(f"📦 위치 판정: {'✅ 출판단지 내부' if inside else '❌ 출판단지 외부'}")
        print("=" * 60)

        passed = is_today and inside
        if passed:
            print("✅ 메타데이터 조건 통과")

        return passed
    except Exception as e:
        print(f"❌ 처리 중 오류: {e}")
        return False
