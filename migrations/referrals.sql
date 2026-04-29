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

-- RLS — backend service role bypasses RLS, so no SELECT policies needed
-- but we enable RLS to keep tables locked down from anon/auth keys.
alter table public.referrals enable row level security;
alter table public.referral_signups enable row level security;
