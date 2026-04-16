"""Phase 6 리팩터 검증: metadata/validator.py 타입 힌트·예외 처리 테스트.

리팩터 목적:
  - validate_metadata(image_path: str) -> bool 시그니처 추가
  - print() → logger.*로 교체
  - 예외 발생 시 False 반환 보장
검증 기준:
  - 반환값이 항상 bool 타입
  - 예외 상황에서 False 반환 (크래시 없음)
  - quick_photo_summary가 None/False/True를 반환하는 각 케이스 처리
"""

from __future__ import annotations

from unittest.mock import patch


class TestValidateMetadataReturnType:
    """validate_metadata의 반환 타입이 항상 bool이어야 한다."""

    def test_returns_bool_when_summary_true(self) -> None:
        from app.metadata.validator import validate_metadata

        with patch("app.metadata.validator.quick_photo_summary", return_value=True):
            result = validate_metadata("/some/image.jpg")
        assert isinstance(result, bool)
        assert result is True

    def test_returns_bool_when_summary_false(self) -> None:
        from app.metadata.validator import validate_metadata

        with patch("app.metadata.validator.quick_photo_summary", return_value=False):
            result = validate_metadata("/some/image.jpg")
        assert isinstance(result, bool)
        assert result is False

    def test_returns_false_when_summary_none(self) -> None:
        """quick_photo_summary가 None이면 False로 처리."""
        from app.metadata.validator import validate_metadata

        with patch("app.metadata.validator.quick_photo_summary", return_value=None):
            result = validate_metadata("/some/image.jpg")
        assert result is False

    def test_returns_false_on_exception(self) -> None:
        """quick_photo_summary가 예외를 던져도 False를 반환해야 한다."""
        from app.metadata.validator import validate_metadata

        with patch(
            "app.metadata.validator.quick_photo_summary",
            side_effect=RuntimeError("EXIF read error"),
        ):
            result = validate_metadata("/broken/image.jpg")
        assert result is False
        assert isinstance(result, bool)

    def test_returns_false_on_file_not_found(self) -> None:
        """FileNotFoundError에도 False를 반환해야 한다."""
        from app.metadata.validator import validate_metadata

        with patch(
            "app.metadata.validator.quick_photo_summary",
            side_effect=FileNotFoundError("no such file"),
        ):
            result = validate_metadata("/nonexistent.jpg")
        assert result is False

    def test_empty_path_still_calls_summary(self) -> None:
        """빈 경로도 validate_metadata가 호출 시도해야 한다."""
        from app.metadata.validator import validate_metadata

        with patch(
            "app.metadata.validator.quick_photo_summary", return_value=False
        ) as mock_summary:
            validate_metadata("")
        mock_summary.assert_called_once_with("")

    def test_passes_image_path_to_summary(self) -> None:
        """image_path를 quick_photo_summary에 그대로 전달해야 한다."""
        from app.metadata.validator import validate_metadata

        path = "/test/photo.jpg"
        with patch(
            "app.metadata.validator.quick_photo_summary", return_value=True
        ) as mock_summary:
            validate_metadata(path)
        mock_summary.assert_called_once_with(path)


class TestValidateMetadataLogging:
    """validate_metadata가 print() 대신 logger를 사용하는지 확인."""

    def test_no_print_called_on_success(self, capsys) -> None:
        """성공 시 stdout/stderr에 출력하지 않아야 한다."""
        from app.metadata.validator import validate_metadata

        with patch("app.metadata.validator.quick_photo_summary", return_value=True):
            validate_metadata("/ok.jpg")
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""

    def test_no_print_called_on_failure(self, capsys) -> None:
        """실패 시에도 stdout/stderr에 출력하지 않아야 한다."""
        from app.metadata.validator import validate_metadata

        with patch("app.metadata.validator.quick_photo_summary", return_value=False):
            validate_metadata("/bad.jpg")
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""

    def test_no_print_called_on_exception(self, capsys) -> None:
        """예외 발생 시에도 print()를 사용하지 않아야 한다."""
        from app.metadata.validator import validate_metadata

        with patch(
            "app.metadata.validator.quick_photo_summary",
            side_effect=ValueError("oops"),
        ):
            validate_metadata("/err.jpg")
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""
