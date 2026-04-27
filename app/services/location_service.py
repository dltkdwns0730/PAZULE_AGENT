"""GPS location validation for mission access."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from app.core.config import settings


@dataclass(frozen=True)
class ClientLocation:
    latitude: float
    longitude: float
    accuracy_meters: float | None = None


class LocationValidationError(ValueError):
    """Raised when client GPS data is missing or malformed."""


def parse_client_location(payload: dict[str, Any]) -> ClientLocation:
    """Parse client-provided GPS coordinates from JSON or form payload."""
    try:
        latitude = float(payload["client_lat"])
        longitude = float(payload["client_lng"])
    except (KeyError, TypeError, ValueError) as exc:
        raise LocationValidationError("gps_required") from exc

    accuracy = payload.get("accuracy_meters")
    try:
        accuracy_meters = None if accuracy in (None, "") else float(accuracy)
    except (TypeError, ValueError) as exc:
        raise LocationValidationError("gps_accuracy_invalid") from exc

    return ClientLocation(latitude, longitude, accuracy_meters)


def distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the Haversine distance between two WGS84 coordinates."""
    earth_radius_m = 6_371_000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return earth_radius_m * c


def validate_client_location(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate client GPS against the configured mission site radius."""
    if settings.SKIP_GPS_VALIDATION:
        return {
            "allowed": True,
            "reason": "gps_validation_skipped",
            "skipped": True,
        }

    try:
        location = parse_client_location(payload)
    except LocationValidationError as exc:
        return {"allowed": False, "reason": str(exc)}

    max_accuracy = settings.MISSION_GPS_MAX_ACCURACY_METERS
    if location.accuracy_meters is not None and location.accuracy_meters > max_accuracy:
        return {
            "allowed": False,
            "reason": "gps_accuracy_too_low",
            "accuracy_meters": location.accuracy_meters,
            "max_accuracy_meters": max_accuracy,
        }

    distance = distance_meters(
        location.latitude,
        location.longitude,
        settings.MISSION_SITE_LAT,
        settings.MISSION_SITE_LON,
    )
    radius = settings.MISSION_SITE_RADIUS_METERS
    allowed = distance <= radius

    return {
        "allowed": allowed,
        "reason": "ok" if allowed else "outside_mission_site",
        "client_lat": location.latitude,
        "client_lng": location.longitude,
        "accuracy_meters": location.accuracy_meters,
        "distance_meters": round(distance, 2),
        "site_lat": settings.MISSION_SITE_LAT,
        "site_lng": settings.MISSION_SITE_LON,
        "site_radius_meters": radius,
    }
