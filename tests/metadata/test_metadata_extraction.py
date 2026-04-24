from unittest.mock import MagicMock, patch
from app.metadata.metadata import (
    extract_gps_coordinates,
    is_in_bbox,
    quick_photo_summary,
)


def test_is_in_bbox():
    # 파주출판단지 내부 좌표
    assert is_in_bbox(37.7115, 126.685) is True
    # 파주출판단지 외부 좌표
    assert is_in_bbox(37.5, 127.0) is False


def test_extract_gps_coordinates_missing_exif():
    with patch("PIL.Image.open") as mock_open:
        mock_img = MagicMock()
        mock_img.getexif.return_value = None
        mock_open.return_value = mock_img

        assert extract_gps_coordinates("fake.jpg") is None


def test_extract_gps_coordinates_success():
    with patch("PIL.Image.open") as mock_open:
        mock_img = MagicMock()
        mock_exif = MagicMock()
        # GPS IFD 데이터 시뮬레이션
        # 1: Ref N, 2: Lat (37, 42, 30), 3: Ref E, 4: Lon (126, 41, 0)
        mock_exif.get_ifd.return_value = {
            1: "N",
            2: (37.0, 42.0, 30.0),
            3: "E",
            4: (126.0, 41.0, 0.0),
        }
        mock_img.getexif.return_value = mock_exif
        mock_open.return_value = mock_img

        coords = extract_gps_coordinates("fake.jpg")
        assert coords == (37.708333333333336, 126.68333333333334)


def test_quick_photo_summary_success():
    with (
        patch("PIL.Image.open") as mock_open,
        patch("app.metadata.metadata.extract_gps_coordinates") as mock_gps,
    ):
        mock_img = MagicMock()
        mock_exif = {306: "2026:04:22 12:00:00"}  # DateTime Original (approx)
        mock_img.getexif.return_value = mock_exif
        mock_open.return_value = mock_img

        # 내부 좌표 모킹
        mock_gps.return_value = (37.7115, 126.685)

        # datetime.now() 모킹 필요 (is_today 체크용)
        from datetime import datetime

        with patch("app.metadata.metadata.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 4, 22)
            mock_dt.strptime = datetime.strptime

            assert quick_photo_summary("fake.jpg") is True


def test_quick_photo_summary_not_today():
    with (
        patch("PIL.Image.open") as mock_open,
        patch("app.metadata.metadata.extract_gps_coordinates") as mock_gps,
    ):
        mock_img = MagicMock()
        mock_exif = {306: "2000:01:01 12:00:00"}
        mock_img.getexif.return_value = mock_exif
        mock_open.return_value = mock_img
        mock_gps.return_value = (37.7115, 126.685)

        from datetime import datetime

        with patch("app.metadata.metadata.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 4, 22)

            assert quick_photo_summary("fake.jpg") is False
