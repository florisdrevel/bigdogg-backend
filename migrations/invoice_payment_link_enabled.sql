-- Per-invoice toggle for whether the Stripe payment link is sent with
-- that invoice. Defaults true (link included). The user can flip it off
-- on the invoice detail screen. Idempotent.

alter table public.invoices
  add column if not exists payment_link_enabled boolean default true;
