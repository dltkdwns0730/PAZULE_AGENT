"""app.models.qwen_vl 단위 테스트.

검증 대상:
  - _encode_image_base64: 성공·파일 없음
  - probe_with_qwen: API 키 없음·성공·커스텀 프롬프트·JSON 파싱 오류·일반 예외
"""

from __future__ import annotations

import base64
import json
from unittest.mock import MagicMock, patch

import pytest

import app.models.qwen_vl as qwen_module


# ── _encode_image_base64 ──────────────────────────────────────────────────────


class TestEncodeImageBase64:
    def test_encodes_file_contents(self, tmp_path: object) -> None:
        """파일 내용을 Base64 인코딩 문자열로 올바르게 반환한다."""
        img_file = tmp_path / "test.jpg"
        img_file.write_bytes(b"fake image data")
        result = qwen_module._encode_image_base64(str(img_file))
        expected = base64.b64encode(b"fake image data").decode("utf-8")
        assert result == expected

    def test_raises_on_missing_file(self, tmp_path: object) -> None:
        """파일이 없으면 FileNotFoundError를 발생시킨다."""
        with pytest.raises(FileNotFoundError):
            qwen_module._encode_image_base64(str(tmp_path / "missing.jpg"))


# ── probe_with_qwen ───────────────────────────────────────────────────────────


def _mock_settings(api_key: str = "fake-api-key") -> MagicMock:
    """테스트용 settings mock을 반환한다."""
    s = MagicMock()
    s.OPENROUTER_API_KEY = api_key
    s.API_TIMEOUT_SECONDS = 30
    s.API_MAX_RETRIES = 2
    s.QWEN_VL_MODEL_ID = "qwen/test-model"
    return s


class TestProbeWithQwen:
    def test_returns_fail_when_no_api_key(self) -> None:
        """OPENROUTER_API_KEY가 없으면 score=0.0, label='fail'을 반환한다."""
        with patch.object(qwen_module, "settings", _mock_settings(api_key="")):
            result = qwen_module.probe_with_qwen("location", "/img.jpg", "활돌이", {})
        assert result["model"] == "qwen"
        assert result["score"] == 0.0
        assert result["label"] == "fail"
        assert "OPENROUTER_API_KEY" in result["reason"]

    def test_success_parses_json_response(self) -> None:
        """LLM이 정상 JSON을 반환하면 score·label·reason을 올바르게 파싱한다."""
        payload = {"score": 0.85, "label": "match", "reason": "photo looks right"}
        mock_response = MagicMock()
        mock_response.content = json.dumps(payload)

        with (
            patch.object(qwen_module, "settings", _mock_settings()),
            patch("app.models.qwen_vl._encode_image_base64", return_value="b64str"),
            patch("app.models.qwen_vl.ChatOpenAI") as mock_cls,
        ):
            mock_cls.return_value.invoke.return_value = mock_response
            result = qwen_module.probe_with_qwen("location", "/img.jpg", "활돌이", {})

        assert result["model"] == "qwen"
        assert result["score"] == pytest.approx(0.85)
        assert result["label"] == "match"
        assert result["reason"] == "photo looks right"

    def test_strips_markdown_code_fence(self) -> None:
        """LLM 응답에 ```json``` 코드 펜스가 있어도 올바르게 파싱한다."""
        payload = {"score": 0.7, "label": "match", "reason": "ok"}
        fenced = f"```json\n{json.dumps(payload)}\n```"
        mock_response = MagicMock()
        mock_response.content = fenced

        with (
            patch.object(qwen_module, "settings", _mock_settings()),
            patch("app.models.qwen_vl._encode_image_base64", return_value="b64str"),
            patch("app.models.qwen_vl.ChatOpenAI") as mock_cls,
        ):
            mock_cls.return_value.invoke.return_value = mock_response
            result = qwen_module.probe_with_qwen("location", "/img.jpg", "활돌이", {})

        assert result["score"] == pytest.approx(0.7)
        assert result["label"] == "match"

    def test_uses_custom_qwen_prompt_from_bundle(self) -> None:
        """prompt_bundle에 qwen_prompt가 있으면 해당 값을 사용한다."""
        payload = {"score": 0.6, "label": "match", "reason": "yes"}
        mock_response = MagicMock()
        mock_response.content = json.dumps(payload)
        captured_calls: list = []

        def fake_invoke(messages: list) -> MagicMock:
            captured_calls.extend(messages)
            return mock_response

        with (
            patch.object(qwen_module, "settings", _mock_settings()),
            patch("app.models.qwen_vl._encode_image_base64", return_value="b64"),
            patch("app.models.qwen_vl.ChatOpenAI") as mock_cls,
        ):
            mock_cls.return_value.invoke.side_effect = fake_invoke
            qwen_module.probe_with_qwen(
                "location",
                "/img.jpg",
                "활돌이",
                {"qwen_prompt": "Is the pink character visible?"},
            )

        # system_instruction이 커스텀 프롬프트를 포함하는지 확인
        assert len(captured_calls) == 1
        content_text = captured_calls[0].content[0]["text"]
        assert "Is the pink character visible?" in content_text

    def test_returns_fail_on_json_parse_error(self) -> None:
        """LLM이 유효하지 않은 JSON을 반환하면 score=0.0, label='fail'을 반환한다."""
        mock_response = MagicMock()
        mock_response.content = "not valid json at all"

        with (
            patch.object(qwen_module, "settings", _mock_settings()),
            patch("app.models.qwen_vl._encode_image_base64", return_value="b64str"),
            patch("app.models.qwen_vl.ChatOpenAI") as mock_cls,
        ):
            mock_cls.return_value.invoke.return_value = mock_response
            result = qwen_module.probe_with_qwen("location", "/img.jpg", "활돌이", {})

        assert result["model"] == "qwen"
        assert result["score"] == 0.0
        assert result["label"] == "fail"

    def test_returns_fail_on_api_exception(self) -> None:
        """API 호출 중 예외 발생 시 score=0.0, label='fail'을 반환한다."""
        with (
            patch.object(qwen_module, "settings", _mock_settings()),
            patch(
                "app.models.qwen_vl._encode_image_base64",
                side_effect=ConnectionError("timeout"),
            ),
        ):
            result = qwen_module.probe_with_qwen("location", "/img.jpg", "활돌이", {})

        assert result["model"] == "qwen"
        assert result["score"] == 0.0
        assert result["label"] == "fail"
        assert "timeout" in result["reason"]

    def test_uses_default_fallback_values_from_llm(self) -> None:
        """LLM 응답 JSON에 누락된 키가 있으면 기본값을 사용한다."""
        # score 없음 → 0.0, label 없음 → 'mismatch', reason 없음 → 기본 메시지
        mock_response = MagicMock()
        mock_response.content = json.dumps({})  # 빈 JSON

        with (
            patch.object(qwen_module, "settings", _mock_settings()),
            patch("app.models.qwen_vl._encode_image_base64", return_value="b64str"),
            patch("app.models.qwen_vl.ChatOpenAI") as mock_cls,
        ):
            mock_cls.return_value.invoke.return_value = mock_response
            result = qwen_module.probe_with_qwen("location", "/img.jpg", "활돌이", {})

        assert result["score"] == pytest.approx(0.0)
        assert result["label"] == "mismatch"
        assert isinstance(result["reason"], str)
        assert len(result["reason"]) > 0
