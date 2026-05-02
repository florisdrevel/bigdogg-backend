-- Quotes/quote_lines RLS — service role full-access (covers all backend
-- writes from FastAPI), authenticated users limited to their own rows.
-- Fixes "new row violates row-level security policy for table quotes"
-- when force-row-level-security is on for these tables.

alter table public.quotes        enable row level security;
alter table public.quote_lines   enable row level security;

drop policy if exists "service role full access on quotes" on public.quotes;
create policy "service role full access on quotes"
    on public.quotes
    for all
    to service_role
    using (true)
    with check (true);

drop policy if exists "service role full access on quote_lines" on public.quote_lines;
create policy "service role full access on quote_lines"
    on public.quote_lines
    for all
    to service_role
    using (true)
    with check (true);

drop policy if exists "Users manage own quotes" on public.quotes;
create policy "Users manage own quotes"
    on public.quotes
    for all
    to authenticated
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

drop policy if exists "Users manage own quote_lines" on public.quote_lines;
create policy "Users manage own quote_lines"
    on public.quote_lines
    for all
    to authenticated
    using (
        exists (
            select 1 from public.quotes q
            where q.id = quote_lines.quote_id
              and q.user_id = auth.uid()
        )
    )
    with check (
        exists (
            select 1 from public.quotes q
            where q.id = quote_lines.quote_id
              and q.user_id = auth.uid()
        )
    );
