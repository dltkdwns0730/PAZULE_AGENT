from app.services.location_service import distance_meters, validate_client_location


def test_distance_meters_zero_for_same_coordinate():
    assert distance_meters(37.711988, 126.6867095, 37.711988, 126.6867095) == 0


def test_validate_client_location_allows_inside_radius(monkeypatch):
    monkeypatch.setattr(
        "app.services.location_service.settings.SKIP_GPS_VALIDATION", False
    )
    monkeypatch.setattr(
        "app.services.location_service.settings.MISSION_SITE_LAT", 37.711988
    )
    monkeypatch.setattr(
        "app.services.location_service.settings.MISSION_SITE_LON", 126.6867095
    )
    monkeypatch.setattr(
        "app.services.location_service.settings.MISSION_SITE_RADIUS_METERS", 300
    )
    monkeypatch.setattr(
        "app.services.location_service.settings.MISSION_GPS_MAX_ACCURACY_METERS", 100
    )

    result = validate_client_location(
        {
            "client_lat": "37.711988",
            "client_lng": "126.6867095",
            "accuracy_meters": "20",
        }
    )

    assert result["allowed"] is True
    assert result["reason"] == "ok"


def test_validate_client_location_rejects_outside_radius(monkeypatch):
    monkeypatch.setattr(
        "app.services.location_service.settings.SKIP_GPS_VALIDATION", False
    )
    monkeypatch.setattr(
        "app.services.location_service.settings.MISSION_SITE_LAT", 37.711988
    )
    monkeypatch.setattr(
        "app.services.location_service.settings.MISSION_SITE_LON", 126.6867095
    )
    monkeypatch.setattr(
        "app.services.location_service.settings.MISSION_SITE_RADIUS_METERS", 50
    )
    monkeypatch.setattr(
        "app.services.location_service.settings.MISSION_GPS_MAX_ACCURACY_METERS", 100
    )

    result = validate_client_location(
        {
            "client_lat": "37.720000",
            "client_lng": "126.700000",
            "accuracy_meters": "20",
        }
    )

    assert result["allowed"] is False
    assert result["reason"] == "outside_mission_site"


def test_validate_client_location_rejects_missing_gps(monkeypatch):
    monkeypatch.setattr(
        "app.services.location_service.settings.SKIP_GPS_VALIDATION", False
    )

    result = validate_client_location({})

    assert result["allowed"] is False
    assert result["reason"] == "gps_required"


def test_validate_client_location_rejects_low_accuracy(monkeypatch):
    monkeypatch.setattr(
        "app.services.location_service.settings.SKIP_GPS_VALIDATION", False
    )
    monkeypatch.setattr(
        "app.services.location_service.settings.MISSION_GPS_MAX_ACCURACY_METERS", 100
    )

    result = validate_client_location(
        {
            "client_lat": "37.711988",
            "client_lng": "126.6867095",
            "accuracy_meters": "150",
        }
    )

    assert result["allowed"] is False
    assert result["reason"] == "gps_accuracy_too_low"


def test_validate_client_location_can_skip(monkeypatch):
    monkeypatch.setattr(
        "app.services.location_service.settings.SKIP_GPS_VALIDATION", True
    )

    result = validate_client_location({})

    assert result["allowed"] is True
    assert result["reason"] == "gps_validation_skipped"
