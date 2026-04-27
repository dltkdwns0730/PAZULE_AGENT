alter table public.mission_sessions
  add column if not exists max_submissions integer not null default 3;

alter table public.mission_sessions
  add column if not exists coupon_code varchar(32);

alter table public.mission_sessions
  alter column max_submissions drop default;

create table if not exists public.mission_submissions (
  id text primary key,
  mission_session_id text not null references public.mission_sessions(id),
  image_hash varchar(128) not null,
  result_summary jsonb not null,
  submitted_at timestamptz not null
);

create index if not exists ix_mission_submission_session_hash
  on public.mission_submissions (mission_session_id, image_hash);

alter table public.coupons
  add column if not exists description text not null default '';

alter table public.coupons
  add column if not exists mission_type varchar(40) not null default '';

alter table public.coupons
  add column if not exists answer varchar(160) not null default '';

alter table public.coupons
  add column if not exists partner_id varchar(120);

alter table public.coupons
  alter column description drop default;

alter table public.coupons
  alter column mission_type drop default;

alter table public.coupons
  alter column answer drop default;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'uq_coupon_mission_session'
      and conrelid = 'public.coupons'::regclass
  ) then
    alter table public.coupons
      add constraint uq_coupon_mission_session unique (mission_session_id);
  end if;
end $$;

create unique index if not exists uq_coupon_user_answer_active
  on public.coupons (user_id, answer)
  where status in ('issued', 'redeemed');
