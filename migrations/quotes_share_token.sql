-- Public share token for quotes. The recipient hits a link with this token
-- (https://bigdogg.nl/#/q/<token>) to view the quote and accept/decline
-- without needing a BigDogg account.
--
-- Tokens are unguessable UUIDs. Tokens never expire — losing the token is
-- like losing a shared file link.

alter table public.quotes
  add column if not exists share_token uuid default uuid_generate_v4() unique;

-- Backfill any existing rows that were created before this column existed.
update public.quotes
set share_token = uuid_generate_v4()
where share_token is null;

create index if not exists quotes_share_token_idx
    on public.quotes (share_token);
