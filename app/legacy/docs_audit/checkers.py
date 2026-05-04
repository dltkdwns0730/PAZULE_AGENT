"""규칙 기반 문서 검사 — docs_audit 체커 모듈."""

from __future__ import annotations

import re
from pathlib import Path

from app.legacy.docs_audit.report_types import (
    PROFILE_REQUIRED_TYPES,
    SECTION_RULES,
    AuditFinding,
    DocumentRecord,
)


def run_document_checks(
    root: Path, docs: list[DocumentRecord], profile: str
) -> list[AuditFinding]:
    """문서 목록에 대해 규칙 기반 검사를 수행한다.

    Args:
        root: 프로젝트 루트 경로.
        docs: 검사할 문서 레코드 목록.
        profile: 적용할 감사 프로파일.

    Returns:
        AuditFinding 목록.
    """
    if not docs:
        return [
            AuditFinding(
                severity="high",
                code="no_documents",
                message="No supported documentation files were found under the root path.",
                path=str(root),
            )
        ]

    findings: list[AuditFinding] = []
    doc_types = [doc.doc_type for doc in docs]

    for doc in docs:
        findings.extend(_check_single_document(doc))

    if profile == "ml-pipeline":
        findings.extend(_check_ml_pipeline_rules(root, doc_types))

    return findings


def find_missing_docs(docs: list[DocumentRecord], profile: str) -> list[str]:
    """프로파일 필수 문서 중 누락된 유형을 반환한다.

    Args:
        docs: 발견된 문서 레코드 목록.
        profile: 적용할 감사 프로파일.

    Returns:
        누락된 문서 유형 문자열 목록.
    """
    present = {doc.doc_type for doc in docs}
    return [
        doc_type
        for doc_type in PROFILE_REQUIRED_TYPES.get(profile, [])
        if doc_type not in present
    ]


def find_missing_doc_findings(missing_docs: list[str]) -> list[AuditFinding]:
    """누락된 문서 유형에 대한 AuditFinding을 생성한다.

    Args:
        missing_docs: 누락된 문서 유형 목록.

    Returns:
        AuditFinding 목록.
    """
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


def recommend_actions(
    findings: list[AuditFinding], missing_docs: list[str]
) -> list[str]:
    """감사 결과를 기반으로 권장 조치를 생성한다.

    Args:
        findings: 감사 발견 항목 목록.
        missing_docs: 누락된 문서 유형 목록.

    Returns:
        권장 조치 문자열 목록.
    """
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


def _check_single_document(doc: DocumentRecord) -> list[AuditFinding]:
    """단일 문서에 대한 품질 검사를 수행한다.

    Args:
        doc: 검사할 문서 레코드.

    Returns:
        AuditFinding 목록.
    """
    findings: list[AuditFinding] = []

    if doc.doc_type != "readme" and not doc.metadata.get("doc_class"):
        findings.append(
            AuditFinding(
                severity="low",
                code="missing_doc_class_meta",
                message="Document is missing classification metadata near the top.",
                path=doc.relative_path,
            )
        )
    if doc.doc_type not in {"readme", "other_doc"} and not doc.metadata.get("version"):
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
    return findings


def _check_ml_pipeline_rules(root: Path, doc_types: list[str]) -> list[AuditFinding]:
    """ML 파이프라인 프로파일 전용 규칙을 검사한다.

    Args:
        root: 프로젝트 루트 경로.
        doc_types: 발견된 문서 유형 목록.

    Returns:
        AuditFinding 목록.
    """
    findings: list[AuditFinding] = []
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
    """문서 유형별 필수 섹션 존재 여부를 검사한다.

    Args:
        doc: 검사할 문서 레코드.

    Returns:
        AuditFinding 목록.
    """
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


def _searchable_text(doc: DocumentRecord) -> str:
    """문서의 제목, 헤딩, 미리보기를 결합한 검색용 문자열을 반환한다.

    Args:
        doc: 문서 레코드.

    Returns:
        소문자로 정규화된 검색용 문자열.
    """
    headings = " ".join(_normalize_heading(heading) for heading in doc.headings)
    return f"{doc.title.lower()} {headings} {doc.body_preview.lower()}"


def _normalize_heading(heading: str) -> str:
    """헤딩 문자열에서 번호, 화살표 등을 제거하고 정규화한다.

    Args:
        heading: 헤딩 문자열.

    Returns:
        정규화된 헤딩 문자열.
    """
    heading = re.sub(r"^\d+[\.\)]\s*", "", heading.lower())
    heading = heading.replace("→", " ")
    return re.sub(r"\s+", " ", heading).strip()
