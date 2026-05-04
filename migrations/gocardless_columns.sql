-- GoCardless Bank Account Data — adds the per-user state columns the
-- new banking router writes to. Safe to run multiple times.

alter table public.user_profiles
  add column if not exists gc_requisition_id text,
  add column if not exists gc_account_ids    jsonb,
  add column if not exists gc_institution_id text,
  add column if not exists gc_connected_at   timestamptz,
  add column if not exists gc_link_state     text;

create index if not exists user_profiles_gc_link_state_idx
  on public.user_profiles (gc_link_state)
  where gc_link_state is not null;
