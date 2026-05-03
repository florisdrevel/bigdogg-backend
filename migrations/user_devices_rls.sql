-- RLS policies for user_devices. Without these, the FastAPI backend
-- (using service_role) can't INSERT new device rows even though the
-- table exists, and the new-device login email never fires.
--
-- Mirrors the same pattern used for quotes/quote_lines.

alter table public.user_devices enable row level security;

drop policy if exists "service role full access on user_devices" on public.user_devices;
create policy "service role full access on user_devices"
    on public.user_devices
    for all
    to service_role
    using (true)
    with check (true);

drop policy if exists "Users read own user_devices" on public.user_devices;
create policy "Users read own user_devices"
    on public.user_devices
    for select
    to authenticated
    using (auth.uid() = user_id);
