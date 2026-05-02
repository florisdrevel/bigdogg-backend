-- BigDogg file_imports — audit log of imported PDF / image files.
-- One row per uploaded file (per import_invoices / import_expenses run).
-- Lets the profile screen show "Imported files" with filename, type,
-- date, record count, and final status.

create table if not exists public.file_imports (
    id              uuid primary key default uuid_generate_v4(),
    user_id         uuid not null references auth.users(id) on delete cascade,
    filename        text not null,
    import_type     text not null check (import_type in ('invoice', 'expense')),
    records_imported  int default 0,
    records_duplicate int default 0,
    records_failed    int default 0,
    status          text not null check (status in ('success', 'partial', 'failed')),
    error_message   text,
    imported_at     timestamptz default now()
);

create index if not exists file_imports_user_id_idx
    on public.file_imports (user_id);
create index if not exists file_imports_imported_at_idx
    on public.file_imports (imported_at desc);

alter table public.file_imports enable row level security;

drop policy if exists "Users manage own file_imports" on public.file_imports;
create policy "Users manage own file_imports"
    on public.file_imports
    for all
    using  (auth.uid() = user_id)
    with check (auth.uid() = user_id);
