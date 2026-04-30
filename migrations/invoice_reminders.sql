-- BigDogg payment-reminder cron tracking table.
-- Tracks how many automatic ZZP'er-facing nudges we have sent for an invoice.
-- This is separate from invoices.reminder_count, which tracks user-triggered
-- client-facing reminder emails (POST /api/v1/invoices/{id}/reminder).

create table if not exists public.invoice_reminders (
    invoice_id      uuid primary key references public.invoices(id) on delete cascade,
    reminder_count  int  not null default 0,
    last_sent_at    timestamptz
);

create index if not exists invoice_reminders_count_idx
    on public.invoice_reminders (reminder_count);
