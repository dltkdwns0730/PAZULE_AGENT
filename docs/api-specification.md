# API Specification

> **분류**: 레퍼런스 · **버전**: v3 · **최종 수정**: 2026-04-07
>
> 전체 엔드포인트의 요청/응답 스키마.
> Base URL: `http://localhost:8080`

---

## 1. Start Mission

`POST /api/mission/start`

**Request** (`application/json`):
```json
{
  "user_id": "guest-001",
  "site_id": "pazule-default",
  "mission_type": "location"
}
```
- `mission_type`: `location` 또는 `photo` (`photo`는 내부적으로 `atmosphere`로 정규화)

**Response** (`200`):
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

---

## 2. Submit Mission

`POST /api/mission/submit`

**Request** (`multipart/form-data`):
- `mission_id` (required)
- `image` (required)
- `model_selection` (optional): `blip` | `qwen` | `siglip2` | `ensemble`

**Response — 성공** (`200`):
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

**Response — 실패** (`200`):
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

**에러**:
- `400`: 잘못된 업로드, 세션 만료, 제출 횟수 초과
- `404`: 세션 없음

---

## 3. Issue Coupon

`POST /api/coupon/issue`

**Request** (`application/json`):
```json
{
  "mission_id": "uuid",
  "partner_id": "partner-01"
}
```

**Response** (`200`):
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

**에러**:
- `400`: 미션 미성공, 자격 없음
- `404`: 미션 세션 없음

---

## 4. Redeem Coupon

`POST /api/coupon/redeem`

**Request** (`application/json`):
```json
{
  "coupon_code": "AB12CD34",
  "partner_pos_id": "POS-1"
}
```

**Response — 성공** (`200`):
```json
{
  "redeem_status": "redeemed",
  "message": "Coupon redeemed.",
  "coupon": {}
}
```

**Response — 실패** (`400`):
```json
{
  "redeem_status": "already_redeemed",
  "message": "Coupon already redeemed.",
  "coupon": {}
}
```

---

## 5. Utility

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/get-today-hint?mission_type=location\|photo` | 오늘의 힌트 조회 |
| `POST` | `/api/preview` (`multipart/form-data`, field: `image`) | 이미지 미리보기 분석 |

---

## 참고

- 쿠폰 발급은 `mission_id` 기준 멱등(idempotent)
- 미션 제출 시 이미지 해시를 기록하여 유저별 중복 제출 감지
- 임계값, 모델 선택은 환경 변수로 설정 가능
