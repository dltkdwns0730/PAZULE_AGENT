# 관리자 계정 기업별 분류 운영 절차

이 문서는 Supabase Auth 계정을 PAZULE의 B2B 멀티컴퍼니 운영 구조에 맞게 분류하는 수동 운영 절차다.

## 목적

- 마스터 계정은 모든 컴퍼니, 사이트, 사용자 활동, 미션, 쿠폰을 조회한다.
- 컴퍼니 관리자는 자기 컴퍼니에 연결된 사이트와 활동만 조회한다.
- 일반 미션 참여자는 `organization_members`에 넣지 않아도 된다. 미션 활동의 기업 분류는 `mission_sessions.site_id -> sites.organization_id` 관계로 처리한다.

## 데이터 구조

| 테이블 | 역할 |
|---|---|
| `organizations` | 기업/컴퍼니 |
| `sites` | 기업이 운영하는 미션 장소 또는 지점 |
| `user_profiles` | Supabase 로그인 계정 프로필 |
| `organization_members` | 관리자/스태프 계정의 기업 소속과 권한 |
| `mission_sessions` | 사용자 미션 활동 |
| `coupons` | 쿠폰 발급/사용 이력 |

## 권한 기준

`organization_members.role`은 회사 내부 관리자 권한에 사용한다.

| role | 용도 |
|---|---|
| `owner` | 회사 최고 관리자 |
| `manager` | 회사 운영 관리자 |
| `viewer` | 조회 전용 관리자 |
| `partner_staff` | 제휴처/매장 직원 |

전체 마스터 권한은 Supabase Auth 유저의 `app_metadata.role`로 지정한다.

```json
{
  "role": "platform_master"
}
```

현재 코드는 `"admin"`도 마스터 권한으로 인정한다.

## 작업 순서

1. 기업 목록을 확정한다.
2. `organizations`에 기업을 등록한다.
3. 각 `sites`가 어느 기업 소속인지 연결한다.
4. Supabase Auth 유저를 `user_profiles`에 동기화한다.
5. 관리자/스태프 계정을 `organization_members`에 배정한다.
6. 전체 권한이 필요한 계정은 Supabase Auth `app_metadata.role = platform_master`로 지정한다.
7. `/admin`에서 회사 필터와 데이터 분리가 맞는지 확인한다.

## 1. 기업 등록

Supabase Dashboard > SQL Editor에서 실행한다.

```sql
insert into public.organizations (id, name, slug, created_at)
values
  ('company-pazule', 'PAZULE 운영사', 'pazule', now()),
  ('company-a', 'A 컴퍼니', 'company-a', now()),
  ('company-b', 'B 컴퍼니', 'company-b', now())
on conflict (slug) do nothing;
```

`id`는 읽기 쉬운 문자열 또는 UUID를 사용할 수 있다. 한 번 정한 `id`는 `sites.organization_id`와 `organization_members.organization_id`에서 계속 참조하므로 임의 변경하지 않는다.

## 2. 사이트를 기업에 연결

기본 사이트를 특정 기업에 연결한다.

```sql
update public.sites
set organization_id = 'company-a'
where id = 'pazule-default';
```

새 사이트를 만들 때는 처음부터 `organization_id`를 지정한다.

```sql
insert into public.sites (
  id,
  organization_id,
  slug,
  name,
  latitude,
  longitude,
  radius_meters,
  is_active,
  created_at
)
values (
  'site-company-a-main',
  'company-a',
  'company-a-main',
  'A 컴퍼니 메인 지점',
  37.711988,
  126.6867095,
  300,
  true,
  now()
)
on conflict (slug) do nothing;
```

## 3. Supabase Auth 계정 동기화

로그인 계정이 `user_profiles`에 없으면 관리자 배정이 되지 않는다. Auth 유저를 프로필 테이블에 동기화한다.

```sql
insert into public.user_profiles (id, email, display_name, created_at)
select
  id::text,
  email,
  coalesce(raw_user_meta_data->>'name', email),
  created_at
from auth.users
on conflict (id) do update
set
  email = excluded.email,
  display_name = excluded.display_name;
```

## 4. 계정을 기업에 배정

특정 이메일 계정을 A 컴퍼니 최고 관리자로 등록한다.

```sql
insert into public.organization_members (
  id,
  organization_id,
  user_id,
  role,
  created_at
)
select
  gen_random_uuid()::text,
  'company-a',
  id,
  'owner',
  now()
from public.user_profiles
where email = 'admin-a@example.com'
on conflict (organization_id, user_id) do update
set role = excluded.role;
```

여러 명을 같은 역할로 한 번에 등록한다.

```sql
insert into public.organization_members (
  id,
  organization_id,
  user_id,
  role,
  created_at
)
select
  gen_random_uuid()::text,
  'company-a',
  id,
  'manager',
  now()
from public.user_profiles
where email in (
  'manager1@example.com',
  'manager2@example.com',
  'manager3@example.com'
)
on conflict (organization_id, user_id) do update
set role = excluded.role;
```

## 5. 마스터 계정 지정

Supabase Dashboard에서 해당 유저의 App Metadata에 다음 값을 넣는다.

```json
{
  "role": "platform_master"
}
```

마스터 계정은 `organization_members`에 등록하지 않아도 모든 기업을 조회할 수 있다.

## 확인 쿼리

기업별 관리자/스태프 목록을 확인한다.

```sql
select
  o.name as company,
  up.email,
  up.display_name,
  om.role
from public.organization_members om
join public.organizations o on o.id = om.organization_id
join public.user_profiles up on up.id = om.user_id
order by o.name, om.role, up.email;
```

기업별 미션 활동을 확인한다.

```sql
select
  o.name as company,
  s.name as site,
  ms.user_id,
  up.email,
  ms.mission_type,
  ms.status,
  ms.created_at
from public.mission_sessions ms
join public.sites s on s.id = ms.site_id
join public.organizations o on o.id = s.organization_id
left join public.user_profiles up on up.id = ms.user_id
order by ms.created_at desc;
```

소속이 없는 관리자 후보를 찾는다.

```sql
select
  up.id,
  up.email,
  up.display_name
from public.user_profiles up
left join public.organization_members om on om.user_id = up.id
where om.id is null
order by up.email;
```

## 운영 체크리스트

- 기업 `slug`는 중복되지 않아야 한다.
- 모든 운영 사이트는 정확한 `organization_id`를 가져야 한다.
- 회사 관리자 계정은 `organization_members`에 있어야 한다.
- 마스터 계정은 Supabase Auth `app_metadata.role`로 지정한다.
- 일반 미션 참여자는 기업 멤버로 넣지 않는다.
- `/admin` 접속 후 회사 필터에서 데이터가 섞이지 않는지 확인한다.

## 문제 해결

| 증상 | 확인할 항목 |
|---|---|
| 회사 관리자가 `/admin`에 접근하지 못함 | `user_profiles.id`가 Supabase Auth `auth.users.id`와 같은지, `organization_members`에 해당 `user_id`가 있는지 확인 |
| 회사 필터가 비어 있음 | 해당 계정의 `organization_members.organization_id`가 실제 `organizations.id`와 연결되는지 확인 |
| 다른 회사 데이터가 보임 | `mission_sessions.site_id`가 잘못된 `sites.organization_id`로 연결됐는지 확인 |
| 마스터가 전체 데이터를 못 봄 | Supabase Auth App Metadata의 `role`이 `platform_master` 또는 `admin`인지 확인 |
