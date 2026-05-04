-- Links a Tink transaction id to either an existing invoice
-- (income → "betaling van factuur"), an existing expense
-- (outgoing → zakelijke kosten), or the magic 'private' sentinel
-- ("not business, ignore"). Suggested_* are tentative matches the
-- backend computes automatically; the user can confirm them in one
-- tap, which converts them into the firm 'invoice'/'expense' types.
--
-- Idempotent — run any number of times.

create table if not exists public.bank_transaction_links (
  id          uuid primary key default uuid_generate_v4(),
  user_id     uuid not null references auth.users(id) on delete cascade,
  tx_id       text not null,                              -- Tink transaction id
  link_type   text not null,                              -- 'invoice' | 'expense' | 'private' | 'suggested_invoice' | 'suggested_expense'
  linked_id   uuid,                                       -- invoice or expense id (null for 'private')
  auto        boolean default false,                      -- true when the matcher created the link without user input
  created_at  timestamptz default now(),
  updated_at  timestamptz default now()
);

-- One link per (user, tx). New attempts upsert in place.
create unique index if not exists bank_tx_links_user_tx_uniq
  on public.bank_transaction_links (user_id, tx_id);

create index if not exists bank_tx_links_user_idx
  on public.bank_transaction_links (user_id);

alter table public.bank_transaction_links enable row level security;

drop policy if exists "users see own bank links"     on public.bank_transaction_links;
drop policy if exists "users insert own bank links"  on public.bank_transaction_links;
drop policy if exists "users update own bank links"  on public.bank_transaction_links;
drop policy if exists "users delete own bank links"  on public.bank_transaction_links;

create policy "users see own bank links"     on public.bank_transaction_links
  for select using (auth.uid() = user_id);
create policy "users insert own bank links"  on public.bank_transaction_links
  for insert with check (auth.uid() = user_id);
create policy "users update own bank links"  on public.bank_transaction_links
  for update using (auth.uid() = user_id);
create policy "users delete own bank links"  on public.bank_transaction_links
  for delete using (auth.uid() = user_id);
