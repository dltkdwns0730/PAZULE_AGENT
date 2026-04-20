"""app.models.blip 단위 테스트.

검증 대상:
  - load_landmark_qa: 기본 파일·폴백·JSON 오류·파일 없음
  - check_with_blip: 모델 미로드·QA 없음·이미지 오류·성공·실패
  - get_visual_context: 이미지 오류·성공 경로
  - probe_with_blip_location / probe_with_blip_atmosphere: 래퍼 결과 구조
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch


import app.models.blip as blip_module


# ── load_landmark_qa ──────────────────────────────────────────────────────────


class TestLoadLandmarkQa:
    def test_loads_primary_file(self, tmp_path: object) -> None:
        """기본 파일이 있으면 해당 데이터를 반환한다."""
        data = {"landmark": [["Q?", "yes"]]}
        primary = tmp_path / "labeled.json"
        primary.write_text(json.dumps(data), encoding="utf-8")
        with patch.object(blip_module, "LANDMARK_QA_FILE", str(primary)):
            result = blip_module.load_landmark_qa()
        assert result == data

    def test_fallback_when_primary_missing(self, tmp_path: object) -> None:
        """기본 파일이 없으면 폴백 파일을 사용한다."""
        fallback_data = {"fallback_landmark": [["Q?", "no"]]}
        fallback = tmp_path / "landmark_qa.json"
        fallback.write_text(json.dumps(fallback_data), encoding="utf-8")
        with (
            patch.object(
                blip_module, "LANDMARK_QA_FILE", str(tmp_path / "missing.json")
            ),
            patch.object(blip_module, "DATA_DIR", str(tmp_path)),
        ):
            result = blip_module.load_landmark_qa()
        assert result == fallback_data

    def test_returns_empty_when_both_missing(self, tmp_path: object) -> None:
        """기본·폴백 모두 없으면 빈 딕셔너리를 반환한다."""
        with (
            patch.object(blip_module, "LANDMARK_QA_FILE", str(tmp_path / "no.json")),
            patch.object(blip_module, "DATA_DIR", str(tmp_path)),
        ):
            result = blip_module.load_landmark_qa()
        assert result == {}

    def test_returns_empty_on_json_decode_error(self, tmp_path: object) -> None:
        """JSON 파싱 오류 시 빈 딕셔너리를 반환한다."""
        bad = tmp_path / "bad.json"
        bad.write_text("not valid json", encoding="utf-8")
        with patch.object(blip_module, "LANDMARK_QA_FILE", str(bad)):
            result = blip_module.load_landmark_qa()
        assert result == {}

    def test_fallback_exception_returns_empty(self, tmp_path: object) -> None:
        """폴백 파일이 있지만 읽기 오류 시 빈 딕셔너리를 반환한다."""
        fallback = tmp_path / "landmark_qa.json"
        fallback.write_text("{invalid}", encoding="utf-8")
        with (
            patch.object(blip_module, "LANDMARK_QA_FILE", str(tmp_path / "no.json")),
            patch.object(blip_module, "DATA_DIR", str(tmp_path)),
        ):
            result = blip_module.load_landmark_qa()
        assert result == {}


# ── check_with_blip ───────────────────────────────────────────────────────────


class TestCheckWithBlip:
    def _patch_loaded_model(self) -> tuple:
        """프로세서·모델이 로드된 상태를 시뮬레이션하는 mock 튜플."""
        mock_proc = MagicMock()
        mock_proc.return_value.pixel_values.to.return_value = MagicMock()
        mock_proc.return_value.input_ids = MagicMock()
        mock_proc.return_value.attention_mask = MagicMock()
        token_output = MagicMock()
        mock_proc.decode.return_value = "yes"
        mock_model = MagicMock()
        mock_model.generate.return_value = [token_output]
        return mock_proc, mock_model

    def test_returns_false_when_no_qa_data(self) -> None:
        """정답 랜드마크에 Q&A 데이터가 없으면 (False, [])를 반환한다."""
        with (
            patch.object(blip_module, "_load_blip"),
            patch.object(blip_module, "_processor", MagicMock()),
            patch.object(blip_module, "_model", MagicMock()),
            patch.object(blip_module, "landmark_qa_data", {}),
        ):
            result, hint = blip_module.check_with_blip("/img.jpg", "없는장소")
        assert result is False
        assert hint == []

    def test_returns_false_when_model_not_loaded(self) -> None:
        """_load_blip이 실패해 _model이 None이면 (False, [])를 반환한다."""
        with (
            patch.object(blip_module, "_load_blip"),
            patch.object(blip_module, "_processor", None),
            patch.object(blip_module, "_model", None),
            patch.object(blip_module, "landmark_qa_data", {"활돌이": [["Q?", "yes"]]}),
        ):
            result, hint = blip_module.check_with_blip("/img.jpg", "활돌이")
        assert result is False

    def test_returns_false_on_image_file_not_found(self) -> None:
        """이미지 파일이 없으면 (False, [])를 반환한다."""
        mock_proc = MagicMock()
        mock_model = MagicMock()
        with (
            patch.object(blip_module, "_load_blip"),
            patch.object(blip_module, "_processor", mock_proc),
            patch.object(blip_module, "_model", mock_model),
            patch.object(blip_module, "landmark_qa_data", {"활돌이": [["Q?", "yes"]]}),
            patch("app.models.blip.Image.open", side_effect=FileNotFoundError),
        ):
            result, hint = blip_module.check_with_blip("/missing.jpg", "활돌이")
        assert result is False
        assert hint == []

    def test_returns_false_on_image_load_exception(self) -> None:
        """Image.open 기타 예외 시 (False, [])를 반환한다."""
        mock_proc = MagicMock()
        mock_model = MagicMock()
        with (
            patch.object(blip_module, "_load_blip"),
            patch.object(blip_module, "_processor", mock_proc),
            patch.object(blip_module, "_model", mock_model),
            patch.object(blip_module, "landmark_qa_data", {"활돌이": [["Q?", "yes"]]}),
            patch("app.models.blip.Image.open", side_effect=OSError("bad file")),
        ):
            result, hint = blip_module.check_with_blip("/bad.jpg", "활돌이")
        assert result is False

    def test_returns_false_on_preprocess_exception(self) -> None:
        """이미지 전처리 중 예외 시 (False, [])를 반환한다."""
        mock_proc = MagicMock()
        mock_proc.side_effect = RuntimeError("preprocess error")
        with (
            patch.object(blip_module, "_load_blip"),
            patch.object(blip_module, "_processor", mock_proc),
            patch.object(blip_module, "_model", MagicMock()),
            patch.object(blip_module, "landmark_qa_data", {"활돌이": [["Q?", "yes"]]}),
            patch("app.models.blip.Image.open", return_value=MagicMock()),
        ):
            result, hint = blip_module.check_with_blip("/img.jpg", "활돌이")
        assert result is False

    def test_success_all_correct(self) -> None:
        """모든 질문에 정답이면 (True, [])를 반환한다."""
        mock_proc = MagicMock()
        pixel_mock = MagicMock()
        mock_proc.return_value.pixel_values.to.return_value = pixel_mock
        mock_proc.decode.return_value = "yes"

        mock_model = MagicMock()
        mock_model.generate.return_value = [MagicMock()]

        qa_data = {"활돌이": [["Is it pink?", "yes"], ["Is it round?", "yes"]]}
        mock_image = MagicMock()
        mock_image.convert.return_value = mock_image

        with (
            patch.object(blip_module, "_load_blip"),
            patch.object(blip_module, "_processor", mock_proc),
            patch.object(blip_module, "_model", mock_model),
            patch.object(blip_module, "landmark_qa_data", qa_data),
            patch("app.models.blip.Image.open", return_value=mock_image),
        ):
            result, hint = blip_module.check_with_blip("/img.jpg", "활돌이")
        assert result is True
        assert hint == []

    def test_failure_below_threshold(self) -> None:
        """정답률이 SUCCESS_THRESHOLD 미만이면 (False, incorrect_list)를 반환한다."""
        mock_proc = MagicMock()
        pixel_mock = MagicMock()
        mock_proc.return_value.pixel_values.to.return_value = pixel_mock
        mock_proc.decode.return_value = "no"  # 모든 답변이 틀림

        mock_model = MagicMock()
        mock_model.generate.return_value = [MagicMock()]

        qa_data = {"활돌이": [["Is it pink?", "yes"]]}  # expected: "yes", got: "no"
        mock_image = MagicMock()
        mock_image.convert.return_value = mock_image

        with (
            patch.object(blip_module, "_load_blip"),
            patch.object(blip_module, "_processor", mock_proc),
            patch.object(blip_module, "_model", mock_model),
            patch.object(blip_module, "landmark_qa_data", qa_data),
            patch("app.models.blip.Image.open", return_value=mock_image),
        ):
            result, hint = blip_module.check_with_blip("/img.jpg", "활돌이")
        assert result is False
        assert len(hint) == 1
        assert hint[0]["expected_answer"] == "yes"


# ── get_visual_context ────────────────────────────────────────────────────────


class TestGetVisualContext:
    def test_returns_error_string_on_image_failure(self) -> None:
        """이미지 로드 실패 시 에러 메시지 문자열을 반환한다."""
        with (
            patch.object(blip_module, "_load_blip"),
            patch("app.models.blip.Image.open", side_effect=OSError("fail")),
        ):
            result = blip_module.get_visual_context("/bad.jpg")
        assert "이미지 로드 오류" in result

    def test_returns_context_string_on_success(self) -> None:
        """정상 실행 시 컨텍스트 문자열을 반환한다."""
        mock_proc = MagicMock()
        pixel_mock = MagicMock()
        mock_proc.return_value.pixel_values.to.return_value = pixel_mock
        mock_proc.decode.return_value = "bright"

        mock_model = MagicMock()
        mock_model.generate.return_value = [MagicMock()]

        mock_image = MagicMock()
        mock_image.convert.return_value = mock_image

        with (
            patch.object(blip_module, "_load_blip"),
            patch.object(blip_module, "_processor", mock_proc),
            patch.object(blip_module, "_model", mock_model),
            patch("app.models.blip.Image.open", return_value=mock_image),
        ):
            result = blip_module.get_visual_context("/img.jpg")
        assert isinstance(result, str)
        assert len(result) > 0


# ── probe_with_blip_location / probe_with_blip_atmosphere ─────────────────────


class TestProbeWithBlip:
    def test_location_probe_success_structure(self) -> None:
        """위치 프로브 성공 시 표준 투표 딕셔너리를 반환한다."""
        with patch.object(blip_module, "check_with_blip", return_value=(True, [])):
            result = blip_module.probe_with_blip_location("/img.jpg", "활돌이", {})
        assert result["model"] == "blip"
        assert result["score"] == 1.0
        assert result["label"] == "match"

    def test_location_probe_failure_structure(self) -> None:
        """위치 프로브 실패 시 score=0.0, label='mismatch'를 반환한다."""
        with patch.object(
            blip_module, "check_with_blip", return_value=(False, [{"q": "x"}])
        ):
            result = blip_module.probe_with_blip_location("/img.jpg", "활돌이", {})
        assert result["score"] == 0.0
        assert result["label"] == "mismatch"

    def test_atmosphere_probe_keyword_found(self) -> None:
        """컨텍스트에 키워드가 있으면 score=0.85를 반환한다."""
        with patch.object(
            blip_module, "get_visual_context", return_value="화사한 분위기"
        ):
            result = blip_module.probe_with_blip_atmosphere("/img.jpg", "화사한", {})
        assert result["model"] == "blip"
        assert result["score"] == 0.85
        assert result["label"] == "match"

    def test_atmosphere_probe_keyword_not_found(self) -> None:
        """컨텍스트에 키워드가 없으면 score=0.2를 반환한다."""
        with patch.object(
            blip_module, "get_visual_context", return_value="dark and gloomy"
        ):
            result = blip_module.probe_with_blip_atmosphere("/img.jpg", "화사한", {})
        assert result["score"] == 0.2
        assert result["label"] == "mismatch"
