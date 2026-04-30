-- BigDogg Offertes (quotes) feature.
-- Mirrors the invoices schema with quote-specific names. Each quote can
-- be converted into an invoice once accepted.

create table if not exists public.quotes (
    id              uuid primary key default uuid_generate_v4(),
    user_id         uuid not null references auth.users(id) on delete cascade,
    client_id       uuid references public.clients(id) on delete set null,
    project_id      uuid references public.projects(id) on delete set null,
    client_name     text,
    client_email    text,
    client_company  text,
    quote_number    text not null,
    quote_date      date not null default current_date,
    valid_until     date,
    status          text not null default 'draft', -- draft | sent | accepted | declined | converted
    subtotal_ex_btw numeric(12,2) default 0,
    btw_amount      numeric(12,2) default 0,
    total_incl_btw  numeric(12,2) default 0,
    notes           text,
    converted_invoice_id uuid references public.invoices(id) on delete set null,
    created_at      timestamptz default now(),
    updated_at      timestamptz default now()
);

create index if not exists quotes_user_id_idx  on public.quotes (user_id);
create index if not exists quotes_status_idx   on public.quotes (status);

create table if not exists public.quote_lines (
    id                  uuid primary key default uuid_generate_v4(),
    quote_id            uuid not null references public.quotes(id) on delete cascade,
    description         text,
    quantity            numeric(12,2) default 1,
    unit_price_ex_btw   numeric(12,2) default 0,
    btw_rate            int default 21,
    line_total_ex_btw   numeric(12,2) default 0,
    unit                text default 'fixed',
    created_at          timestamptz default now()
);

create index if not exists quote_lines_quote_id_idx on public.quote_lines (quote_id);
