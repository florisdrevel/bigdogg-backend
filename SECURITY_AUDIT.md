# BigDogg backend — IDOR & multi-tenant security audit

**Branch**: `security/idor-audit`
**Scope**: every route under `/api/v1/*` plus `/o/{token}`, `/a/{token}`, `/q/{token}`, `/cron/*`, and `/health`.
**Method**: read-only static review of every router in `app/routers/` against the threat model that the backend talks to Postgres via the Supabase service-role key, so RLS is bypassed and tenant isolation depends 100% on application code adding `.eq("user_id", user_id)` to every query.

---

## Top-line findings

| # | Severity | Finding | Where |
|---|---|---|---|
| 1 | **CONFIRMED IDOR** | Any authenticated user can mark **any other user's invoice as paid** by linking a bank transaction to a victim's invoice id. Also lets attacker un-pay a victim's invoice by unlinking. | `banking.py:1085` (`POST /banking/transactions/{tx_id}/link`) → `banking.py:726` (`_mark_invoice_paid`) |
| 2 | **LIKELY IDOR** | `DELETE /clients/{client_id}` reads/updates `invoices` filtered only by `client_id` with no `user_id` scope. Caller can probe foreign-user client_ids and null out the `client_id` on their invoices. | `clients.py:111` |
| 3 | **LIKELY IDOR** | `POST /subscription/webhook` falls back to unsigned `json.loads(payload)` when `stripe_webhook_secret` is missing or `"whsec_placeholder"`. Forged event can grant any user paid status. | `subscription.py:1590-1600` (paired with `subscriptions.update(...).eq("user_id", metadata.user_id)`) |
| 4 | LIKELY (info disclosure) | `GET /subscription/activated?user_id=…` is unauthenticated and returns paid/inactive — enables user-UUID enumeration to identify paying customers. | `subscription.py:355` |
| 5 | Operational | Cron secret compared with `!=` (timing-leak vulnerable) and falls back to a **hard-coded literal** `"bigdogg-cron-2026"` if env var unset. | `config.py:21` + 6 cron handlers |
| 6 | Operational | Several invoice/quote update paths (reminder_count, status='sent') omit `.eq("user_id", user_id)` on the trailing update. Gated today by parent `.single()`, but defense-in-depth missing. | `invoices.py:321`, `email.py:253` |
| 7 | Operational | Bearer JWT accepted as `?token=` query param on PDF / report download routes — ends up in logs, browser history, Referer. | `pdf.py:36`, `reports.py:261`, `annual_report.py:643`, `quotes.py:397` |
| 8 | Operational | `project_id` accepted in body (hours, expenses, invoices) without verifying it belongs to caller. Cross-tenant **linking** only, not data leak. | `hours.py:230`, `expenses.py:88`, `invoices.py:95` |
| 9 | Operational | Quote `share_token` and client-onboarding `client_invites.token` have **no expiry** — share links work forever. | `quotes.py:692`, `clients.py:153` |
| 10 | Operational | Several `PUT`/`DELETE` paths return 200 when the row doesn't belong to the caller (no-op) — leaks "row exists" vs "not yours". | `products.py:102`, `expenses.py:323`, `hours.py:254`, `investments.py:85` |
| 11 | Operational | `POST /support` is unauthenticated and has no rate limit → email-bomb spam vector. | `support.py:22` |

---

## Authentication mechanism — verdict

**Cryptographic verification: SAFE.**

Every router derives `user_id` from `supabase.auth.get_user(token).user.id`. This call goes to Supabase Auth's GoTrue server, which validates the JWT signature, expiry, and issuer server-side using the project's JWT secret. There is **no** local-only decode path, no `jwt.decode(token, verify=False)` anywhere in the codebase, and no router accepts `user_id` from a request body / query / header in place of the token.

The pattern `get_user_id(request)` is duplicated as a local helper in 24 router files (auth.py, products.py, clients.py, invoices.py, expenses.py, ai.py, …) — operationally a code-smell but not a security issue.

Per-handler exceptions to "Authorization: Bearer" verification:
- `pdf.py:36`, `reports.py:261`, `annual_report.py:643`, `quotes.py:397` — accept the JWT as `?token=` query parameter. Still calls `supabase.auth.get_user(token)` so cryptographic verification is preserved, but URL-borne JWTs leak into logs/Referer (operational, not auth-bypass).

Verdict: **JWT auth chain is sound. No CONFIRMED auth-bypass.**

---

## /cron/* secret comparison — verdict

**Operational issue: timing-attack vulnerable + hard-coded default.**

Six cron-protected endpoints:
- `POST /api/v1/subscription/cron/cancellation-reminders` — `subscription.py:884`
- `GET  /api/v1/subscription/admin/churn-stats` — `subscription.py:1008`
- `POST /api/v1/subscription/cron/trial-expiry` — `subscription.py:1249`
- `POST /api/v1/subscription/cron/btw-reminders` — `subscription.py:1490`
- `POST /api/v1/reports/cron/annual` — `annual_report.py:690`
- `POST /api/v1/reminders/cron/payment-reminders` — `reminders.py:173`

All six compare via plain `if auth != settings.cron_secret` — non-constant-time, leaks information byte-by-byte. Fix: `hmac.compare_digest`.

`config.py:21` defaults `cron_secret` to the literal `"bigdogg-cron-2026"` when env var is unset. Any non-prod deploy that forgets to set `CRON_SECRET` is wide open — and the literal is in the public git history (rotated in step 1 of the earlier audit, but the default is still in code). Fix: refuse to boot if `CRON_SECRET` is unset.

---

## Share-link & accountant token security — verdict

**SAFE in current implementation, with two operational gaps.**

| Token | Generation | Scope | Expiry | Verdict |
|---|---|---|---|---|
| `accountant_invites.token` | DB-default UUID | Owner-scoped via `_resolve_portal_token` then `.eq("user_id", owner_id)` everywhere | 7 days (`_PORTAL_TTL_DAYS`) | SAFE |
| `quotes.share_token` | `uuid.uuid4()` server-side | Single quote only via `share_token` lookup | **None** — link works forever | Operational gap |
| `client_invites.token` | DB-default UUID | New client added under the inviting user only | **None** | Operational gap |

The public-preview routes in `share.py` (`/o/{token}`, `/a/{token}`, `/q/{token}`) only leak the inviter's business name + (for quotes) the total — acceptable for OG-card scrapers like WhatsApp/Slack. No tokens are enumerable (no list endpoint exposes them across users).

Accountant invite revocation flips `used=true` (or hard-deletes); subsequent `_resolve_portal_token` calls 403. Extension is owner-scoped. First-access email is implemented (from the earlier step 8 work).

---

## Per-endpoint inventory

### Legend
- **scope**: how the handler ties the resource back to the authenticated user
- **child OK?** column applies only to child-table writes (invoice_lines, quote_lines, bank_transaction_links)

### auth.py — `/api/v1/auth`

| Method | Path | tables | scope | child OK? | verdict |
|---|---|---|---|---|---|
| POST | /register | referrals, referral_signups | n/a (public signup) | n/a | SAFE |
| POST | /login | user_devices | user_id from Supabase response | n/a | SAFE |
| POST | /refresh | — | Supabase validates refresh_token | n/a | SAFE |
| POST | /logout | — | n/a | n/a | SAFE |
| POST | /reset-password | — | Supabase sends to email's owner | n/a | SAFE |
| POST | /change-password | — | JWT + current_password re-verify (step 7) | n/a | SAFE |
| DELETE | /delete-account | 19 tenant tables | JWT + current_password; every delete `.eq("user_id", user_id)`; invoice_lines via parent | yes | SAFE |

### products.py — `/api/v1/products`

| Method | Path | tables | scope | verdict |
|---|---|---|---|---|
| GET | / | products | `.eq("user_id", user_id)` | SAFE |
| POST | / | products | user_id from JWT | SAFE |
| PUT | /{product_id} | products | `.eq("id", product_id).eq("user_id", user_id)` | SAFE |
| DELETE | /{product_id} | products | scoped, but returns 200 on foreign id | SAFE (operational) |

### clients.py — `/api/v1/clients`

| Method | Path | tables | scope | verdict |
|---|---|---|---|---|
| GET | / | clients | scoped | SAFE |
| POST | / | clients | scoped | SAFE |
| PUT | /{client_id} | clients | scoped | SAFE |
| **DELETE** | **/{client_id}** | **invoices, clients** | **invoices SELECT and `.update({client_id: null})` filter only on `client_id`, no `.eq("user_id", user_id)`** | **LIKELY IDOR** |
| GET | /onboarding/{token} | client_invites | token-only, server-stored | SAFE (no expiry — operational) |
| POST | /onboarding/{token} | client_invites, clients, notifications | user_id derived from token row, not body | SAFE |
| POST | /invite | client_invites | scoped | SAFE |

### invoices.py — `/api/v1/invoices`

| Method | Path | tables | scope | child OK? | verdict |
|---|---|---|---|---|---|
| GET | / | invoices | scoped | n/a | SAFE |
| GET | /{invoice_id} | invoices, invoice_lines | parent `.single()` gates lines fetch | yes | SAFE |
| POST | / | invoices, invoice_lines, clients, products, user_profiles | clients lookup scoped (step 3); user_id stamped | yes | SAFE |
| PATCH | /{invoice_id}/status | invoices | scoped | n/a | SAFE (status string not validated) |
| POST | /{invoice_id}/reminder | invoices, user_profiles | parent .single() gates; trailing update unscoped | n/a | SAFE-by-gate (operational) |
| DELETE | /{invoice_id} | invoices, invoice_lines | parent scoped, then child by parent id | yes | SAFE |
| PATCH | /{invoice_id} | invoices | scoped, whitelist of fields | n/a | SAFE |

### ai.py — `/api/v1/ai`

| Method | Path | tables | scope | verdict |
|---|---|---|---|---|
| POST | /parse-invoice | products, clients (read) + ai_usage | scoped on both | SAFE |
| POST | /parse-quote | products, clients (read) + ai_usage | scoped on both | SAFE |

### expenses.py — `/api/v1/expenses`

| Method | Path | tables | scope | verdict |
|---|---|---|---|---|
| GET | / | expenses | scoped (signed URLs minted from receipt paths) | SAFE |
| POST | / | expenses | scoped | SAFE |
| POST | /parse-receipt | ai_usage | scoped via quota | SAFE |
| POST | /upload-receipt/{expense_id} | expenses | pre-check + update both scoped (step 5) | SAFE |
| DELETE | /{expense_id} | expenses | scoped (silently 200 on foreign id) | SAFE (operational) |

### overview.py — `/api/v1/overview`

| Method | Path | tables | scope | verdict |
|---|---|---|---|---|
| GET | /quarterly | invoices, expenses | scoped | SAFE |
| GET | /annual | invoices, expenses | scoped | SAFE |

### profile.py — `/api/v1/profile`

| Method | Path | tables | scope | verdict |
|---|---|---|---|---|
| GET | / | user_profiles | `id == user_id` | SAFE |
| POST | / | user_profiles | scoped | SAFE |
| POST | /logo | user_profiles + logos bucket (public) | scoped path | SAFE (logos intentionally public) |

### subscription.py — `/api/v1/subscription`

| Method | Path | tables | scope | verdict |
|---|---|---|---|---|
| GET | /status | subscriptions | scoped | SAFE |
| **GET** | **/activated?user_id=…** | **subscriptions** | **user_id from query string, no auth** | **LIKELY (info disclosure)** — enables paid-user UUID enumeration |
| POST | /checkout | subscriptions | scoped | SAFE |
| POST | /portal | subscriptions | scoped | SAFE |
| GET | /usage-summary | invoices, clients, expenses, subscriptions, cancellation_events | scoped | SAFE |
| POST | /cancel | subscriptions, cancellation_events | scoped | SAFE |
| POST | /reactivate | subscriptions, cancellation_events | scoped | SAFE |
| POST | /cron/cancellation-reminders | subscriptions, cancellation_events, user_profiles | x-cron-secret (`!=` compare) | SAFE-but-timing |
| GET | /admin/churn-stats | cancellation_events | x-cron-secret | SAFE-but-timing |
| POST | /cron/trial-expiry | subscriptions, trial_warning_emails, user_profiles | x-cron-secret | SAFE-but-timing |
| POST | /cron/btw-reminders | subscriptions, user_profiles | x-cron-secret | SAFE-but-timing |
| **POST** | **/webhook** | **subscriptions, expenses, referral_signups** | **fallback to `json.loads(payload)` when secret missing/placeholder; user_id from event metadata** | **LIKELY IDOR — forged event grants any user paid status** |

### pdf.py — `/api/v1/pdf`

| Method | Path | tables | scope | child OK? | verdict |
|---|---|---|---|---|---|
| GET | /{invoice_id} | invoices, invoice_lines, user_profiles | parent scoped (.single()), lines via parent | yes | SAFE (token in URL — operational) |

### email.py — `/api/v1/email`

| Method | Path | tables | scope | child OK? | verdict |
|---|---|---|---|---|---|
| POST | /invoice/{invoice_id} | invoices, invoice_lines, user_profiles | parent scoped; trailing status update unscoped | yes | SAFE-by-gate (operational) |
| POST | /quote/{quote_id} | quotes, quote_lines, user_profiles | parent scoped; status + share_token update | yes | SAFE |

### reports.py — `/api/v1/reports`

| Method | Path | tables | scope | verdict |
|---|---|---|---|---|
| GET | /btw/pdf | invoices, expenses, user_profiles | scoped (token in URL — operational) | SAFE |
| GET | /quarter-detail | invoices, expenses | scoped | SAFE |
| POST | /annual/generate | — | no-op stub; no auth check | SAFE (stub) |

### annual_report.py — `/api/v1/reports`

| Method | Path | tables | scope | verdict |
|---|---|---|---|---|
| GET/HEAD | /annual/pdf | invoices, expenses, hours, invoice_lines, products, investments, user_profiles | scoped (token in URL — operational) | SAFE |
| POST | /cron/annual | per-user across `auth.admin.list_users()` | x-cron-secret (`!=`) | SAFE-but-timing |

### import_invoices.py — mounted under both `/api/v1/invoices` and `/api/v1/expenses`

| Method | Path | tables | scope | verdict |
|---|---|---|---|---|
| POST | /import-invoices | invoices | scoped on duplicate check + insert | SAFE |
| GET | /imported | invoices | scoped | SAFE |
| DELETE | /imported/{invoice_id} | invoices | scoped | SAFE |
| POST | /import-expenses | expenses | scoped | SAFE |

(Mounting on two prefixes is an operational duplication — same handler reachable at two paths, no security impact.)

### payments.py — `/api/v1/payments`

| Method | Path | tables | scope | verdict |
|---|---|---|---|---|
| POST | /connect | user_profiles | scoped | SAFE |
| GET | /connect/dashboard | user_profiles | scoped | SAFE |
| GET | /connect/status | user_profiles | scoped | SAFE |
| POST | /invoice/{invoice_id}/payment-link | invoices, user_profiles | scoped | SAFE |
| POST | /webhook/connect | invoices, stripe_processed_events | signature REQUIRED (step 4 hardening); 500 if missing | SAFE |
| POST | /webhook | subscriptions, invoices, stripe_processed_events | signature REQUIRED | SAFE |

### hours.py — `/api/v1/hours`

| Method | Path | tables | scope | child OK? | verdict |
|---|---|---|---|---|---|
| GET | / | hours, invoices, invoice_lines, products | scoped on all; child via parent | yes | SAFE |
| POST | / | hours | scoped; project_id from body not verified | n/a | SAFE (operational: project_id unchecked) |
| DELETE | /{entry_id} | hours | scoped | n/a | SAFE |

### investments.py — `/api/v1/investments`

| Method | Path | tables | scope | verdict |
|---|---|---|---|---|
| GET | / | investments | scoped | SAFE |
| GET | /annual/{year} | investments | scoped | SAFE |
| POST | / | investments | scoped | SAFE |
| DELETE | /{investment_id} | investments | scoped | SAFE |

### projects.py — `/api/v1/projects`

| Method | Path | tables | scope | verdict |
|---|---|---|---|---|
| GET | / | projects, invoices, expenses, hours, invoice_lines | scoped on all parents | SAFE |
| POST | / | projects | scoped | SAFE |
| PATCH | /{project_id} | projects | scoped | SAFE |
| DELETE | /{project_id} | invoices, expenses, projects | cascade nulls scoped; projects delete scoped | SAFE |

### support.py — `/api/v1/support`

| Method | Path | tables | scope | verdict |
|---|---|---|---|---|
| POST | / | — | public, no rate limit | SAFE (operational: spam vector) |

### reminders.py — `/api/v1/reminders`

| Method | Path | tables | scope | verdict |
|---|---|---|---|---|
| POST | /cron/payment-reminders | invoices, invoice_reminders, user_profiles | x-cron-secret (`!=`) | SAFE-but-timing |

### referrals.py — `/api/v1/referrals`

| Method | Path | tables | scope | verdict |
|---|---|---|---|---|
| POST | /generate | referrals | scoped | SAFE |
| GET | /stats | referrals, referral_signups, subscriptions | scoped | SAFE |

### quotes.py — `/api/v1/quotes`

| Method | Path | tables | scope | child OK? | verdict |
|---|---|---|---|---|---|
| GET | / | quotes | scoped | n/a | SAFE |
| GET | /{quote_id} | quotes, quote_lines | parent scoped, child via parent | yes | SAFE |
| POST | / | quotes, quote_lines, products, clients | clients scoped (step 3); user_id from JWT | yes | SAFE |
| PUT | /{quote_id} | quotes, quote_lines, products, clients | parent + client switch both scoped | yes | SAFE |
| DELETE | /{quote_id} | quote_lines, quotes | parent scoped | yes | SAFE |
| POST | /{quote_id}/convert | quotes, quote_lines, invoices, invoice_lines | parent scoped, new invoice user_id from JWT | yes | SAFE |
| POST/GET | /{quote_id}/pdf | quotes, quote_lines, user_profiles | parent scoped (token in URL — operational) | yes | SAFE |
| GET | /public/{token} | quotes, quote_lines, user_profiles | share_token only; only client-safe fields | n/a | SAFE (no expiry — operational) |
| POST | /public/{token}/accept | quotes, notifications | share_token resolves the only row touched | n/a | SAFE |
| POST | /public/{token}/decline | quotes, notifications | share_token resolves the only row touched | n/a | SAFE |

### banking.py — `/api/v1/banking`

| Method | Path | tables | scope | child OK? | verdict |
|---|---|---|---|---|---|
| POST | /connect | user_profiles | scoped | n/a | SAFE |
| GET | /callback | user_profiles | state matches scope | n/a | SAFE |
| GET | /transactions | user_profiles, bank_transactions, invoices, expenses, investments, bank_transaction_links | scoped on every read; child via parent-id whitelist | yes | SAFE |
| **POST** | **/transactions/{tx_id}/link** | **bank_transaction_links, invoices** | **link insert scoped, but `_mark_invoice_paid(linked_id)` updates invoices with NO user_id check** | **no** | **CONFIRMED IDOR** |
| POST | /transactions/{tx_id}/create-expense | expenses, bank_transaction_links | scoped (creates new owned rows) | yes | SAFE |
| POST | /transactions/{tx_id}/create-investment | investments, bank_transaction_links | scoped | yes | SAFE |
| POST | /import | bank_transactions, links, invoices, expenses, investments | all scoped — but matcher calls the same flawed `_mark_invoice_paid` | yes | SAFE-by-context (helper still risky) |
| GET | /accounts | user_profiles | scoped | n/a | SAFE |
| GET | /status | user_profiles | scoped | n/a | SAFE |
| DELETE | /disconnect | user_profiles | scoped | n/a | SAFE |

### notifications.py — `/api/v1/notifications`

| Method | Path | tables | scope | verdict |
|---|---|---|---|---|
| GET | / | notifications | scoped | SAFE |
| GET | /unread-count | notifications | scoped | SAFE |
| POST | /{notification_id}/read | notifications | scoped | SAFE |
| POST | /read-all | notifications | scoped | SAFE |
| DELETE | /{notification_id} | notifications | scoped | SAFE |

### devices.py — `/api/v1/devices`

| Method | Path | tables | scope | verdict |
|---|---|---|---|---|
| POST | /register-fcm-token | fcm_device_tokens | upsert with JWT user_id | SAFE |
| DELETE | /fcm-token | fcm_device_tokens | scoped | SAFE |

### share.py — root-mounted

| Method | Path | tables | scope | verdict |
|---|---|---|---|---|
| GET | /o/{token} | client_invites, user_profiles | token-only; only business_name exposed | SAFE |
| GET | /a/{token} | accountant_invites, user_profiles | token-only; only business_name exposed | SAFE |
| GET | /q/{token} | quotes, user_profiles | share_token-only; quote number + total + business name | SAFE |

### accountants.py — `/api/v1/accountants`

| Method | Path | tables | scope | child OK? | verdict |
|---|---|---|---|---|---|
| POST | /invite | accountant_invites, user_profiles | scoped | n/a | SAFE |
| GET | /invites | accountant_invites | scoped | n/a | SAFE |
| DELETE | /invites/{token} | accountant_invites | `.eq("user_id", user_id)` | n/a | SAFE |
| POST | /invites/{token}/extend | accountant_invites | scoped | n/a | SAFE |
| GET | /portal/{token}(/years\|/overview\|/invoices\|/expenses\|/btw-breakdown\|/aging\|/investments\|/export.csv\|/hours\|/annual-report.pdf\|/invoices/{id}/pdf) | per-token | `_resolve_portal_token` resolves owner; every query `.eq("user_id", owner_id)`; children via parent (step 5+8) | yes | SAFE |

### bank.py — `/api/v1/bank`

| Method | Path | tables | scope | verdict |
|---|---|---|---|---|
| POST | /parse-statement | ai_usage | scoped via quota; no tenant DB writes | SAFE |

### main.py — root

| Method | Path | verdict |
|---|---|---|
| GET | /health | SAFE |

---

## Prioritized fix list

**Phase 2 should fix in this order.** Items 1–4 are the financial-tenant-isolation work. Items 5–11 are defense-in-depth + operational hardening.

### 1. CONFIRMED IDOR — bank-link can mark any user's invoice paid

- **Where**: `banking.py:1085` (`POST /api/v1/banking/transactions/{tx_id}/link`), which calls `_mark_invoice_paid(linked_id)` at `banking.py:726`.
- **What happens**: User A posts `{"link_type": "invoice", "linked_id": "<User B's invoice UUID>"}`. The link row gets the attacker's `user_id`, but `_mark_invoice_paid` does `supabase.table("invoices").update({"status": "paid"}).eq("id", invoice_id).execute()` with no `user_id` filter. User B's invoice flips to `paid`. The unlink path at `banking.py:1109–1115` flips it back to `sent`, equally without scoping.
- **Fix**: before persisting the link, verify `invoices.id = linked_id AND user_id = caller`. Inside `_mark_invoice_paid`, add `.eq("user_id", user_id)` to the UPDATE and 404 if it changes 0 rows. Same for the un-link side.

### 2. LIKELY IDOR — client delete tampers with foreign invoices

- **Where**: `clients.py:111` (`DELETE /api/v1/clients/{client_id}`).
- **What happens**: The unpaid-invoices probe and the subsequent `invoices.update({"client_id": None}).eq("client_id", client_id)` both omit `.eq("user_id", user_id)`. A caller passing a foreign `client_id` can (a) infer that another user has clients via the probe response, and (b) null out the `client_id` field on the victim's invoices.
- **Fix**: add `.eq("user_id", user_id)` to both invoice queries inside `delete_client`. The `clients` delete is already scoped — keep it.

### 3. LIKELY IDOR — Stripe webhook bypass grants paid status

- **Where**: `subscription.py:1590–1600` (`POST /api/v1/subscription/webhook`).
- **What happens**: If `settings.stripe_webhook_secret` is empty OR equals the literal `"whsec_placeholder"`, signature verification is skipped and `event = json.loads(payload)` is processed as if real. An attacker posts a forged `checkout.session.completed` with `metadata.user_id = <victim>` and `metadata.plan = "yearly"` → `subscriptions.update({"status": "active"}).eq("user_id", metadata.user_id)` runs, granting the victim a paid tier under the attacker's choosing.
- **Fix**: match the pattern already used in `payments.py` after step 4 — refuse to process the webhook (500) when the secret is missing. Never `json.loads(payload)`.

### 4. LIKELY (info disclosure) — `/subscription/activated` enumeration

- **Where**: `subscription.py:355` (`GET /api/v1/subscription/activated?user_id=…`).
- **What happens**: Unauthenticated probe of an arbitrary user_id returns `{"active": true|false, "plan": "monthly"|None}`. An attacker iterating user UUIDs can identify paying customers and their plan. Documented as a polling probe for the native checkout webview, but the design uses raw UUIDs.
- **Fix**: replace the raw `user_id` query param with a short-lived signed nonce returned from `/checkout`. Add a per-IP rate limit at minimum.

### 5. Operational — cron secret timing + hard-coded default

- **Where**: `config.py:21` plus 6 `if auth != settings.cron_secret` comparisons (subscription.py:895/1021/1259/1502, annual_report.py:693, reminders.py:193).
- **Fix**: (a) every comparison → `hmac.compare_digest(auth.encode(), settings.cron_secret.encode())`; (b) `config.py` should refuse to boot if `CRON_SECRET` is missing or equals the literal default.

### 6. Operational — defense-in-depth scoping on trailing updates

- **Where**: `invoices.py:321` (reminder_count) and `email.py:253` (status='sent') update by id only.
- **Fix**: add `.eq("user_id", user_id)` to both. Currently safe because parent `.single()` checks gate access, but a later refactor could lose that guard.

### 7. Operational — tokens in URL query strings

- **Where**: `pdf.py:36`, `reports.py:261`, `annual_report.py:643`, `quotes.py:397`.
- **Fix**: require `Authorization: Bearer` header. Alternatively swap query-string JWT for a short-lived one-shot signed download token issued from a paired POST endpoint.

### 8. Operational — `project_id` in body not verified

- **Where**: `hours.py:230`, `expenses.py:88`, `invoices.py:95`.
- **Fix**: when `project_id` is provided, `SELECT id FROM projects WHERE id = $1 AND user_id = $2` first; 404 if missing.

### 9. Operational — quote share_token / client_invites.token have no expiry

- **Where**: `quotes.py:692`, `clients.py:153`/`168`.
- **Fix**: add `share_token_expires_at` / `expires_at` columns, default 30 days for quotes and 14 days for client invites; enforce in the public lookup.

### 10. Operational — 200 instead of 404 on no-op write

- **Where**: `products.py:102`, `expenses.py:323`, `hours.py:254`, `investments.py:85` DELETEs return 200 regardless of row ownership.
- **Fix**: capture `result.data` length; raise 404 if 0 rows affected. Same for the PUT paths that look up after the eq filter.

### 11. Operational — `/support` no rate limit

- **Where**: `support.py:22`.
- **Fix**: per-IP rate limiter (e.g. `slowapi`); also reject submissions where the body is suspiciously long.

---

## Tables — final scoping status

| Table | Scoping verdict | Notes |
|---|---|---|
| invoices | ⚠ partial | `banking._mark_invoice_paid` (helper) + `clients.delete_client` (route) update without `user_id` filter. Read paths SAFE. |
| invoice_lines | SAFE | Always touched via parent invoice id; parent ownership verified first in every handler. |
| expenses | SAFE | Receipt URLs now signed (step 5). |
| clients | SAFE on its own table; **see invoices issue in client_delete** |
| products | SAFE |
| hours | SAFE | project_id ownership not validated — operational. |
| investments | SAFE |
| projects | SAFE |
| subscriptions | ⚠ webhook fallback can grant `status=active` to any user_id when secret missing |
| quotes | SAFE | share_token has no expiry — operational. |
| quote_lines | SAFE | parent-gated. |
| bank_transactions | SAFE |
| bank_transaction_links | SAFE on writes; but linked invoice_id can trigger the `_mark_invoice_paid` IDOR. |
| invoice_reminders | SAFE |
| referrals / referral_signups | SAFE |
| notifications | SAFE |
| user_devices | SAFE (operational: no expiry/cleanup) |
| fcm_device_tokens | SAFE (operational: prior-owner tokens not cleaned on logout) |
| accountant_invites | SAFE |
| client_invites | SAFE (operational: no expiry) |
| ai_usage | SAFE |
| user_profiles | SAFE (logos bucket public by design) |
| subscription_cancellation_events | SAFE |
| trial_warning_emails | SAFE |
| stripe_processed_events | SAFE (global idempotency table, no tenant data) |
| accountant_portal_access_log | SAFE (write-only audit) |

---

## Recommendation for Phase 2

**STOP here for approval.** When you sign off on the fix list above, Phase 2 should:

1. Introduce one mechanism that makes ownership scoping correct **by construction**: a FastAPI dependency `current_user: User = Depends(verified_user)` that yields the authenticated user object, plus a thin data-access helper module (`app/services/tenant_db.py` or similar) exposing `get_owned(table, id, user_id) -> row`, `update_owned(...)`, `delete_owned(...)`, and `get_owned_child(child_table, child_id, parent_table, parent_fk, user_id) -> row`. The four IDOR fixes route through these helpers.

2. Fix findings 1–4 first (financial impact), then 5–11 (defense-in-depth + operational).

3. For object-by-id reads/updates/deletes, 404 (not 403) when not owned — caller can't tell "exists somewhere else" vs "doesn't exist".

4. Pytest regression suite proving cross-tenant access fails for invoice, expense, client, bank_transaction, quote — create user A and user B, have B attempt every read/update/delete on A's rows, assert 404. Also:
   - forged/unsigned JWT → 401
   - expired JWT → 401
   - client-supplied `user_id` in body → ignored (use the JWT's id)

5. Small reviewable commits on `security/idor-audit`. PR description explains each finding and the fix. **Do not merge** without sign-off.

Phase 3 (RLS reactivation roadmap) will be written separately as `RLS_ROADMAP.md` after Phase 2 ships.
