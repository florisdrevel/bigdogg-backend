-- Per-line product reference on invoice_lines and quote_lines, so the
-- hours calculation can resolve `unit` from the actual product instead
-- of having to match the (often-edited) description against product
-- names. Existing rows get NULL — they continue to fall back to the
-- description-based resolution.
--
-- Idempotent — run any number of times.

alter table public.invoice_lines
  add column if not exists product_id uuid
    references public.products(id) on delete set null;

create index if not exists invoice_lines_product_id_idx
  on public.invoice_lines (product_id)
  where product_id is not null;

alter table public.quote_lines
  add column if not exists product_id uuid
    references public.products(id) on delete set null;

create index if not exists quote_lines_product_id_idx
  on public.quote_lines (product_id)
  where product_id is not null;
