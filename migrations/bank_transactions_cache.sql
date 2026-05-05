-- Cache table for transactions, regardless of source (Tink, MT940 file
-- import, CAMT.053 file import). One row per unique transaction; the
-- matcher reads from here so it works even when Tink is unreachable
-- (sandbox token expired, no PSD2 connection at all, etc).
--
-- Idempotent — run any number of times.

create table if not exists public.bank_transactions (
  id            uuid primary key default uuid_generate_v4(),
  user_id       uuid not null references auth.users(id) on delete cascade,
  external_id   text not null,                 -- Tink id, MT940 ref, CAMT EntryRef
  source        text not null,                 -- 'tink' | 'mt940' | 'camt053'
  date          date,
  amount        numeric(12, 2),                -- positive = incoming, negative = outgoing
  currency      text default 'EUR',
  description   text,
  merchant      text,
  account_iban  text,
  raw           jsonb,
  imported_at   timestamptz default now()
);

-- One transaction per (user, external_id) — repeated imports of the
-- same statement file are a no-op.
create unique index if not exists bank_transactions_user_extid_uniq
  on public.bank_transactions (user_id, external_id);

create index if not exists bank_transactions_user_date_idx
  on public.bank_transactions (user_id, date desc);

alter table public.bank_transactions enable row level security;

drop policy if exists "users see own bank tx"     on public.bank_transactions;
drop policy if exists "users insert own bank tx"  on public.bank_transactions;
drop policy if exists "users update own bank tx"  on public.bank_transactions;
drop policy if exists "users delete own bank tx"  on public.bank_transactions;

create policy "users see own bank tx"     on public.bank_transactions
  for select using (auth.uid() = user_id);
create policy "users insert own bank tx"  on public.bank_transactions
  for insert with check (auth.uid() = user_id);
create policy "users update own bank tx"  on public.bank_transactions
  for update using (auth.uid() = user_id);
create policy "users delete own bank tx"  on public.bank_transactions
  for delete using (auth.uid() = user_id);
