"""파일 탐색 및 문서 파싱 — docs_audit 스캐너 모듈."""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.legacy.docs_audit.report_types import (
    COMMON_META_PATTERNS,
    DOC_SUFFIXES,
    MARKDOWN_LINK_RE,
    SKIP_DIR_NAMES,
    DocumentRecord,
    LinkRecord,
)


def detect_profile(root: Path) -> str:
    """프로젝트 루트를 분석해 적합한 프로파일을 자동 감지한다.

    Args:
        root: 프로젝트 루트 경로.

    Returns:
        'ml-pipeline' | 'python-service' | 'frontend' | 'generic'.
    """
    has_pyproject = (root / "pyproject.toml").exists()
    has_package_json = (root / "package.json").exists() or any(
        root.glob("**/package.json")
    )
    has_benchmarks = any(
        "benchmarks" in path.parts for path in root.rglob("*") if path.is_file()
    )
    has_pipeline_terms = any(
        term in str(path).lower()
        for term in ("pipeline", "architecture", "api_spec", "docs")
        for path in root.rglob("*")
        if path.is_file()
    )
    if has_benchmarks and has_pipeline_terms:
        return "ml-pipeline"
    if has_pyproject:
        return "python-service"
    if has_package_json:
        return "frontend"
    return "generic"


def collect_documents(root: Path) -> list[DocumentRecord]:
    """루트 경로를 재귀 탐색하여 문서 레코드 목록을 수집한다.

    Args:
        root: 탐색할 루트 경로.

    Returns:
        DocumentRecord 목록.
    """
    records: list[DocumentRecord] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.suffix.lower() not in DOC_SUFFIXES:
            continue
        text = _read_text(path)
        if not text.strip():
            continue
        records.append(_build_document_record(root, path, text))
    return records


def discover_version_sources(root: Path) -> dict[str, str]:
    """프로젝트 파일에서 버전 정보를 탐색한다.

    Args:
        root: 프로젝트 루트 경로.

    Returns:
        파일 경로 → 버전 문자열 딕셔너리.
    """
    versions: dict[str, str] = {}
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        text = _read_text(pyproject)
        match = re.search(r'(?m)^version\s*=\s*"([^"]+)"', text)
        if match:
            versions["pyproject.toml"] = match.group(1)
    package_json_candidates = [root / "package.json", *root.glob("**/package.json")]
    seen: set[str] = set()
    for package_json in package_json_candidates:
        if not package_json.exists():
            continue
        rel = package_json.relative_to(root).as_posix()
        if rel in seen:
            continue
        seen.add(rel)
        try:
            data = json.loads(_read_text(package_json))
        except json.JSONDecodeError:
            continue
        version = data.get("version")
        if version:
            versions[rel] = str(version)
    return versions


def _build_document_record(root: Path, path: Path, text: str) -> DocumentRecord:
    """단일 문서 파일에서 DocumentRecord를 생성한다.

    Args:
        root: 프로젝트 루트 경로.
        path: 문서 파일 경로.
        text: 문서 텍스트 내용.

    Returns:
        생성된 DocumentRecord.
    """
    return DocumentRecord(
        path=str(path),
        relative_path=path.relative_to(root).as_posix(),
        doc_type=_classify_document(path, text),
        title=_extract_title(text) or path.stem,
        headings=_extract_headings(text),
        metadata=_extract_metadata(text),
        links=_extract_links(path, text),
        line_count=len(text.splitlines()),
        purpose_near_top=_has_purpose_near_top(text),
        body_preview=_preview(text),
    )


def _classify_document(path: Path, text: str) -> str:
    """파일 경로와 내용을 기반으로 문서 유형을 분류한다.

    Args:
        path: 문서 파일 경로.
        text: 문서 텍스트 내용.

    Returns:
        분류된 문서 유형 문자열.
    """
    rel = path.as_posix().lower()
    name = path.name.lower()
    title = (_extract_title(text) or "").lower()
    if name.startswith("readme"):
        return "readme"
    if "changelog" in name:
        return "changelog"
    if "benchmark" in rel or "benchmark" in name:
        return "benchmark"
    if "pipeline_verification" in rel or "pipeline verification" in title:
        return "pipeline_verification"
    if "verification" in name and "pipeline" in name:
        return "pipeline_verification"
    if "architecture" in name:
        return "architecture"
    if "api_spec" in name or "api specification" in title:
        return "api_spec"
    if "commercialization" in name or "strategy" in name:
        return "strategy"
    if "spec" in name and "api" not in name:
        return "feature_spec"
    if "feature spec" in title or "design doc" in title:
        return "feature_spec"
    return "other_doc"


def _extract_title(text: str) -> str | None:
    """문서 텍스트에서 H1 제목을 추출한다.

    Args:
        text: 문서 텍스트.

    Returns:
        제목 문자열 또는 None.
    """
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return None


def _extract_headings(text: str) -> list[str]:
    """문서 텍스트에서 모든 헤딩을 추출한다.

    Args:
        text: 문서 텍스트.

    Returns:
        헤딩 문자열 목록.
    """
    return [
        re.sub(r"^#+\s*", "", line.strip()).strip()
        for line in text.splitlines()
        if line.strip().startswith("#")
    ]


def _extract_metadata(text: str) -> dict[str, str]:
    """문서 상단에서 메타데이터 패턴을 추출한다.

    Args:
        text: 문서 텍스트.

    Returns:
        메타데이터 키-값 딕셔너리.
    """
    metadata: dict[str, str] = {}
    for key, pattern in COMMON_META_PATTERNS.items():
        match = pattern.search(text[:600])
        if match:
            metadata[key] = match.group(1).strip()
    return metadata


def _extract_links(path: Path, text: str) -> list[LinkRecord]:
    """문서 텍스트에서 마크다운 링크를 추출하고 유효성을 검사한다.

    Args:
        path: 문서 파일 경로 (상대 링크 해석 기준).
        text: 문서 텍스트.

    Returns:
        LinkRecord 목록.
    """
    records: list[LinkRecord] = []
    for target in MARKDOWN_LINK_RE.findall(text):
        if target.startswith(("http://", "https://", "mailto:")) or target.startswith(
            "#"
        ):
            records.append(
                LinkRecord(
                    target=target, resolved_path=None, is_relative=False, exists=True
                )
            )
            continue
        clean = target.split("#", 1)[0]
        resolved = (path.parent / clean).resolve()
        records.append(
            LinkRecord(
                target=target,
                resolved_path=str(resolved),
                is_relative=True,
                exists=resolved.exists(),
            )
        )
    return records


def _has_purpose_near_top(text: str) -> bool:
    """문서 상단 20줄 내에 목적/개요 관련 키워드가 있는지 확인한다.

    Args:
        text: 문서 텍스트.

    Returns:
        목적 키워드가 상단에 있으면 True.
    """
    lines = [line.strip().lower() for line in text.splitlines()[:20] if line.strip()]
    sample = " ".join(lines)
    return any(
        hint in sample
        for hint in ["목적", "purpose", "overview", "배경", "summary", "요약"]
    )


def _preview(text: str, limit: int = 1200) -> str:
    """문서 텍스트의 상단 미리보기 문자열을 생성한다.

    Args:
        text: 문서 텍스트.
        limit: 미리보기 최대 길이 (기본값: 1200).

    Returns:
        미리보기 문자열.
    """
    preview_lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " ".join(preview_lines[:12])[:limit]


def _read_text(path: Path) -> str:
    """파일을 UTF-8로 읽어 문자열로 반환한다.

    Args:
        path: 읽을 파일 경로.

    Returns:
        파일 텍스트 내용.
    """
    return path.read_text(encoding="utf-8", errors="replace")
