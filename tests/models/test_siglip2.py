"""app.models.siglip2 단위 테스트.

검증 대상:
  - probe_with_siglip2: 모델 로드 실패·이미지 로드 실패·추론 실패·성공·실패
  - 후보 텍스트: siglip2_candidates 제공 / location·atmosphere 폴백
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import app.models.siglip2 as siglip2_module


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────


def _make_inference_mocks(score_val: float = 0.9) -> tuple:
    """추론 성공 경로용 mock 세트를 반환한다.

    Returns:
        (mock_proc, mock_tok, mock_model, mock_image, mock_probs)
    """
    # _image_processor / _tokenizer — 체인 호출 결과만 mock
    mock_proc = MagicMock()
    mock_tok = MagicMock()

    # probs[0][0].cpu().numpy() → score_val
    mock_node = MagicMock()
    mock_node.cpu.return_value.numpy.return_value = score_val
    mock_probs = [[mock_node]]  # 실제 중첩 리스트로 구성

    mock_model = MagicMock()
    mock_image = MagicMock()
    mock_image.convert.return_value = mock_image

    return mock_proc, mock_tok, mock_model, mock_image, mock_probs


# ── probe_with_siglip2 ────────────────────────────────────────────────────────


class TestProbeWithSiglip2:
    def test_returns_mismatch_on_model_load_failure(self) -> None:
        """모델 로드 실패 시 score=0.0, label='mismatch'를 반환한다."""
        with patch.object(
            siglip2_module, "_load_siglip2", side_effect=RuntimeError("oom")
        ):
            result = siglip2_module.probe_with_siglip2(
                "location", "/img.jpg", "활돌이", {}
            )
        assert result["model"] == "siglip2"
        assert result["score"] == 0.0
        assert result["label"] == "mismatch"
        assert "oom" in result["reason"]

    def test_returns_mismatch_on_image_load_failure(self) -> None:
        """이미지 로드 실패 시 score=0.0, label='mismatch'를 반환한다."""
        with (
            patch.object(siglip2_module, "_load_siglip2"),
            patch.object(siglip2_module, "_model", MagicMock()),
            patch.object(siglip2_module, "_image_processor", MagicMock()),
            patch.object(siglip2_module, "_tokenizer", MagicMock()),
            patch(
                "app.models.siglip2.Image.open",
                side_effect=OSError("no file"),
            ),
        ):
            result = siglip2_module.probe_with_siglip2(
                "location", "/missing.jpg", "활돌이", {}
            )
        assert result["score"] == 0.0
        assert result["label"] == "mismatch"
        assert "Image load failed" in result["reason"]

    def test_returns_mismatch_on_inference_failure(self) -> None:
        """추론 중 예외 발생 시 score=0.0, label='mismatch'를 반환한다."""
        mock_image = MagicMock()
        mock_image.convert.return_value = mock_image
        # _image_processor 호출 자체가 RuntimeError를 발생시켜 추론 블록을 실패시킴
        mock_proc = MagicMock(side_effect=RuntimeError("cuda error"))

        with (
            patch.object(siglip2_module, "_load_siglip2"),
            patch.object(siglip2_module, "_image_processor", mock_proc),
            patch.object(siglip2_module, "_tokenizer", MagicMock()),
            patch.object(siglip2_module, "_model", MagicMock()),
            patch("app.models.siglip2.Image.open", return_value=mock_image),
        ):
            result = siglip2_module.probe_with_siglip2(
                "location", "/img.jpg", "활돌이", {}
            )
        assert result["score"] == 0.0
        assert result["label"] == "mismatch"
        assert "Inference failed" in result["reason"]

    def test_fallback_candidate_location(self) -> None:
        """candidates 없고 location 타입이면 'a photo of {answer}' 텍스트를 사용한다."""
        mock_proc, mock_tok, mock_model, mock_image, mock_probs = _make_inference_mocks(
            0.9
        )
        with (
            patch.object(siglip2_module, "_load_siglip2"),
            patch.object(siglip2_module, "_image_processor", mock_proc),
            patch.object(siglip2_module, "_tokenizer", mock_tok),
            patch.object(siglip2_module, "_model", mock_model),
            patch("app.models.siglip2.Image.open", return_value=mock_image),
            patch("app.models.siglip2.torch.sigmoid", return_value=mock_probs),
            patch("app.models.siglip2.torch.no_grad"),
        ):
            result = siglip2_module.probe_with_siglip2(
                "location", "/img.jpg", "활돌이", {}
            )
        assert "a photo of 활돌이" in result["reason"]

    def test_fallback_candidate_atmosphere(self) -> None:
        """candidates 없고 atmosphere 타입이면 'a photo with {answer} atmosphere' 폼을 사용한다."""
        mock_proc, mock_tok, mock_model, mock_image, mock_probs = _make_inference_mocks(
            0.3
        )
        with (
            patch.object(siglip2_module, "_load_siglip2"),
            patch.object(siglip2_module, "_image_processor", mock_proc),
            patch.object(siglip2_module, "_tokenizer", mock_tok),
            patch.object(siglip2_module, "_model", mock_model),
            patch("app.models.siglip2.Image.open", return_value=mock_image),
            patch("app.models.siglip2.torch.sigmoid", return_value=mock_probs),
            patch("app.models.siglip2.torch.no_grad"),
        ):
            result = siglip2_module.probe_with_siglip2(
                "atmosphere", "/img.jpg", "화사한", {}
            )
        assert "a photo with 화사한 atmosphere" in result["reason"]

    def test_uses_provided_candidates_first(self) -> None:
        """prompt_bundle의 siglip2_candidates 첫 번째 항목을 target_text로 사용한다."""
        mock_proc, mock_tok, mock_model, mock_image, mock_probs = _make_inference_mocks(
            0.9
        )
        bundle = {"siglip2_candidates": ["pink sausage mascot"]}
        with (
            patch.object(siglip2_module, "_load_siglip2"),
            patch.object(siglip2_module, "_image_processor", mock_proc),
            patch.object(siglip2_module, "_tokenizer", mock_tok),
            patch.object(siglip2_module, "_model", mock_model),
            patch("app.models.siglip2.Image.open", return_value=mock_image),
            patch("app.models.siglip2.torch.sigmoid", return_value=mock_probs),
            patch("app.models.siglip2.torch.no_grad"),
        ):
            result = siglip2_module.probe_with_siglip2(
                "location", "/img.jpg", "활돌이", bundle
            )
        assert "pink sausage mascot" in result["reason"]

    def test_success_label_match_above_threshold(self) -> None:
        """점수가 threshold 이상이면 label='match'를 반환한다."""
        mock_proc, mock_tok, mock_model, mock_image, mock_probs = _make_inference_mocks(
            0.95
        )
        mock_settings = MagicMock()
        mock_settings.LOCATION_PASS_THRESHOLD = 0.5
        mock_settings.ATMOSPHERE_PASS_THRESHOLD = 0.5

        with (
            patch.object(siglip2_module, "_load_siglip2"),
            patch.object(siglip2_module, "_image_processor", mock_proc),
            patch.object(siglip2_module, "_tokenizer", mock_tok),
            patch.object(siglip2_module, "_model", mock_model),
            patch("app.models.siglip2.Image.open", return_value=mock_image),
            patch("app.models.siglip2.torch.sigmoid", return_value=mock_probs),
            patch("app.models.siglip2.torch.no_grad"),
            patch.object(siglip2_module, "settings", mock_settings),
        ):
            result = siglip2_module.probe_with_siglip2(
                "location", "/img.jpg", "활돌이", {}
            )
        assert result["model"] == "siglip2"
        assert result["score"] == pytest.approx(0.95)
        assert result["label"] == "match"

    def test_success_label_mismatch_below_threshold(self) -> None:
        """점수가 threshold 미만이면 label='mismatch'를 반환한다."""
        mock_proc, mock_tok, mock_model, mock_image, mock_probs = _make_inference_mocks(
            0.1
        )
        mock_settings = MagicMock()
        mock_settings.LOCATION_PASS_THRESHOLD = 0.5
        mock_settings.ATMOSPHERE_PASS_THRESHOLD = 0.5

        with (
            patch.object(siglip2_module, "_load_siglip2"),
            patch.object(siglip2_module, "_image_processor", mock_proc),
            patch.object(siglip2_module, "_tokenizer", mock_tok),
            patch.object(siglip2_module, "_model", mock_model),
            patch("app.models.siglip2.Image.open", return_value=mock_image),
            patch("app.models.siglip2.torch.sigmoid", return_value=mock_probs),
            patch("app.models.siglip2.torch.no_grad"),
            patch.object(siglip2_module, "settings", mock_settings),
        ):
            result = siglip2_module.probe_with_siglip2(
                "location", "/img.jpg", "활돌이", {}
            )
        assert result["label"] == "mismatch"
        assert result["score"] == pytest.approx(0.1)
