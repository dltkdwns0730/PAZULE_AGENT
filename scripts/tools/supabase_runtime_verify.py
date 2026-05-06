"""Verify Supabase DB and Google OAuth readiness without printing secrets."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, parse, request

from dotenv import dotenv_values, load_dotenv, set_key


ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT / ".env"
MANAGEMENT_API = "https://api.supabase.com/v1"
DEFAULT_REDIRECT_PATH = "/auth/callback"
EXPECTED_TABLES = {
    "coupons",
    "lead_submissions",
    "mission_events",
    "mission_sessions",
    "mission_submissions",
    "missions",
    "organization_members",
    "organizations",
    "sites",
    "user_profiles",
}


@dataclass(frozen=True)
class OAuthCheckResult:
    ready: bool
    status: int | None
    detail: str


def _load_env() -> dict[str, str]:
    if ENV_PATH.exists():
        load_dotenv(ENV_PATH, override=True)
        return {
            key: value or ""
            for key, value in dotenv_values(ENV_PATH).items()
            if key is not None
        }
    return {}


def _env_value(*names: str) -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value.strip()
    return ""


def _is_client_api_key(value: str) -> bool:
    return value.startswith("sb_publishable_") or value.startswith("eyJ")


def select_client_api_key(api_keys: list[dict[str, Any]]) -> str:
    """Choose a browser-safe Supabase API key from Management API records."""
    publishable: list[str] = []
    legacy_anon: list[str] = []
    for api_key in api_keys:
        value = str(api_key.get("api_key") or "")
        if not value:
            continue
        key_type = str(api_key.get("type") or "").lower()
        name = str(api_key.get("name") or "").lower()
        prefix = str(api_key.get("prefix") or "").lower()
        if value.startswith("sb_publishable_") or key_type == "publishable":
            publishable.append(value)
        elif name == "anon" or prefix == "anon":
            legacy_anon.append(value)
    if publishable:
        return publishable[0]
    if legacy_anon:
        return legacy_anon[0]
    raise RuntimeError("No publishable or legacy anon Supabase API key was returned.")


def fetch_project_client_api_key(project_ref: str, access_token: str) -> str:
    """Fetch the project's publishable/anon key using the Supabase Management API."""
    url = (
        f"{MANAGEMENT_API}/projects/{parse.quote(project_ref)}/api-keys" "?reveal=true"
    )
    req = request.Request(
        url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        },
    )
    try:
        with request.urlopen(req, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(
            "Supabase Management API could not reveal project API keys. "
            "Add VITE_SUPABASE_PUBLISHABLE_KEY manually from Dashboard > "
            f"Project Settings > API. status={exc.code} detail={detail}"
        ) from exc
    if not isinstance(payload, list):
        raise RuntimeError("Unexpected Supabase Management API response.")
    return select_client_api_key(payload)


def ensure_frontend_env_values(
    env_values: dict[str, str], *, sync_env: bool = False
) -> tuple[str, str]:
    supabase_url = _env_value("VITE_SUPABASE_URL", "SUPABASE_URL")
    client_key = _env_value(
        "VITE_SUPABASE_PUBLISHABLE_KEY",
        "SUPABASE_PUBLISHABLE_KEY",
        "SUPABASE_ANON_KEY",
    )
    if not client_key:
        project_ref = _env_value("SUPABASE_PROJECT_REF")
        access_token = _env_value("SUPABASE_ACCESS_TOKEN")
        if project_ref and access_token:
            client_key = fetch_project_client_api_key(project_ref, access_token)
    if not supabase_url:
        raise RuntimeError("Missing SUPABASE_URL or VITE_SUPABASE_URL.")
    if not client_key:
        raise RuntimeError(
            "Missing VITE_SUPABASE_PUBLISHABLE_KEY. Add a publishable or anon "
            "key for browser OAuth."
        )
    if not _is_client_api_key(client_key):
        raise RuntimeError(
            "Configured Supabase key is not frontend-safe. Do not use secret or "
            "service_role keys in Vite."
        )
    if sync_env and ENV_PATH.exists():
        if not env_values.get("VITE_SUPABASE_URL"):
            set_key(ENV_PATH, "VITE_SUPABASE_URL", supabase_url)
        if not env_values.get("VITE_SUPABASE_PUBLISHABLE_KEY"):
            set_key(ENV_PATH, "VITE_SUPABASE_PUBLISHABLE_KEY", client_key)
    return supabase_url.rstrip("/"), client_key


def build_google_oauth_url(supabase_url: str, redirect_to: str) -> str:
    url = f"{supabase_url.rstrip('/')}/auth/v1/authorize"
    return (
        f"{url}?{parse.urlencode({'provider': 'google', 'redirect_to': redirect_to})}"
    )


def verify_google_oauth_authorize(
    supabase_url: str, client_api_key: str, redirect_to: str
) -> OAuthCheckResult:
    authorize_url = build_google_oauth_url(supabase_url, redirect_to)
    req = request.Request(
        authorize_url,
        headers={
            "apikey": client_api_key,
            "Accept": "text/html,application/json",
            "User-Agent": "pazule-runtime-verify/1.0",
        },
    )
    try:
        with request.urlopen(req, timeout=20) as response:
            response.read()
            status = response.status
        return OAuthCheckResult(
            ready=status in {200, 302},
            status=status,
            detail="Google OAuth authorize endpoint responded.",
        )
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return OAuthCheckResult(False, exc.code, detail)
    except error.URLError as exc:
        return OAuthCheckResult(False, None, str(exc.reason))


def verify_expected_tables() -> tuple[bool, str]:
    database_url = _env_value("DATABASE_URL")
    if not database_url:
        return False, "DATABASE_URL is not configured; DB table check skipped."
    import psycopg

    with psycopg.connect(database_url, connect_timeout=10) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                select table_name
                from information_schema.tables
                where table_schema = 'public'
                """
            )
            found = {row[0] for row in cursor.fetchall()}
    missing = sorted(EXPECTED_TABLES - found)
    if missing:
        return False, f"Missing expected table(s): {', '.join(missing)}"
    return True, f"Found {len(EXPECTED_TABLES)} expected public table(s)."


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sync-env",
        action="store_true",
        help="Write VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY to .env if missing.",
    )
    parser.add_argument(
        "--redirect-to",
        default="http://localhost:5173/auth/callback",
        help="OAuth callback URL registered in Supabase Auth redirect URLs.",
    )
    parser.add_argument(
        "--check-db",
        action="store_true",
        help="Also verify expected public tables when DATABASE_URL is configured.",
    )
    args = parser.parse_args()

    env_values = _load_env()
    supabase_url, client_key = ensure_frontend_env_values(
        env_values, sync_env=args.sync_env
    )
    oauth = verify_google_oauth_authorize(supabase_url, client_key, args.redirect_to)
    print(f"oauth_google_ready={oauth.ready}")
    print(f"oauth_google_status={oauth.status}")
    if not oauth.ready:
        print(f"oauth_google_detail={oauth.detail[:500]}")
        return 1
    if args.check_db:
        db_ready, detail = verify_expected_tables()
        print(f"db_schema_ready={db_ready}")
        print(f"db_schema_detail={detail}")
        if not db_ready:
            return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)
