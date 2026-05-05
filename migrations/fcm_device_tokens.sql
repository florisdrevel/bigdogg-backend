-- FCM device-token registry for OS-level push (Firebase Cloud Messaging).
-- Each row is one phone-OS pair the user has signed in on. We fan out
-- pushes to all rows for a given user so multiple devices stay in sync.

create table if not exists public.fcm_device_tokens (
  id          uuid primary key default uuid_generate_v4(),
  user_id     uuid not null references auth.users(id) on delete cascade,
  fcm_token   text not null,
  platform    text not null,                  -- 'android' | 'ios' | 'web'
  device_name text,
  last_seen   timestamptz default now(),
  created_at  timestamptz default now()
);

-- Same token registered twice for the same user is a no-op.
create unique index if not exists fcm_device_tokens_user_token_uniq
  on public.fcm_device_tokens (user_id, fcm_token);

create index if not exists fcm_device_tokens_user_idx
  on public.fcm_device_tokens (user_id);

alter table public.fcm_device_tokens enable row level security;

drop policy if exists "users see own fcm tokens"     on public.fcm_device_tokens;
drop policy if exists "users insert own fcm tokens"  on public.fcm_device_tokens;
drop policy if exists "users update own fcm tokens"  on public.fcm_device_tokens;
drop policy if exists "users delete own fcm tokens"  on public.fcm_device_tokens;

create policy "users see own fcm tokens"     on public.fcm_device_tokens
  for select using (auth.uid() = user_id);
create policy "users insert own fcm tokens"  on public.fcm_device_tokens
  for insert with check (auth.uid() = user_id);
create policy "users update own fcm tokens"  on public.fcm_device_tokens
  for update using (auth.uid() = user_id);
create policy "users delete own fcm tokens"  on public.fcm_device_tokens
  for delete using (auth.uid() = user_id);
