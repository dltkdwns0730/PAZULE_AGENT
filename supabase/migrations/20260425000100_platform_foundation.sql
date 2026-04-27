create table if not exists public.organizations (
  id text primary key,
  name varchar(160) not null,
  slug varchar(80) not null unique,
  created_at timestamptz not null
);

create table if not exists public.user_profiles (
  id text primary key,
  display_name varchar(120),
  email varchar(320),
  created_at timestamptz not null
);

create index if not exists ix_user_profiles_email
  on public.user_profiles (email);

create table if not exists public.organization_members (
  id text primary key,
  organization_id text not null references public.organizations(id),
  user_id text not null references public.user_profiles(id),
  role varchar(40) not null,
  created_at timestamptz not null,
  constraint uq_org_member unique (organization_id, user_id)
);

create table if not exists public.sites (
  id text primary key,
  organization_id text not null references public.organizations(id),
  slug varchar(80) not null unique,
  name varchar(160) not null,
  latitude double precision not null,
  longitude double precision not null,
  radius_meters integer not null,
  is_active boolean not null,
  created_at timestamptz not null
);

create table if not exists public.missions (
  id text primary key,
  site_id text not null references public.sites(id),
  mission_type varchar(40) not null,
  answer varchar(160) not null,
  hint text not null,
  vqa_hints jsonb not null,
  is_active boolean not null,
  created_at timestamptz not null
);

create table if not exists public.mission_sessions (
  id text primary key,
  legacy_mission_id varchar(80) unique,
  user_id text not null references public.user_profiles(id),
  site_id text not null references public.sites(id),
  mission_type varchar(40) not null,
  answer varchar(160) not null,
  hint text not null,
  status varchar(40) not null,
  latest_judgment jsonb,
  created_at timestamptz not null,
  expires_at timestamptz not null
);

create table if not exists public.coupons (
  id text primary key,
  code varchar(32) not null unique,
  mission_session_id text references public.mission_sessions(id),
  user_id text not null references public.user_profiles(id),
  status varchar(40) not null,
  discount_rule varchar(120) not null,
  issued_at timestamptz not null,
  expires_at timestamptz not null,
  redeemed_at timestamptz,
  partner_pos_id varchar(120)
);

create table if not exists public.mission_events (
  id text primary key,
  mission_session_id text references public.mission_sessions(id),
  user_id text references public.user_profiles(id),
  event_type varchar(80) not null,
  payload jsonb not null,
  created_at timestamptz not null
);

create table if not exists public.lead_submissions (
  id text primary key,
  organization_name varchar(160) not null,
  contact_name varchar(120) not null,
  email varchar(320) not null,
  message text,
  created_at timestamptz not null
);
