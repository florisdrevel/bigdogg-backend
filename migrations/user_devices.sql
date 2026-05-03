-- Tracks the devices a user has logged in from. Powers the
-- "new device login notification" email.
--
-- Fingerprint is derived from User-Agent (browser+OS), stable across
-- browser-version updates. Same person, same device → same fingerprint.

create table if not exists public.user_devices (
    id           uuid primary key default uuid_generate_v4(),
    user_id      uuid not null references auth.users(id) on delete cascade,
    fingerprint  text not null,
    user_agent   text,
    last_ip      text,
    first_seen   timestamptz default now(),
    last_seen    timestamptz default now(),
    unique (user_id, fingerprint)
);

create index if not exists user_devices_user_id_idx
    on public.user_devices (user_id);
