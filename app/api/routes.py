"""Backward-compatibility shim for app.api.routes.

New code should import directly from:
- app.api.user_routes  (user-facing endpoints)
- app.api.admin_routes (operations console endpoints)
"""

from app.api.admin_routes import admin_api  # noqa: F401
from app.api.user_routes import user_api as api  # noqa: F401

__all__ = ["api", "admin_api"]
