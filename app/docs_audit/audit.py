from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


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


@dataclass
class LinkRecord:
    target: str
    resolved_path: str | None
    is_relative: bool
    exists: bool


@dataclass
class DocumentRecord:
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
    severity: str
    code: str
    message: str
    path: str | None = None
    evidence: str | None = None


@dataclass
class AuditResult:
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


def detect_profile(root: Path) -> str:
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


def audit_project(root_path: str | Path, profile: str = "auto") -> AuditResult:
    root = Path(root_path).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Root path does not exist: {root}")

    detected_profile = detect_profile(root)
    effective_profile = detected_profile if profile == "auto" else profile
    documents = _collect_documents(root)
    version_sources = _discover_version_sources(root)
    findings = _run_document_checks(root, documents, effective_profile)
    missing_docs = _find_missing_docs(documents, effective_profile)
    findings.extend(_find_missing_doc_findings(missing_docs))
    recommended_actions = _recommend_actions(findings, missing_docs)
    stats = _build_stats(documents, findings)

    return AuditResult(
        root_path=str(root),
        profile=effective_profile,
        detected_profile=detected_profile,
        documents=documents,
        findings=sorted(findings, key=_finding_sort_key),
        missing_docs=missing_docs,
        recommended_actions=recommended_actions,
        version_sources=version_sources,
        stats=stats,
    )


def render_report_markdown(result: AuditResult) -> str:
    lines: list[str] = []
    lines.append("# Documentation Audit Report")
    lines.append("")
    lines.append(f"- Root: `{result.root_path}`")
    lines.append(f"- Profile: `{result.profile}`")
    lines.append(f"- Detected Profile: `{result.detected_profile}`")
    lines.append(f"- Documentation Score: `{result.stats.get('score', 0)}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Documents scanned: `{result.stats.get('document_count', 0)}`")
    lines.append(f"- Findings: `{result.stats.get('finding_count', 0)}`")
    lines.append(f"- Missing required document types: `{len(result.missing_docs)}`")
    if result.version_sources:
        lines.append("")
        lines.append("## Version Sources")
        lines.append("")
        for path, version in sorted(result.version_sources.items()):
            lines.append(f"- `{path}` -> `{version}`")

    lines.append("")
    lines.append("## Document Inventory")
    lines.append("")
    lines.append("| Type | Count | Paths |")
    lines.append("|---|---:|---|")
    for doc_type, docs in sorted(_group_docs_by_type(result.documents).items()):
        joined = "<br/>".join(f"`{doc.relative_path}`" for doc in docs[:6])
        if len(docs) > 6:
            joined += "<br/>..."
        lines.append(f"| `{doc_type}` | {len(docs)} | {joined} |")

    lines.append("")
    lines.append("## Findings")
    lines.append("")
    if not result.findings:
        lines.append("- No findings.")
    else:
        for finding in result.findings:
            item = f"- [{finding.severity.upper()}] `{finding.code}`: {finding.message}"
            if finding.path:
                item += f" (`{finding.path}`)"
            lines.append(item)
            if finding.evidence:
                lines.append(f"  Evidence: `{finding.evidence}`")

    lines.append("")
    lines.append("## Missing Required Documentation")
    lines.append("")
    if not result.missing_docs:
        lines.append("- No missing required document types.")
    else:
        for doc_type in result.missing_docs:
            lines.append(f"- `{doc_type}`")

    lines.append("")
    lines.append("## Recommended Actions")
    lines.append("")
    for action in result.recommended_actions:
        lines.append(f"- {action}")

    return "\n".join(lines) + "\n"


def render_docs_index(result: AuditResult) -> str:
    lines: list[str] = []
    lines.append("# Generated Documentation Index")
    lines.append("")
    lines.append(f"- Root: `{result.root_path}`")
    lines.append(f"- Profile: `{result.profile}`")
    lines.append("")
    for doc_type, docs in sorted(_group_docs_by_type(result.documents).items()):
        lines.append(f"## {doc_type}")
        lines.append("")
        for doc in docs:
            lines.append(f"- `{doc.relative_path}`: {doc.title}")
        lines.append("")
    return "\n".join(lines) + "\n"


def write_report_files(result: AuditResult, output_dir: str | Path) -> list[Path]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "docs-audit-report.md"
    json_path = out_dir / "docs-audit-report.json"
    index_path = out_dir / "docs-index.generated.md"
    md_path.write_text(render_report_markdown(result), encoding="utf-8")
    json_path.write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    index_path.write_text(render_docs_index(result), encoding="utf-8")
    return [md_path, json_path, index_path]


def write_templates(output_dir: str | Path) -> list[Path]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "feature-spec.template.md": _feature_spec_template(),
        "pipeline-verification.template.md": _pipeline_verification_template(),
        "benchmark-report.template.md": _benchmark_template(),
        "llm-doc-audit-prompt.md": _llm_prompt_guide(),
    }
    written: list[Path] = []
    for filename, content in files.items():
        path = out_dir / filename
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def scaffold_missing_documents(
    result: AuditResult, output_dir: str | Path
) -> list[Path]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    templates = {
        "feature_spec": ("feature-spec.todo.md", _feature_spec_template()),
        "pipeline_verification": (
            "pipeline-verification.todo.md",
            _pipeline_verification_template(),
        ),
        "benchmark": ("benchmark-report.todo.md", _benchmark_template()),
    }
    written: list[Path] = []
    for missing_type in result.missing_docs:
        if missing_type not in templates:
            continue
        filename, content = templates[missing_type]
        path = out_dir / filename
        if path.exists():
            continue
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def _collect_documents(root: Path) -> list[DocumentRecord]:
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


def _build_document_record(root: Path, path: Path, text: str) -> DocumentRecord:
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
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return None


def _extract_headings(text: str) -> list[str]:
    return [
        re.sub(r"^#+\s*", "", line.strip()).strip()
        for line in text.splitlines()
        if line.strip().startswith("#")
    ]


def _extract_metadata(text: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for key, pattern in COMMON_META_PATTERNS.items():
        match = pattern.search(text[:600])
        if match:
            metadata[key] = match.group(1).strip()
    return metadata


def _extract_links(path: Path, text: str) -> list[LinkRecord]:
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
    lines = [line.strip().lower() for line in text.splitlines()[:20] if line.strip()]
    sample = " ".join(lines)
    return any(
        hint in sample
        for hint in ["목적", "purpose", "overview", "배경", "summary", "요약"]
    )


def _run_document_checks(
    root: Path, docs: list[DocumentRecord], profile: str
) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    doc_types = [doc.doc_type for doc in docs]
    if not docs:
        return [
            AuditFinding(
                severity="high",
                code="no_documents",
                message="No supported documentation files were found under the root path.",
                path=str(root),
            )
        ]

    for doc in docs:
        if doc.doc_type != "readme" and not doc.metadata.get("doc_class"):
            findings.append(
                AuditFinding(
                    severity="low",
                    code="missing_doc_class_meta",
                    message="Document is missing classification metadata near the top.",
                    path=doc.relative_path,
                )
            )
        if doc.doc_type not in {"readme", "other_doc"} and not doc.metadata.get(
            "version"
        ):
            findings.append(
                AuditFinding(
                    severity="low",
                    code="missing_version_meta",
                    message="Document is missing version metadata near the top.",
                    path=doc.relative_path,
                )
            )
        if doc.doc_type not in {"readme", "other_doc"} and not doc.metadata.get(
            "last_updated"
        ):
            findings.append(
                AuditFinding(
                    severity="low",
                    code="missing_last_updated_meta",
                    message="Document is missing last-updated metadata near the top.",
                    path=doc.relative_path,
                )
            )
        if len(doc.headings) < 2 and doc.doc_type != "changelog":
            findings.append(
                AuditFinding(
                    severity="low",
                    code="too_few_sections",
                    message="Document has fewer than two headings.",
                    path=doc.relative_path,
                )
            )
        if not doc.purpose_near_top and doc.doc_type != "changelog":
            findings.append(
                AuditFinding(
                    severity="low",
                    code="purpose_not_clear_near_top",
                    message="Document purpose is not obvious near the top of the file.",
                    path=doc.relative_path,
                )
            )
        for link in doc.links:
            if link.is_relative and not link.exists:
                findings.append(
                    AuditFinding(
                        severity="medium",
                        code="broken_relative_link",
                        message="Document contains a broken relative link.",
                        path=doc.relative_path,
                        evidence=link.target,
                    )
                )
        findings.extend(_check_doc_type_sections(doc))

    if profile == "ml-pipeline":
        if "benchmark" in doc_types and "pipeline_verification" not in doc_types:
            findings.append(
                AuditFinding(
                    severity="high",
                    code="missing_end_to_end_pipeline_verification",
                    message="ML pipeline project has benchmark docs but no end-to-end pipeline verification document.",
                    path=str(root),
                )
            )
        if "changelog" in doc_types and "feature_spec" not in doc_types:
            findings.append(
                AuditFinding(
                    severity="high",
                    code="missing_feature_spec_workflow",
                    message="Project has version history but no feature-spec document type for future changes.",
                    path=str(root),
                )
            )
    return findings


def _check_doc_type_sections(doc: DocumentRecord) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    searchable = _searchable_text(doc)
    for rule_name, aliases in SECTION_RULES.get(doc.doc_type, []):
        if not any(alias.lower() in searchable for alias in aliases):
            findings.append(
                AuditFinding(
                    severity="medium",
                    code=f"missing_section_{rule_name}",
                    message=f"Document appears to be missing the '{rule_name}' section expected for {doc.doc_type}.",
                    path=doc.relative_path,
                )
            )
    return findings


def _find_missing_docs(docs: list[DocumentRecord], profile: str) -> list[str]:
    present = {doc.doc_type for doc in docs}
    return [
        doc_type
        for doc_type in PROFILE_REQUIRED_TYPES.get(profile, [])
        if doc_type not in present
    ]


def _find_missing_doc_findings(missing_docs: list[str]) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    for missing_doc in missing_docs:
        severity = (
            "high"
            if missing_doc in {"feature_spec", "pipeline_verification"}
            else "medium"
        )
        findings.append(
            AuditFinding(
                severity=severity,
                code="missing_required_doc_type",
                message=f"Required document type is missing: {missing_doc}",
                evidence=missing_doc,
            )
        )
    return findings


def _recommend_actions(
    findings: list[AuditFinding], missing_docs: list[str]
) -> list[str]:
    actions: list[str] = []
    if missing_docs:
        actions.append(
            "Create template-backed documents for the missing required types first."
        )
    if any(f.code == "broken_relative_link" for f in findings):
        actions.append(
            "Fix broken relative links so design and verification docs stay navigable."
        )
    if any(f.code == "missing_feature_spec_workflow" for f in findings):
        actions.append(
            "Add a feature-spec workflow so changelog entries are backed by change design records."
        )
    if any(f.code == "missing_end_to_end_pipeline_verification" for f in findings):
        actions.append(
            "Add an end-to-end pipeline verification doc that covers validator to responder outcomes."
        )
    if any(f.code.startswith("missing_section_") for f in findings):
        actions.append(
            "Standardize document sections by type so benchmark, spec, and verification docs are comparable."
        )
    if not actions:
        actions.append(
            "Documentation structure is healthy; keep using the current templates and metadata header."
        )
    return actions


def _discover_version_sources(root: Path) -> dict[str, str]:
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


def _group_docs_by_type(docs: list[DocumentRecord]) -> dict[str, list[DocumentRecord]]:
    grouped: dict[str, list[DocumentRecord]] = {}
    for doc in docs:
        grouped.setdefault(doc.doc_type, []).append(doc)
    return grouped


def _build_stats(
    docs: list[DocumentRecord], findings: list[AuditFinding]
) -> dict[str, Any]:
    penalty = sum(SEVERITY_WEIGHTS.get(finding.severity, 0) for finding in findings)
    severity_counts = {"high": 0, "medium": 0, "low": 0}
    for finding in findings:
        if finding.severity in severity_counts:
            severity_counts[finding.severity] += 1
    return {
        "document_count": len(docs),
        "finding_count": len(findings),
        "score": max(0, 100 - penalty),
        "severity_counts": severity_counts,
    }


def _searchable_text(doc: DocumentRecord) -> str:
    headings = " ".join(_normalize_heading(heading) for heading in doc.headings)
    return f"{doc.title.lower()} {headings} {doc.body_preview.lower()}"


def _normalize_heading(heading: str) -> str:
    heading = re.sub(r"^\d+[\.\)]\s*", "", heading.lower())
    heading = heading.replace("→", " ")
    return re.sub(r"\s+", " ", heading).strip()


def _preview(text: str, limit: int = 1200) -> str:
    preview_lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " ".join(preview_lines[:12])[:limit]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _finding_sort_key(finding: AuditFinding) -> tuple[int, str, str]:
    order = {"high": 0, "medium": 1, "low": 2}
    return (order.get(finding.severity, 99), finding.path or "", finding.code)


def _feature_spec_template() -> str:
    return """# Feature Specification

> **분류**: 명세 · **버전**: v0.1 · **최종 수정**: YYYY-MM-DD

## 배경

- 어떤 문제를 해결하려는가
- 기존 방식이 왜 부족한가

## 목표 / 비목표

- 목표:
- 비목표:

## 영향 범위

- 사용자 영향:
- 운영 영향:
- 문서 영향:

## API / 상태 / 데이터 변경

- API:
- 상태:
- 데이터:

## 구현 개요

- 핵심 흐름:
- 주요 컴포넌트:

## 테스트 계획

- 단위 테스트:
- 통합 테스트:
- 회귀 검증:

## 롤백 / 호환성

- 롤백 기준:
- 호환성 고려사항:
"""


def _pipeline_verification_template() -> str:
    return """# Pipeline Verification Report

> **분류**: 검증 · **버전**: v0.1 · **최종 수정**: YYYY-MM-DD

## 검증 대상

- 대상 버전:
- 대상 파이프라인:

## 시나리오

| 시나리오 | 입력 | 기대 결과 |
|---|---|---|
| 예시 | sample.jpg | success=true |

## 실행 조건

- 환경:
- 모델 설정:
- 데이터 조건:

## 실제 결과

| 시나리오 | 실제 결과 | 차이 | 회귀 여부 |
|---|---|---|---|
| 예시 | success=true | 없음 | No |

## 실패 케이스

- 무엇이 실패했는가
- 원인 후보는 무엇인가

## 결론

- 배포 가능 여부:
- 추가 조치:
"""


def _benchmark_template() -> str:
    return """# Benchmark Report

> **분류**: 벤치마크 · **버전**: v0.1 · **최종 수정**: YYYY-MM-DD

## 목적

- 무엇을 비교하는가

## 변경 사항

- 코드 / 프롬프트 / 설정 변경 사항

## 환경

- 모델:
- 장비:
- 라이브러리 버전:

## 데이터셋 / 샘플

- 샘플 수:
- 입력 설명:

## 실행 방법

```bash
python scripts/benchmark_example.py
```

## 결과

| 항목 | baseline | candidate | 변화 |
|---|---:|---:|---:|
| score | 0.00 | 0.00 | 0.00 |

## 결론

- 무엇이 좋아졌는가
- 무엇이 아직 부족한가

## 다음 액션

- 후속 실험:
- 문서 반영:
"""


def _llm_prompt_guide() -> str:
    return """# LLM Documentation Audit Prompt Guide

상위 폴더 경로만 주어졌을 때 아래 순서로 문서 감사를 수행한다.

## 입력

- root path
- profile: generic | python-service | frontend | ml-pipeline
- output goal: audit | index | scaffold suggestions

## 점검 순서

1. 파일 트리를 스캔해 README, docs, changelog, API spec, benchmark, tests, scripts를 찾는다.
2. 문서를 유형별로 분류한다.
3. 각 문서에서 제목, 분류, 버전, 최종 수정, 섹션 구조를 확인한다.
4. 상대 링크와 테스트/스크립트 참조를 점검한다.
5. profile 기준으로 필수 문서가 누락되었는지 확인한다.
6. 벤치마크 문서와 검증 문서가 실제 파이프라인 전체를 다루는지 구분한다.
7. 결과를 아래 포맷으로 정리한다.

## 출력 포맷

### Summary
- 프로젝트 성격
- 문서 점수
- 큰 결함 3개

### Inventory
- 문서 유형별 목록

### Findings
- high / medium / low

### Missing Docs
- 필요한 문서 유형

### Recommended Actions
- 우선순위 순서의 개선안
"""
