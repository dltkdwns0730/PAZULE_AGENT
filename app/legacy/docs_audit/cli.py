"""문서 감사 CLI 진입점 모듈."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from .audit import (
    audit_project,
    scaffold_missing_documents,
    write_report_files,
    write_templates,
)

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """CLI 인자 파서를 빌드한다.

    Returns:
        argparse.ArgumentParser 인스턴스.
    """
    parser = argparse.ArgumentParser(
        description="Audit project documentation from a single root path."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("scan", "report", "init-templates", "scaffold-missing"):
        sub = subparsers.add_parser(name)
        sub.add_argument("root_path", help="Project root path to audit.")
        sub.add_argument(
            "--profile",
            default="auto",
            choices=["auto", "generic", "python-service", "frontend", "ml-pipeline"],
            help="Rule profile for the audit.",
        )
        sub.add_argument(
            "--output-dir",
            default=None,
            help="Directory for generated files. Defaults to <root>/generated-docs/docs-audit.",
        )

    scan = subparsers.choices["scan"]
    scan.add_argument(
        "--format",
        default="pretty",
        choices=["pretty", "json"],
        help="Console output format.",
    )

    report = subparsers.choices["report"]
    report.add_argument(
        "--format",
        default="both",
        choices=["md", "json", "both"],
        help="Which report files to keep.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI 메인 진입점.

    Args:
        argv: 커맨드라인 인자 목록 (None이면 sys.argv 사용).

    Returns:
        종료 코드 (0: 성공, 2: 오류).
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root_path).resolve()
    output_dir = (
        Path(args.output_dir)
        if args.output_dir
        else root / "generated-docs" / "docs-audit"
    )

    if args.command == "scan":
        return _run_scan(args, root)

    if args.command == "report":
        return _run_report(args, root, output_dir)

    if args.command == "init-templates":
        for path in write_templates(output_dir):
            print(path)
        return 0

    if args.command == "scaffold-missing":
        return _run_scaffold(args, root, output_dir)

    parser.error(f"Unknown command: {args.command}")
    return 2


def _run_scan(args: argparse.Namespace, root: Path) -> int:
    """scan 서브커맨드를 실행한다.

    Args:
        args: 파싱된 CLI 인자.
        root: 감사할 프로젝트 루트 경로.

    Returns:
        종료 코드.
    """
    result = audit_project(root, profile=args.profile)
    if args.format == "json":
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"Root: {result.root_path}")
        print(f"Profile: {result.profile} (detected: {result.detected_profile})")
        print(f"Score: {result.stats['score']}")
        print(f"Documents: {result.stats['document_count']}")
        print(f"Findings: {result.stats['finding_count']}")
        if result.missing_docs:
            print("Missing:")
            for missing in result.missing_docs:
                print(f"  - {missing}")
        if result.findings:
            print("Top findings:")
            for finding in result.findings[:10]:
                location = f" ({finding.path})" if finding.path else ""
                print(
                    f"  - [{finding.severity}] {finding.code}{location}: {finding.message}"
                )
    return 0


def _run_report(args: argparse.Namespace, root: Path, output_dir: Path) -> int:
    """report 서브커맨드를 실행한다.

    Args:
        args: 파싱된 CLI 인자.
        root: 감사할 프로젝트 루트 경로.
        output_dir: 출력 디렉터리 경로.

    Returns:
        종료 코드.
    """
    result = audit_project(root, profile=args.profile)
    written = write_report_files(result, output_dir)
    if args.format == "md":
        (output_dir / "docs-audit-report.json").unlink(missing_ok=True)
    elif args.format == "json":
        (output_dir / "docs-audit-report.md").unlink(missing_ok=True)
        (output_dir / "docs-index.generated.md").unlink(missing_ok=True)
    for path in written:
        if path.exists():
            print(path)
    return 0


def _run_scaffold(args: argparse.Namespace, root: Path, output_dir: Path) -> int:
    """scaffold-missing 서브커맨드를 실행한다.

    Args:
        args: 파싱된 CLI 인자.
        root: 감사할 프로젝트 루트 경로.
        output_dir: 출력 디렉터리 경로.

    Returns:
        종료 코드.
    """
    result = audit_project(root, profile=args.profile)
    written = scaffold_missing_documents(result, output_dir)
    if not written:
        print("No missing scaffold targets.")
    else:
        for path in written:
            print(path)
    return 0
