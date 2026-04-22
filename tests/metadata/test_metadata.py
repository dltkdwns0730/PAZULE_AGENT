"""app.metadata.metadata 단위 테스트.

검증 대상:
  - extract_gps_coordinates: GPS 있음/없음/예외
  - is_in_bbox: BBox 내부/외부 경계값
  - quick_photo_summary: 오늘+내부(True) / GPS없음(False) / 예외(False)
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch


from app.metadata.metadata import (
    MAX_LAT,
    MAX_LON,
    MIN_LAT,
    MIN_LON,
    extract_gps_coordinates,
    is_in_bbox,
    quick_photo_summary,
)


# ── is_in_bbox ────────────────────────────────────────────────────────────────


class TestIsInBbox:
    def test_center_inside(self) -> None:
        lat = (MIN_LAT + MAX_LAT) / 2
        lon = (MIN_LON + MAX_LON) / 2
        assert is_in_bbox(lat, lon) is True

    def test_min_boundary_inside(self) -> None:
        assert is_in_bbox(MIN_LAT, MIN_LON) is True

    def test_max_boundary_inside(self) -> None:
        assert is_in_bbox(MAX_LAT, MAX_LON) is True

    def test_lat_too_low(self) -> None:
        assert is_in_bbox(MIN_LAT - 0.001, MIN_LON) is False

    def test_lat_too_high(self) -> None:
        assert is_in_bbox(MAX_LAT + 0.001, MIN_LON) is False

    def test_lon_too_low(self) -> None:
        assert is_in_bbox(MIN_LAT, MIN_LON - 0.001) is False

    def test_lon_too_high(self) -> None:
        assert is_in_bbox(MIN_LAT, MAX_LON + 0.001) is False

    def test_far_outside(self) -> None:
        # 서울 중심부
        assert is_in_bbox(37.5665, 126.9780) is False


# ── extract_gps_coordinates ───────────────────────────────────────────────────


class _MockExif:
    """PIL EXIF 모킹용 헬퍼."""

    def __init__(self, gps_ifd=None):
        self._gps = gps_ifd

    def get_ifd(self, tag):
        if tag == 0x8825:
            return self._gps
        return {}

    def __bool__(self):
        return True


class TestExtractGpsCoordinates:
    def _make_img_mock(self, gps_ifd=None, has_exif=True):
        img = MagicMock()
        if has_exif:
            img.getexif.return_value = _MockExif(gps_ifd)
        else:
            img.getexif.return_value = None
        return img

    def test_no_exif_returns_none(self) -> None:
        img = self._make_img_mock(has_exif=False)
        with patch("app.metadata.metadata.Image.open", return_value=img):
            result = extract_gps_coordinates("/fake.jpg")
        assert result is None

    def test_empty_gps_ifd_returns_none(self) -> None:
        img = self._make_img_mock(gps_ifd=None)
        # gps_ifd=None → get_ifd returns None → falsy → return None
        with patch("app.metadata.metadata.Image.open", return_value=img):
            result = extract_gps_coordinates("/fake.jpg")
        assert result is None

    def test_valid_gps_returns_coordinates(self) -> None:
        gps_ifd = {
            1: "N",  # GPSLatitudeRef
            2: (37.0, 42.0, 12.0),  # GPSLatitude (DMS)
            3: "E",  # GPSLongitudeRef
            4: (126.0, 41.0, 0.0),  # GPSLongitude (DMS)
        }
        img = self._make_img_mock(gps_ifd=gps_ifd)
        with patch("app.metadata.metadata.Image.open", return_value=img):
            result = extract_gps_coordinates("/fake.jpg")
        assert result is not None
        lat, lon = result
        assert abs(lat - (37.0 + 42.0 / 60 + 12.0 / 3600)) < 1e-6
        assert abs(lon - (126.0 + 41.0 / 60 + 0.0 / 3600)) < 1e-6

    def test_south_hemisphere_negative_latitude(self) -> None:
        gps_ifd = {
            1: "S",
            2: (10.0, 0.0, 0.0),
            3: "E",
            4: (20.0, 0.0, 0.0),
        }
        img = self._make_img_mock(gps_ifd=gps_ifd)
        with patch("app.metadata.metadata.Image.open", return_value=img):
            result = extract_gps_coordinates("/fake.jpg")
        assert result is not None
        lat, _ = result
        assert lat < 0

    def test_west_hemisphere_negative_longitude(self) -> None:
        gps_ifd = {
            1: "N",
            2: (10.0, 0.0, 0.0),
            3: "W",
            4: (20.0, 0.0, 0.0),
        }
        img = self._make_img_mock(gps_ifd=gps_ifd)
        with patch("app.metadata.metadata.Image.open", return_value=img):
            result = extract_gps_coordinates("/fake.jpg")
        assert result is not None
        _, lon = result
        assert lon < 0

    def test_exception_returns_none(self) -> None:
        with patch(
            "app.metadata.metadata.Image.open", side_effect=Exception("IO Error")
        ):
            result = extract_gps_coordinates("/bad.jpg")
        assert result is None


# ── quick_photo_summary ───────────────────────────────────────────────────────


class TestQuickPhotoSummary:
    def _inside_coords(self):
        return ((MIN_LAT + MAX_LAT) / 2, (MIN_LON + MAX_LON) / 2)

    def test_today_and_inside_returns_true(self) -> None:
        today_str = datetime.now().strftime("%Y:%m:%d")
        inside = self._inside_coords()

        class FakeExif(dict):
            def items(self):
                return [(306, f"{today_str} 12:00:00")]  # tag 306 = DateTime

            def get_ifd(self, tag):
                if tag == 0x8825:
                    return {
                        1: "N",
                        2: (inside[0], 0.0, 0.0),
                        3: "E",
                        4: (inside[1], 0.0, 0.0),
                    }
                return {}

            def __bool__(self):
                return True

        img = MagicMock()
        img.getexif.return_value = FakeExif()

        with patch("app.metadata.metadata.Image.open", return_value=img):
            result = quick_photo_summary("/fake.jpg")

        assert result is True

    def test_no_gps_returns_false(self) -> None:
        class EmptyGpsExif:
            def items(self):
                return []

            def get_ifd(self, tag):
                return {}

            def __bool__(self):
                return True

        img = MagicMock()
        img.getexif.return_value = EmptyGpsExif()

        with patch("app.metadata.metadata.Image.open", return_value=img):
            result = quick_photo_summary("/fake.jpg")

        assert result is False

    def test_exception_returns_false(self) -> None:
        with patch(
            "app.metadata.metadata.Image.open", side_effect=Exception("IO Error")
        ):
            result = quick_photo_summary("/bad.jpg")
        assert result is False

    def test_no_exif_returns_false(self) -> None:
        img = MagicMock()
        img.getexif.return_value = None

        with patch("app.metadata.metadata.Image.open", return_value=img):
            result = quick_photo_summary("/fake.jpg")

        assert result is False
