"""app.core.keyword 단위 테스트.

검증 대상:
  - keyword_mapping: 7개 키워드 존재, 각 리스트 비어있지 않음
  - feedback_guide: 7개 키워드 존재, 각 항목에 'desc' 키 포함
"""

from __future__ import annotations


from app.core.keyword import feedback_guide, keyword_mapping

EXPECTED_KEYWORDS = {
    "화사한",
    "차분한",
    "활기찬",
    "자연적인",
    "옛스러운",
    "신비로운",
    "웅장한",
}


class TestKeywordMapping:
    def test_all_keywords_present(self) -> None:
        assert EXPECTED_KEYWORDS == set(keyword_mapping.keys())

    def test_each_keyword_has_non_empty_list(self) -> None:
        for keyword, synonyms in keyword_mapping.items():
            assert len(synonyms) > 0, f"'{keyword}' 키워드의 동의어 목록이 비어있음"

    def test_synonyms_are_strings(self) -> None:
        for keyword, synonyms in keyword_mapping.items():
            for s in synonyms:
                assert isinstance(s, str), f"'{keyword}' 동의어 '{s}'가 문자열이 아님"


class TestFeedbackGuide:
    def test_all_keywords_present(self) -> None:
        assert EXPECTED_KEYWORDS == set(feedback_guide.keys())

    def test_each_entry_has_desc(self) -> None:
        for keyword, guide in feedback_guide.items():
            assert "desc" in guide, f"'{keyword}'에 'desc' 키 없음"

    def test_desc_is_non_empty_string(self) -> None:
        for keyword, guide in feedback_guide.items():
            assert isinstance(guide["desc"], str) and len(guide["desc"]) > 0
