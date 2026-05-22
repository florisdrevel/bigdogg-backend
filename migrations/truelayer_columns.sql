-- TrueLayer Open Banking — per-user state columns on user_profiles.
-- Safe to run multiple times.
--
-- The bank_transactions cache table and bank_transaction_links table
-- (from bank_transactions_cache.sql / bank_transaction_links.sql) are
-- source-agnostic and stay as-is.

alter table public.user_profiles
  add column if not exists tl_access_token       text,
  add column if not exists tl_refresh_token      text,
  add column if not exists tl_token_expires_at   timestamptz,
  add column if not exists tl_connected_at       timestamptz,
  add column if not exists tl_link_state         text,
  add column if not exists tl_provider_id        text;

create index if not exists user_profiles_tl_link_state_idx
  on public.user_profiles (tl_link_state)
  where tl_link_state is not null;
