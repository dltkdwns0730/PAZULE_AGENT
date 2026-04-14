from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.docs_audit.audit import (
    audit_project,
    render_report_markdown,
    scaffold_missing_documents,
    write_report_files,
    write_templates,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class DocsAuditTest(unittest.TestCase):
    def test_audit_detects_missing_ml_pipeline_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "README.md", "# Demo\n\n## Overview\n\nExample project.\n")
            _write(
                root / "docs" / "architecture.md",
                "# Architecture\n\n> **분류**: 설계 · **버전**: v1 · **최종 수정**: 2026-04-07\n\n## 상태 흐름\n\n## 노드 역할\n",
            )
            _write(
                root / "docs" / "api_specification.md",
                "# API Specification\n\n> **분류**: 레퍼런스 · **버전**: v1 · **최종 수정**: 2026-04-07\n\n## Request\n\n## Response\n\n## Error\n",
            )
            _write(
                root / "docs" / "CHANGELOG.md",
                "# Changelog\n\n> **분류**: 레퍼런스 · **버전**: v1 · **최종 수정**: 2026-04-07\n\n## v1.0\n",
            )
            _write(
                root / "docs" / "benchmarks" / "baseline.md",
                "# Benchmark\n\n> **분류**: 벤치마크 · **버전**: v1 · **최종 수정**: 2026-04-07\n\n## 목적\n\n## Test 1\n\n## 결론\n",
            )

            result = audit_project(root, profile="ml-pipeline")

            self.assertIn("feature_spec", result.missing_docs)
            self.assertIn("pipeline_verification", result.missing_docs)
            self.assertTrue(
                any(
                    f.code == "missing_end_to_end_pipeline_verification"
                    for f in result.findings
                )
            )

    def test_audit_detects_broken_relative_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(
                root / "README.md",
                "# Demo\n\n## Overview\n\nSee [spec](./docs/missing.md).\n",
            )

            result = audit_project(root, profile="generic")

            self.assertTrue(
                any(f.code == "broken_relative_link" for f in result.findings)
            )

    def test_report_and_template_writers_generate_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "README.md", "# Demo\n\n## Overview\n\nProject overview.\n")
            result = audit_project(root, profile="ml-pipeline")

            report_dir = root / "generated"
            write_report_files(result, report_dir)
            written_templates = write_templates(report_dir / "templates")
            written_scaffolds = scaffold_missing_documents(
                result, report_dir / "scaffold"
            )

            self.assertTrue((report_dir / "docs-audit-report.md").exists())
            self.assertTrue((report_dir / "docs-audit-report.json").exists())
            self.assertTrue((report_dir / "docs-index.generated.md").exists())
            self.assertTrue(
                any(
                    path.name == "feature-spec.template.md"
                    for path in written_templates
                )
            )
            self.assertTrue(
                any(path.name == "feature-spec.todo.md" for path in written_scaffolds)
            )

            payload = json.loads(
                (report_dir / "docs-audit-report.json").read_text(encoding="utf-8")
            )
            self.assertEqual(payload["stats"]["document_count"], 1)
            self.assertIn("## Summary", render_report_markdown(result))


if __name__ == "__main__":
    unittest.main()
