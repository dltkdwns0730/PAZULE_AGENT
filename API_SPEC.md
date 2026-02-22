# PAZULE API Spec (v3)

Base URL: `http://localhost:8080`

## 1) Start Mission

- `POST /api/mission/start`
- Request (`application/json`):

```json
{
  "user_id": "guest-001",
  "site_id": "pazule-default",
  "mission_type": "location"
}
```

- `mission_type`: `location` or `photo`
  - `photo` is normalized internally to `atmosphere`

- Response (`200`):

```json
{
  "mission_id": "uuid",
  "mission_type": "location",
  "eligibility": {"allowed": true},
  "constraints": {
    "max_submissions": 3,
    "expires_at": "2026-02-18T10:00:00+00:00",
    "site_radius_meters": 300
  },
  "hint": "daily hint text"
}
```

## 2) Submit Mission

- `POST /api/mission/submit`
- Request (`multipart/form-data`):
  - `mission_id` (required)
  - `image` (required)
  - `model_selection` (optional): `clip|blip|qwen|siglip2|ensemble`

- Response success (`200`):

```json
{
  "success": true,
  "message": "Mission succeeded.",
  "missionType": "location",
  "couponEligible": true,
  "confidence": 0.86,
  "decision_trace": {},
  "model_votes": [],
  "mission_id": "uuid"
}
```

- Response fail (`200`):

```json
{
  "success": false,
  "message": "Mission conditions not satisfied.",
  "missionType": "photo",
  "hint": "best model reason",
  "confidence": 0.42,
  "decision_trace": {},
  "model_votes": [],
  "mission_id": "uuid"
}
```

- Validation failure examples:
  - `400`: invalid upload, session expired, submission limit reached
  - `404`: session not found

## 3) Issue Coupon

- `POST /api/coupon/issue`
- Request (`application/json`):

```json
{
  "mission_id": "uuid",
  "partner_id": "partner-01"
}
```

- Response (`200`):

```json
{
  "code": "AB12CD34",
  "description": "mission completion coupon",
  "mission_type": "mission1",
  "answer": "target text",
  "mission_id": "uuid",
  "partner_id": "partner-01",
  "discount_rule": "10%_OFF",
  "status": "issued",
  "issued_at": "2026-02-18T10:00:00+00:00",
  "expires_at": "2026-02-25T10:00:00+00:00",
  "redeemed_at": null,
  "partner_pos_id": null
}
```

- Failure examples:
  - `400`: mission not successful, not eligible
  - `404`: mission session not found

## 4) Redeem Coupon

- `POST /api/coupon/redeem`
- Request (`application/json`):

```json
{
  "coupon_code": "AB12CD34",
  "partner_pos_id": "POS-1"
}
```

- Response success (`200`):

```json
{
  "redeem_status": "redeemed",
  "message": "Coupon redeemed.",
  "coupon": {}
}
```

- Response fail (`400`):

```json
{
  "redeem_status": "already_redeemed",
  "message": "Coupon already redeemed.",
  "coupon": {}
}
```

## 5) Utility Endpoints

- `GET /get-today-hint?mission_type=location|photo`
- `POST /api/preview` (`multipart/form-data`, field: `image`)

## Notes

- Coupon issuance is idempotent by `mission_id`.
- Mission submit records image hash to detect duplicate submissions per user.
- Threshold and model selection behavior are environment-configurable.
