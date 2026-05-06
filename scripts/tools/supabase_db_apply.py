"""Apply PAZULE Supabase migrations using values from the repo .env file.

Default mode is a dry run. Pass --apply to mutate the remote database.
Secrets are never printed; commands are logged with sensitive values redacted.
"""

from __future__ import annotations

import argparse
import getpass
import os
import shutil
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv


PROJECT_REF = "yooopszfddqzybicpotx"
ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT / ".env"


def _load_env() -> None:
    if ENV_PATH.exists():
        load_dotenv(ENV_PATH, override=True)


def _npx() -> str:
    executable = shutil.which("npx.cmd") or shutil.which("npx")
    if not executable:
        raise RuntimeError("npx is required but was not found on PATH.")
    return executable


def _redact(parts: list[str]) -> str:
    redacted: list[str] = []
    redact_next = False
    for part in parts:
        if redact_next:
            redacted.append("***")
            redact_next = False
            continue
        redacted.append(part)
        if part in {"--db-url", "--password", "--token"}:
            redact_next = True
    return " ".join(redacted)


def _run(parts: list[str], *, env: dict[str, str]) -> None:
    print(f"$ {_redact(parts)}")
    subprocess.run(parts, cwd=ROOT, env=env, check=True)


def _require_any(*names: str) -> None:
    missing = [name for name in names if not os.getenv(name)]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"Missing required .env value(s): {joined}")


def _optional_secret(name: str, prompt: str, *, allow_prompt: bool) -> str:
    value = os.getenv(name)
    if value:
        return value
    if allow_prompt and sys.stdin.isatty():
        return getpass.getpass(prompt)
    raise RuntimeError(
        f"Missing {name}. Set it only in the current PowerShell session, for "
        "example: $env:SUPABASE_DB_PASSWORD='...'. Do not store it in .env."
    )


def _build_env() -> dict[str, str]:
    env = os.environ.copy()
    token = os.getenv("SUPABASE_ACCESS_TOKEN")
    if token:
        env["SUPABASE_ACCESS_TOKEN"] = token
    return env


def _push_with_database_url(args: argparse.Namespace, env: dict[str, str]) -> None:
    _require_any("DATABASE_URL")
    command = [
        _npx(),
        "supabase",
        "db",
        "push",
        "--db-url",
        os.environ["DATABASE_URL"],
    ]
    if not args.apply:
        command.append("--dry-run")
    if args.include_all:
        command.append("--include-all")
    _run(command, env=env)


def _link_and_push(args: argparse.Namespace, env: dict[str, str]) -> None:
    _require_any("SUPABASE_ACCESS_TOKEN")
    db_password = _optional_secret(
        "SUPABASE_DB_PASSWORD",
        "Supabase database password: ",
        allow_prompt=args.prompt_password,
    )
    _run(
        [
            _npx(),
            "supabase",
            "link",
            "--project-ref",
            args.project_ref,
            "--password",
            db_password,
        ],
        env=env,
    )
    command = [
        _npx(),
        "supabase",
        "db",
        "push",
        "--password",
        db_password,
    ]
    if not args.apply:
        command.append("--dry-run")
    if args.include_all:
        command.append("--include-all")
    _run(command, env=env)


def _smoke_check() -> None:
    _require_any("DATABASE_URL")
    from app.db.session import smoke_check_database_connection

    ok = smoke_check_database_connection(os.environ["DATABASE_URL"])
    print(f"DB smoke check: {ok}")
    if not ok:
        raise RuntimeError("DB smoke check failed.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply migrations. Without this flag, only dry-run is executed.",
    )
    parser.add_argument(
        "--project-ref",
        default=os.getenv("SUPABASE_PROJECT_REF", PROJECT_REF),
        help="Supabase project ref used when DATABASE_URL is not provided.",
    )
    parser.add_argument(
        "--include-all",
        action="store_true",
        help="Pass --include-all to supabase db push.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run SQLAlchemy SELECT 1 smoke check after migration command.",
    )
    parser.add_argument(
        "--prompt-password",
        action="store_true",
        help="Prompt for SUPABASE_DB_PASSWORD in an interactive terminal.",
    )
    args = parser.parse_args()

    _load_env()
    env = _build_env()
    if os.getenv("DATABASE_URL", "").startswith("postgres"):
        _push_with_database_url(args, env)
    else:
        _link_and_push(args, env)

    if args.smoke:
        _smoke_check()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
