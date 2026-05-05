-- Accountant portal — read-only access for an accountant to one or
-- more BigDogg-user accounts.
--
-- Two new tables:
--   accountant_invites   — pending invitations from a BigDogg user to an
--                          accountant (by email). Token-gated; one-shot.
--   accountant_clients   — confirmed link from accountant_id to a
--                          user_id. RLS on the data tables checks this
--                          to gate read access.
--
-- Idempotent — run any number of times.

create table if not exists public.accountant_invites (
  token       uuid primary key default uuid_generate_v4(),
  user_id     uuid not null references auth.users(id) on delete cascade,
  email       text not null,
  used        boolean default false,
  expires_at  timestamptz default (now() + interval '14 days'),
  created_at  timestamptz default now()
);

create index if not exists accountant_invites_email_idx
  on public.accountant_invites (lower(email));
create index if not exists accountant_invites_user_idx
  on public.accountant_invites (user_id);


create table if not exists public.accountant_clients (
  id              uuid primary key default uuid_generate_v4(),
  accountant_id   uuid not null references auth.users(id) on delete cascade,
  user_id         uuid not null references auth.users(id) on delete cascade,
  status          text not null default 'active',  -- 'active' | 'revoked'
  created_at      timestamptz default now(),
  revoked_at      timestamptz
);

create unique index if not exists accountant_clients_pair_uniq
  on public.accountant_clients (accountant_id, user_id);
create index if not exists accountant_clients_accountant_idx
  on public.accountant_clients (accountant_id);
create index if not exists accountant_clients_user_idx
  on public.accountant_clients (user_id);


-- ── RLS on the new tables ──────────────────────────────────────
alter table public.accountant_invites  enable row level security;
alter table public.accountant_clients  enable row level security;

drop policy if exists "users see own invites"     on public.accountant_invites;
drop policy if exists "users insert own invites"  on public.accountant_invites;
drop policy if exists "users delete own invites"  on public.accountant_invites;

create policy "users see own invites"    on public.accountant_invites
  for select using (auth.uid() = user_id);
create policy "users insert own invites" on public.accountant_invites
  for insert with check (auth.uid() = user_id);
create policy "users delete own invites" on public.accountant_invites
  for delete using (auth.uid() = user_id);

drop policy if exists "users see own accountants"      on public.accountant_clients;
drop policy if exists "accountants see own clients"    on public.accountant_clients;
drop policy if exists "users update own accountants"   on public.accountant_clients;
drop policy if exists "accountants insert own"         on public.accountant_clients;

create policy "users see own accountants"     on public.accountant_clients
  for select using (auth.uid() = user_id);
create policy "accountants see own clients"   on public.accountant_clients
  for select using (auth.uid() = accountant_id);
create policy "users update own accountants"  on public.accountant_clients
  for update using (auth.uid() = user_id);
create policy "accountants insert own"        on public.accountant_clients
  for insert with check (auth.uid() = accountant_id);


-- ── Read-only access for accountants on user data tables ───────
-- An accountant who has an `active` row in accountant_clients gets
-- SELECT access to that user's invoices, expenses, investments,
-- clients, products, projects, and overview-driving rows.
--
-- We layer ADDITIONAL "select" policies; the existing owner policies
-- are unchanged. Postgres ORs RLS policies, so the user keeps full
-- access AND their accountant gets read.

drop policy if exists "accountant reads invoices"     on public.invoices;
drop policy if exists "accountant reads invoice_lines" on public.invoice_lines;
drop policy if exists "accountant reads expenses"     on public.expenses;
drop policy if exists "accountant reads investments"  on public.investments;
drop policy if exists "accountant reads clients"      on public.clients;
drop policy if exists "accountant reads products"     on public.products;
drop policy if exists "accountant reads projects"     on public.projects;
drop policy if exists "accountant reads quotes"       on public.quotes;
drop policy if exists "accountant reads quote_lines"  on public.quote_lines;

create policy "accountant reads invoices" on public.invoices
  for select using (
    exists (
      select 1 from public.accountant_clients ac
      where ac.accountant_id = auth.uid()
        and ac.user_id = invoices.user_id
        and ac.status = 'active'
    )
  );

create policy "accountant reads invoice_lines" on public.invoice_lines
  for select using (
    exists (
      select 1 from public.accountant_clients ac
      join public.invoices i on i.id = invoice_lines.invoice_id
      where ac.accountant_id = auth.uid()
        and ac.user_id = i.user_id
        and ac.status = 'active'
    )
  );

create policy "accountant reads expenses" on public.expenses
  for select using (
    exists (
      select 1 from public.accountant_clients ac
      where ac.accountant_id = auth.uid()
        and ac.user_id = expenses.user_id
        and ac.status = 'active'
    )
  );

create policy "accountant reads investments" on public.investments
  for select using (
    exists (
      select 1 from public.accountant_clients ac
      where ac.accountant_id = auth.uid()
        and ac.user_id = investments.user_id
        and ac.status = 'active'
    )
  );

create policy "accountant reads clients" on public.clients
  for select using (
    exists (
      select 1 from public.accountant_clients ac
      where ac.accountant_id = auth.uid()
        and ac.user_id = clients.user_id
        and ac.status = 'active'
    )
  );

create policy "accountant reads products" on public.products
  for select using (
    exists (
      select 1 from public.accountant_clients ac
      where ac.accountant_id = auth.uid()
        and ac.user_id = products.user_id
        and ac.status = 'active'
    )
  );

create policy "accountant reads projects" on public.projects
  for select using (
    exists (
      select 1 from public.accountant_clients ac
      where ac.accountant_id = auth.uid()
        and ac.user_id = projects.user_id
        and ac.status = 'active'
    )
  );

create policy "accountant reads quotes" on public.quotes
  for select using (
    exists (
      select 1 from public.accountant_clients ac
      where ac.accountant_id = auth.uid()
        and ac.user_id = quotes.user_id
        and ac.status = 'active'
    )
  );

create policy "accountant reads quote_lines" on public.quote_lines
  for select using (
    exists (
      select 1 from public.accountant_clients ac
      join public.quotes q on q.id = quote_lines.quote_id
      where ac.accountant_id = auth.uid()
        and ac.user_id = q.user_id
        and ac.status = 'active'
    )
  );
