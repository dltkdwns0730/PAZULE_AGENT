"""app.models.adapter_utils 단위 테스트.

검증 대상:
  - normalize_score: 클리핑 범위, 경계값, 커스텀 범위
  - build_vote: 정상 딕셔너리 구조, score 클리핑 통과 여부
  - normalize_label: 임곗값 이상/미만/동일
  - text_overlap_score: 완전 일치, 부분 일치, 빈 문자열, 대소문자 무시
"""

from __future__ import annotations

import pytest

from app.models.adapter_utils import (
    build_vote,
    normalize_label,
    normalize_score,
    text_overlap_score,
)


# ── normalize_score ───────────────────────────────────────────────────────────


class TestNormalizeScore:
    def test_within_range_unchanged(self) -> None:
        assert normalize_score(0.5) == 0.5

    def test_above_max_clipped_to_one(self) -> None:
        assert normalize_score(1.5) == 1.0

    def test_below_min_clipped_to_zero(self) -> None:
        assert normalize_score(-0.3) == 0.0

    def test_exact_zero_boundary(self) -> None:
        assert normalize_score(0.0) == 0.0

    def test_exact_one_boundary(self) -> None:
        assert normalize_score(1.0) == 1.0

    def test_custom_min_max(self) -> None:
        assert normalize_score(5.0, min_val=2.0, max_val=4.0) == 4.0

    def test_custom_min_below(self) -> None:
        assert normalize_score(1.0, min_val=2.0, max_val=4.0) == 2.0

    def test_custom_range_within(self) -> None:
        assert normalize_score(3.0, min_val=2.0, max_val=4.0) == 3.0


# ── build_vote ────────────────────────────────────────────────────────────────


class TestBuildVote:
    def test_returns_dict_with_required_keys(self) -> None:
        vote = build_vote("blip", 0.8, "match", "looks good")
        assert set(vote.keys()) == {"model", "score", "label", "reason"}

    def test_model_field(self) -> None:
        vote = build_vote("siglip2", 0.5, "mismatch")
        assert vote["model"] == "siglip2"

    def test_label_field(self) -> None:
        vote = build_vote("blip", 0.9, "match")
        assert vote["label"] == "match"

    def test_score_clipped_above_one(self) -> None:
        vote = build_vote("blip", 1.5, "match")
        assert vote["score"] == 1.0

    def test_score_clipped_below_zero(self) -> None:
        vote = build_vote("blip", -0.2, "mismatch")
        assert vote["score"] == 0.0

    def test_score_passthrough_within_range(self) -> None:
        vote = build_vote("blip", 0.73, "match")
        assert vote["score"] == pytest.approx(0.73)

    def test_reason_default_empty(self) -> None:
        vote = build_vote("blip", 0.5, "match")
        assert vote["reason"] == ""

    def test_reason_custom(self) -> None:
        vote = build_vote("blip", 0.5, "match", "keyword found")
        assert vote["reason"] == "keyword found"


# ── normalize_label ───────────────────────────────────────────────────────────


class TestNormalizeLabel:
    def test_above_threshold_is_match(self) -> None:
        assert normalize_label(0.8, 0.6) == "match"

    def test_below_threshold_is_mismatch(self) -> None:
        assert normalize_label(0.4, 0.6) == "mismatch"

    def test_equal_to_threshold_is_match(self) -> None:
        assert normalize_label(0.6, 0.6) == "match"

    def test_zero_score(self) -> None:
        assert normalize_label(0.0, 0.5) == "mismatch"

    def test_one_score(self) -> None:
        assert normalize_label(1.0, 0.5) == "match"


# ── text_overlap_score ────────────────────────────────────────────────────────


class TestTextOverlapScore:
    def test_full_match_returns_one(self) -> None:
        assert text_overlap_score("hello", "hello world") == 1.0

    def test_no_match_returns_zero(self) -> None:
        assert text_overlap_score("cat", "a big dog") == 0.0

    def test_partial_match(self) -> None:
        score = text_overlap_score("hello world", "hello there")
        assert score == pytest.approx(0.5)

    def test_case_insensitive(self) -> None:
        assert text_overlap_score("HELLO", "hello world") == 1.0

    def test_empty_answer_returns_zero(self) -> None:
        assert text_overlap_score("", "some context") == 0.0

    def test_empty_context_returns_zero(self) -> None:
        assert text_overlap_score("hello", "") == 0.0

    def test_both_empty_returns_zero(self) -> None:
        assert text_overlap_score("", "") == 0.0

    def test_multi_word_full_match(self) -> None:
        score = text_overlap_score("cat dog bird", "I saw a cat and a dog and a bird")
        assert score == 1.0

    def test_multi_word_partial_match(self) -> None:
        score = text_overlap_score("화사한 분위기", "화사한 느낌의 사진")
        # "화사한" matches, "분위기" does not → 0.5
        assert score == pytest.approx(0.5)
