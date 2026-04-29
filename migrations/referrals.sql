-- Referral system tables.
-- Run this in the Supabase SQL editor before deploying the referrals backend.

create extension if not exists pgcrypto;

-- Each user has at most one referral code.
create table if not exists public.referrals (
    id uuid primary key default gen_random_uuid(),
    referrer_user_id uuid not null references auth.users(id) on delete cascade,
    code text not null unique,
    created_at timestamptz not null default now(),
    unique (referrer_user_id)
);

create index if not exists referrals_code_idx on public.referrals (code);

-- One row per signup that came in via a referral link.
create table if not exists public.referral_signups (
    id uuid primary key default gen_random_uuid(),
    referrer_code text not null,
    referrer_user_id uuid references auth.users(id) on delete set null,
    new_user_id uuid not null references auth.users(id) on delete cascade,
    created_at timestamptz not null default now(),
    converted boolean not null default false,
    converted_at timestamptz,
    unique (new_user_id)
);

create index if not exists referral_signups_referrer_code_idx
    on public.referral_signups (referrer_code);
create index if not exists referral_signups_new_user_id_idx
    on public.referral_signups (new_user_id);

-- RLS is intentionally DISABLED on these tables.
--
-- Why: the backend FastAPI router enforces auth (extracts user_id from the
-- JWT) before every insert/select. supabase-py's auth.get_user(token) call
-- switches the client to operate as the authenticated user for subsequent
-- requests, so service_role does NOT bypass RLS here — leaving RLS on with
-- no policies means every insert hits a 42501 row-level security violation.
-- Disabling RLS lets the backend's own auth checks be the only gate, which
-- matches the pattern the other operational tables (subscriptions, invoices,
-- expenses) use.
alter table public.referrals disable row level security;
alter table public.referral_signups disable row level security;
