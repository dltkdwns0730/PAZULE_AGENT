from __future__ import annotations

import argparse
import json
from pathlib import Path

from .audit import (
    audit_project,
    scaffold_missing_documents,
    write_report_files,
    write_templates,
)


def build_parser() -> argparse.ArgumentParser:
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
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root_path).resolve()
    output_dir = Path(args.output_dir) if args.output_dir else root / "generated-docs" / "docs-audit"

    if args.command == "scan":
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
                    print(f"  - [{finding.severity}] {finding.code}{location}: {finding.message}")
        return 0

    if args.command == "report":
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

    if args.command == "init-templates":
        for path in write_templates(output_dir):
            print(path)
        return 0

    if args.command == "scaffold-missing":
        result = audit_project(root, profile=args.profile)
        written = scaffold_missing_documents(result, output_dir)
        if not written:
            print("No missing scaffold targets.")
        else:
            for path in written:
                print(path)
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2
