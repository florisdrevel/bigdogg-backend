-- Per-user invoice/quote color preference. Hex strings like "#1B3A4B".
-- Null falls back to the BigDogg defaults (TEAL primary + GOLD accent).

alter table public.user_profiles
  add column if not exists invoice_primary_color  text,
  add column if not exists invoice_accent_color   text;
