"""Documentation audit toolkit."""

from .audit import (
    AuditResult,
    DocumentRecord,
    audit_project,
    detect_profile,
    render_docs_index,
    render_report_markdown,
    scaffold_missing_documents,
    write_report_files,
    write_templates,
)

__all__ = [
    "AuditResult",
    "DocumentRecord",
    "audit_project",
    "detect_profile",
    "render_docs_index",
    "render_report_markdown",
    "scaffold_missing_documents",
    "write_report_files",
    "write_templates",
]
