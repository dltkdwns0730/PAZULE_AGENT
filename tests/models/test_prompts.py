"""app.models.prompts 단위 테스트.

검증 대상:
  - _to_english: location / atmosphere 분기, 매핑 없는 경우 원본 반환
  - build_prompt_bundle: location / atmosphere 반환값, None answer 기본값
"""

from __future__ import annotations


from app.models.prompts import (
    ATMOSPHERE_EN,
    LANDMARK_EN,
    _to_english,
    build_prompt_bundle,
)


# ── _to_english ───────────────────────────────────────────────────────────────


class TestToEnglish:
    def test_location_known_key(self) -> None:
        result = _to_english("활판공방 인쇄기", "location")
        assert result == LANDMARK_EN["활판공방 인쇄기"]

    def test_location_unknown_key_returns_original(self) -> None:
        result = _to_english("알수없는장소", "location")
        assert result == "알수없는장소"

    def test_atmosphere_known_key(self) -> None:
        result = _to_english("차분하고 자연적인", "atmosphere")
        assert result == ATMOSPHERE_EN["차분하고 자연적인"]

    def test_atmosphere_unknown_key_returns_original(self) -> None:
        result = _to_english("알수없는분위기", "atmosphere")
        assert result == "알수없는분위기"

    def test_atmosphere_all_keys_translate(self) -> None:
        for korean, english in ATMOSPHERE_EN.items():
            assert _to_english(korean, "atmosphere") == english

    def test_location_all_landmark_keys_translate(self) -> None:
        for korean, english in LANDMARK_EN.items():
            assert _to_english(korean, "location") == english


# ── build_prompt_bundle ───────────────────────────────────────────────────────


class TestBuildPromptBundle:
    def test_location_bundle_has_required_keys(self) -> None:
        bundle = build_prompt_bundle("location", "네모탑")
        for key in (
            "mission_type",
            "answer",
            "answer_en",
            "blip_question",
            "qwen_prompt",
            "siglip2_candidates",
        ):
            assert key in bundle

    def test_location_mission_type_stored(self) -> None:
        bundle = build_prompt_bundle("location", "네모탑")
        assert bundle["mission_type"] == "location"

    def test_location_answer_stored(self) -> None:
        bundle = build_prompt_bundle("location", "네모탑")
        assert bundle["answer"] == "네모탑"

    def test_location_blip_question_format(self) -> None:
        bundle = build_prompt_bundle("location", "네모탑")
        assert "Is this a photo of" in bundle["blip_question"]

    def test_location_siglip2_candidates_has_two(self) -> None:
        bundle = build_prompt_bundle("location", "네모탑")
        assert len(bundle["siglip2_candidates"]) == 2

    def test_atmosphere_bundle_has_required_keys(self) -> None:
        bundle = build_prompt_bundle("atmosphere", "차분한")
        for key in (
            "mission_type",
            "answer",
            "answer_en",
            "blip_question",
            "qwen_prompt",
            "siglip2_candidates",
        ):
            assert key in bundle

    def test_atmosphere_mission_type_stored(self) -> None:
        bundle = build_prompt_bundle("atmosphere", "화사한")
        assert bundle["mission_type"] == "atmosphere"

    def test_atmosphere_blip_question_format(self) -> None:
        bundle = build_prompt_bundle("atmosphere", "활기찬")
        assert "atmosphere" in bundle["blip_question"]

    def test_atmosphere_siglip2_candidates_has_two(self) -> None:
        bundle = build_prompt_bundle("atmosphere", "화사한")
        assert len(bundle["siglip2_candidates"]) == 2

    def test_none_answer_defaults_to_unknown(self) -> None:
        bundle = build_prompt_bundle("location", None)
        assert bundle["answer"] == "unknown"

    def test_empty_answer_defaults_to_unknown(self) -> None:
        bundle = build_prompt_bundle("atmosphere", "")
        assert bundle["answer"] == "unknown"

    def test_answer_en_translated_for_location(self) -> None:
        bundle = build_prompt_bundle("location", "활판공방 인쇄기")
        assert bundle["answer_en"] == LANDMARK_EN["활판공방 인쇄기"]

    def test_answer_en_translated_for_atmosphere(self) -> None:
        bundle = build_prompt_bundle("atmosphere", "차분하고 자연적인")
        assert bundle["answer_en"] == ATMOSPHERE_EN["차분하고 자연적인"]
