"""데이터클래스, 상수, 정규식 — docs_audit 모듈 공유 타입."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------

DOC_SUFFIXES = {".md", ".mdx", ".rst", ".txt"}
SKIP_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    "dist",
    "build",
    "generated-docs",
}
PROFILE_REQUIRED_TYPES = {
    "generic": ["readme", "changelog"],
    "python-service": ["readme", "api_spec", "changelog"],
    "frontend": ["readme", "changelog"],
    "ml-pipeline": [
        "readme",
        "architecture",
        "api_spec",
        "changelog",
        "benchmark",
        "feature_spec",
        "pipeline_verification",
    ],
}
SEVERITY_WEIGHTS = {"high": 12, "medium": 4, "low": 1}
SECTION_RULES: dict[str, list[tuple[str, list[str]]]] = {
    "benchmark": [
        ("purpose", ["목적", "purpose"]),
        ("test", ["test ", "실험", "시나리오"]),
        ("conclusion", ["결론", "conclusion", "요약"]),
    ],
    "feature_spec": [
        ("background", ["배경", "background", "문제"]),
        ("goal", ["목표", "goal", "goals", "비목표", "non-goal"]),
        ("impact", ["영향", "api", "데이터", "state", "상태"]),
        ("test_plan", ["테스트", "test", "검증"]),
    ],
    "pipeline_verification": [
        ("target", ["검증 대상", "version", "버전"]),
        ("scenario", ["시나리오", "scenario", "입력"]),
        ("expected", ["기대", "expected"]),
        ("actual", ["실제", "actual", "결과"]),
    ],
    "api_spec": [
        ("endpoint", ["start mission", "submit mission", "request", "endpoint"]),
        ("response", ["response", "응답"]),
        ("error", ["error", "에러"]),
    ],
    "architecture": [
        ("flow", ["상태 흐름", "state contract", "flow"]),
        ("node", ["노드", "node"]),
        ("decision", ["council", "judge", "router"]),
    ],
    "changelog": [("version_entries", ["## v", "### v"])],
}
COMMON_META_PATTERNS = {
    "doc_class": re.compile(
        r"\*\*(?:분류|classification)\*\*:\s*([^\n·|]+)", re.IGNORECASE
    ),
    "version": re.compile(r"\*\*(?:버전|version)\*\*:\s*([^\n·|]+)", re.IGNORECASE),
    "last_updated": re.compile(
        r"\*\*(?:최종 수정|last updated)\*\*:\s*([^\n·|]+)", re.IGNORECASE
    ),
}
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


# ---------------------------------------------------------------------------
# 데이터클래스
# ---------------------------------------------------------------------------


@dataclass
class LinkRecord:
    """문서 내 링크 정보."""

    target: str
    resolved_path: str | None
    is_relative: bool
    exists: bool


@dataclass
class DocumentRecord:
    """감사 대상 문서의 메타데이터 및 내용 요약."""

    path: str
    relative_path: str
    doc_type: str
    title: str
    headings: list[str]
    metadata: dict[str, str]
    links: list[LinkRecord]
    line_count: int
    purpose_near_top: bool
    body_preview: str


@dataclass
class AuditFinding:
    """감사 결과 발견 항목."""

    severity: str
    code: str
    message: str
    path: str | None = None
    evidence: str | None = None


@dataclass
class AuditResult:
    """전체 감사 결과."""

    root_path: str
    profile: str
    detected_profile: str
    documents: list[DocumentRecord]
    findings: list[AuditFinding]
    missing_docs: list[str]
    recommended_actions: list[str]
    version_sources: dict[str, str]
    stats: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """감사 결과를 직렬화 가능한 딕셔너리로 변환한다.

        Returns:
            감사 결과 딕셔너리.
        """
        return {
            "root_path": self.root_path,
            "profile": self.profile,
            "detected_profile": self.detected_profile,
            "documents": [asdict(doc) for doc in self.documents],
            "findings": [asdict(finding) for finding in self.findings],
            "missing_docs": self.missing_docs,
            "recommended_actions": self.recommended_actions,
            "version_sources": self.version_sources,
            "stats": self.stats,
        }
