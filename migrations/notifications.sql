-- In-app notifications. Inserted server-side when something noteworthy
-- happens (invoice paid, quote accepted/declined, client onboarded).
-- The Flutter app polls /api/v1/notifications and shows unread ones in
-- a bell-icon dropdown on the dashboard.

create table if not exists public.notifications (
    id          uuid primary key default uuid_generate_v4(),
    user_id     uuid not null references auth.users(id) on delete cascade,
    -- Stable enum-ish identifier so the frontend can pick an icon /
    -- route the user somewhere on tap. Add new types as needed.
    type        text not null,
    title       text not null,
    body        text,
    -- Free-form payload (e.g. {"invoice_id": "..."}). Frontend uses it
    -- to deep-link to the relevant detail screen on tap.
    data        jsonb,
    read_at     timestamptz,
    created_at  timestamptz default now()
);

create index if not exists notifications_user_id_idx
    on public.notifications (user_id, created_at desc);
create index if not exists notifications_unread_idx
    on public.notifications (user_id) where read_at is null;

-- Service role bypass (FastAPI inserts) + authenticated users can only
-- see their own notifications.
alter table public.notifications enable row level security;

drop policy if exists "service role full access on notifications" on public.notifications;
create policy "service role full access on notifications"
    on public.notifications
    for all
    to service_role
    using (true)
    with check (true);

drop policy if exists "Users manage own notifications" on public.notifications;
create policy "Users manage own notifications"
    on public.notifications
    for all
    to authenticated
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);
