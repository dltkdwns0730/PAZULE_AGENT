"""프로젝트 문서 감사(audit) 오케스트레이션 모듈."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.legacy.docs_audit.checkers import (
    find_missing_doc_findings,
    find_missing_docs,
    recommend_actions,
    run_document_checks,
)
from app.legacy.docs_audit.report_types import (
    AuditFinding,
    AuditResult,
    DocumentRecord,
    SEVERITY_WEIGHTS,
)
from app.legacy.docs_audit.scanner import (
    collect_documents,
    detect_profile,
    discover_version_sources,
)

logger = logging.getLogger(__name__)


def audit_project(root_path: str | Path, profile: str = "auto") -> AuditResult:
    """프로젝트 문서를 감사하고 결과를 반환한다.

    Args:
        root_path: 감사할 프로젝트 루트 경로.
        profile: 감사 프로파일 ('auto' | 'generic' | 'python-service' | 'frontend' | 'ml-pipeline').

    Returns:
        전체 감사 결과 객체.

    Raises:
        FileNotFoundError: root_path가 존재하지 않을 때.
    """
    root = Path(root_path).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Root path does not exist: {root}")

    detected_profile = detect_profile(root)
    effective_profile = detected_profile if profile == "auto" else profile
    documents = collect_documents(root)
    version_sources = discover_version_sources(root)
    findings = run_document_checks(root, documents, effective_profile)
    missing_docs = find_missing_docs(documents, effective_profile)
    findings.extend(find_missing_doc_findings(missing_docs))
    recommended_actions = recommend_actions(findings, missing_docs)
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
    """감사 결과를 마크다운 형식의 리포트 문자열로 렌더링한다.

    Args:
        result: 감사 결과 객체.

    Returns:
        마크다운 형식의 리포트 문자열.
    """
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
    """감사 결과에서 문서 인덱스 마크다운을 생성한다.

    Args:
        result: 감사 결과 객체.

    Returns:
        마크다운 형식의 문서 인덱스 문자열.
    """
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
    """감사 결과를 마크다운, JSON, 인덱스 파일로 저장한다.

    Args:
        result: 감사 결과 객체.
        output_dir: 출력 디렉터리 경로.

    Returns:
        저장된 파일 경로 목록.
    """
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
    """문서 템플릿 파일들을 지정된 디렉터리에 생성한다.

    Args:
        output_dir: 출력 디렉터리 경로.

    Returns:
        생성된 템플릿 파일 경로 목록.
    """
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
    """누락된 필수 문서 유형에 대한 스캐폴딩 파일을 생성한다.

    Args:
        result: 감사 결과 객체.
        output_dir: 출력 디렉터리 경로.

    Returns:
        생성된 스캐폴딩 파일 경로 목록.
    """
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


def _group_docs_by_type(docs: list[DocumentRecord]) -> dict[str, list[DocumentRecord]]:
    """문서 목록을 유형별로 그룹화한다.

    Args:
        docs: 문서 레코드 목록.

    Returns:
        유형 → 문서 목록 딕셔너리.
    """
    grouped: dict[str, list[DocumentRecord]] = {}
    for doc in docs:
        grouped.setdefault(doc.doc_type, []).append(doc)
    return grouped


def _build_stats(
    docs: list[DocumentRecord], findings: list[AuditFinding]
) -> dict[str, Any]:
    """문서와 발견 항목 통계를 계산한다.

    Args:
        docs: 문서 레코드 목록.
        findings: 감사 발견 항목 목록.

    Returns:
        통계 딕셔너리 (document_count, finding_count, score, severity_counts).
    """
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


def _finding_sort_key(finding: AuditFinding) -> tuple[int, str, str]:
    """AuditFinding 정렬 키를 반환한다 (severity → path → code 순).

    Args:
        finding: 정렬할 AuditFinding.

    Returns:
        정렬 키 튜플.
    """
    order = {"high": 0, "medium": 1, "low": 2}
    return (order.get(finding.severity, 99), finding.path or "", finding.code)


def _feature_spec_template() -> str:
    """Feature Spec 문서 마크다운 템플릿을 반환한다.

    Returns:
        Feature Spec 템플릿 문자열.
    """
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
    """Pipeline Verification 문서 마크다운 템플릿을 반환한다.

    Returns:
        Pipeline Verification 템플릿 문자열.
    """
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
    """Benchmark Report 문서 마크다운 템플릿을 반환한다.

    Returns:
        Benchmark Report 템플릿 문자열.
    """
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
    """LLM 문서 감사 프롬프트 가이드 마크다운을 반환한다.

    Returns:
        프롬프트 가이드 문자열.
    """
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
