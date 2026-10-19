# BigDogg Marketing — run history

Tracks what each weekly marketing run has covered, so future runs avoid repeating the same
forum threads, blog topics, outreach targets, and directory-listing checks.

**Goal:** 0 → 2,000 paying users by end of 2026. Free channels only, no paid ads. This
routine only researches and drafts — it never posts, sends, signs up, or touches payment
details.

## 🚨 Critical, unresolved since 2026-08-17: 12 weekly PRs in a row, unreviewed, and the continuity mechanism keeps silently failing

As of this run (2026-10-19), **PRs #2 through #13 (12 straight weeks, 2026-07-28 through
2026-10-12) are all still open against `main`, none merged, none closed.** This run opens a
13th (expected to land as PR #14). This has been flagged to the founder via notification
after nearly every run since 2026-08-17 (that's roughly nine separate flags now) with no
recorded action.

Because every branch is cut from `main`, and `main` has never received a `marketing/` merge,
this file does not persist on its own — each run must reconstruct history from open
`marketing-drafts-*` branches via the GitHub API. **That reconstruction step has now failed
twice, not once:**

1. **2026-09-07** labeled itself "(first run)", discarded the full history 2026-08-31 had
   consolidated, and reused two already-used forum threads plus a near-duplicate blog topic.
   This was caught and documented by 2026-09-14.
2. **2026-09-28, 2026-10-05, and 2026-10-12 — three runs in a row — regressed the same way.**
   Each one again labeled its `STATE.md` "(first run)", again contained only that single
   week's data, and did not reconstruct or carry forward the consolidated history. As a
   direct, confirmed result:
   - Forum thread **77718** (factuur met materiaalopslag) has now been used as a "fresh"
     reply target **five separate times**: 2026-07-28, 2026-08-10, 2026-09-07, 2026-10-05,
     2026-10-12.
   - Forum thread **78290** (btw op de jaarbalans) has also been used **five times**:
     2026-08-03, 2026-08-10, 2026-09-07, 2026-10-05, 2026-10-12.
   - The **"BTW-aangifte doen als beginnend zzp'er"** blog topic (or a near-identical
     rewording of it) has been used as that week's "new" blog post **four times**:
     2026-08-03, 2026-09-07, 2026-10-05, 2026-10-12.

   **This is no longer a theoretical risk — if any of these drafts had actually been posted,
   the same forum thread would have received multiple different "founder" replies from
   BigDogg across different weeks**, which would look spammy/inconsistent to anyone reading
   that thread, and the blog would have near-duplicate posts targeting the same keyword.

This run (2026-10-19) rebuilt full history by reading `marketing/STATE.md` from **all 12**
open `marketing-drafts-*` branches (not just the latest one, precisely because the latest
few have proven unreliable) before doing any new research — see the consolidated reference
lists below. This is now the **third time** this full manual reconstruction has had to
happen from scratch, and it gets more expensive and more error-prone every week this stays
unresolved.

**Recommendation, unchanged and now urgent: merge or close PRs #2–#14.** A durable fix worth
considering, repeated from several prior runs: merge just a consolidated `marketing/STATE.md`
to `main` on its own, decoupled from the review-and-post draft content, so future runs stop
depending on a perfect cross-branch reconstruction (which has now demonstrably failed twice)
every single week. Flagged to the founder via push notification alongside this run.

**Method for future runs, until this is resolved:** do not trust a single recent branch's
`STATE.md` at face value, even if it doesn't say "(first run)". Cross-check the forum-thread
IDs and blog-topic wording in the consolidated lists below against whatever the most recent
1-2 branches claim, since this exact failure mode (confident-looking but wrong/incomplete
`STATE.md`) has now happened on 4 separate weeks (09-07, 09-28, 10-05, 10-12).

## Known constraints for this routine

- Sandbox has no browser, no logged-in accounts, cannot send/post/publish anything — output
  is drafts only, reviewed and posted/sent by the founder.
- Facebook and LinkedIn are out of scope (require login) — do not research or draft for them.
- `WebFetch` to higherlevel.nl has failed every single run so far — **13 consecutive weeks**
  now (2026-07-28 through 2026-10-19). Earlier runs saw `EGRESS_BLOCKED`/403; this run saw
  `getaddrinfo ENOTFOUND www.higherlevel.nl` (DNS failure) — same practical effect, the
  domain cannot be reached from this sandbox. All forum research is WebSearch-snippets-only;
  full thread content, exact dates, and reply counts are **not** independently verified —
  the founder should open each thread directly before posting.
- `main` and `master` have diverged significantly (confirmed repeatedly since 2026-08-31,
  reconfirmed this run). `origin/main` — the base every marketing PR targets — is old and
  reflects an early state of the app. `origin/master` has the real, current app (31 routers
  as of this run, including `trips.py`, `quotes.py`, `reminders.py`, `banking.py`/`bank.py`,
  `accountants.py`, `referrals.py`, `investments.py`, `hours.py`). **For any product-feature
  claim in a draft, verify against `master`, not `main`.** Still no recorded founder decision
  on whether `main` being frozen/stale relative to `master` is intentional.
- **Pricing:** `app/routers/subscription.py` on `master` — `PRICE_MONTHLY = 1199` cents =
  **€11.99/month** actual monthly billing. `PRICE_YEARLY = 11988` cents = €119.88/year,
  exactly 12 × €9.99 (confirmed by an explicit code comment: "so marketing can keep 'from
  €9,99/maand' on the yearly plan"). Drafts should say "vanaf €9,99 per maand bij een
  jaarabonnement" rather than a bare "€9,99/maand", which would overstate the monthly-billed
  price. Confirmed unchanged this run.
- **Reminders feature, precisely:** `app/routers/reminders.py` flags overdue invoices and
  lets the *user* send a reminder with one tap — it does not auto-email the client on its
  own. Describe it that way, not as "automatic overdue-invoice emails."
- **Accountant-portal feature:** `app/routers/accountants.py` — a token-gated, read-only
  link an accountant can open without a BigDogg account or password, 14-day validity,
  revocable by the owner. Confirmed again this run; useful as a concrete boekhouder-outreach
  hook (used again this week).
- **Referral program, confirmed against `app/routers/referrals.py`:** 2 referrals = 1 bonus
  month, capped at 3 bonus months total — matches the brief, confirmed in code.
- **Tax constants confirmed this run** (`app/constants/tax_rates.py`, master, "last verified
  for tax year 2026"): urencriterium 1.225 uur, KM-tarief €0,23/km, zelfstandigenaftrek
  €1.200 (down from €2.470 in 2025, scheduled to keep declining), file explicitly flags these
  must be re-verified every tax year.

---

## Run: 2026-10-19 (this run)

**Branch:** `marketing-drafts-2026-10-19`
**Drafts folder:** `marketing/drafts/2026-10-19/`

**PR backlog check (via GitHub MCP `search_pull_requests` + `list_branches`):** confirmed
PRs #2–#13 (2026-07-28 through 2026-10-12) all `open`, none `merged`, none `closed`. Flagged
via push notification alongside this run (see "Critical" section above for why this one is
more urgent than previous flags — the 4 duplication incidents are now a confirmed pattern,
not a one-off).

**History reconstruction method used:** read `marketing/STATE.md` from **all 12** prior
`marketing-drafts-*` branches directly via `get_file_contents` (not just the latest one),
specifically because 4 of the last 6 branches' own `STATE.md` had already proven unreliable
("first run" regressions). Cross-referenced every forum-thread ID and blog-topic wording
across all 12 before picking this week's new ones.

**`WebFetch` status:** still broken — `getaddrinfo ENOTFOUND www.higherlevel.nl`. 13th
consecutive week. All forum research below is WebSearch-snippets-only.

### Forum threads used (higherlevel.nl) — verified against the full 12-week history, genuinely new
- https://www.higherlevel.nl/forums/topic/78515-hoe-houden-jullie-als-online-verkoper-je-boekhouding-bij-met-meerdere-platforms/ — multi-platform boekhouding voor online verkopers (Administratie en verzekeringen, ~61 dagen oud op moment van search)
- https://www.higherlevel.nl/forums/topic/77505-vraag-over-eigen-vermogen-inkomstenbelasting/ — eigen vermogen en inkomstenbelasting bij een eenmanszaak (Fiscale zaken)
- https://www.higherlevel.nl/forums/topic/73038-kan-ik-sponsoring-van-open-source-projecten-opvoeren-als-kosten-voor-mijn-zzp/ — sponsoring van open-source projecten als zakelijke kosten (Fiscale zaken)

### Blog topic used
- "Zzp of eenmanszaak: wat is het verschil (en wat betekent dat voor je administratie)?"
  (target keyword: zzp of eenmanszaak administratieve verschillen). This has been on the
  "not yet covered" candidate list since the very first run (2026-07-28) and was never
  picked up — confirmed genuinely unused across all 12 weeks before using it this run.

### Outreach targets contacted (drafted, not sent)
- onderneming.nl — brief follow-up (first pitched 2026-08-17, no response in ~9 weeks)
- boekhouder.nl — new listing/review pitch (flagged as a candidate since 2026-08-17, never
  actually pitched until now)
- Independent boekhouder/accountant — referral partnership, accountant-portal angle (generic
  template, no real recipient — same gap every prior run has had)

### Directory listing status (checked 2026-10-19, via WebSearch only — no account created, nothing submitted)
| Site | BigDogg listed? |
|---|---|
| appwiki.nl | No |
| zzp-centrum.nl | No |
| onderneming.nl | No |
| ikwordzzper.nl | No |
| vergelijk-boekhoudprogramma.nl | No distinct live site found matching this exact name — unchanged finding across all 13 runs |

### Video script topics used
- Wat is het verschil tussen een offerte en een opdrachtbevestiging?
- Fictieve dienstbetrekking: mag je voor je ex-werkgever factureren?
- Zelfstandigenaftrek 2026: hoeveel is het en wie krijgt het?

---

## Consolidated reference lists (deduplicated across all 13 weeks, 2026-07-28 → 2026-10-19)

Use these lists first on future runs — they're deduplicated and corrected for the known
regressions above. Cross-check against the 1-2 most recent branches too, but don't trust
those alone.

### Forum threads already used — do not reuse (topic IDs, higherlevel.nl)
73546, 77718 (used 5×: 07-28, 08-10, 09-07, 10-05, 10-12 — definitely do not reuse again),
63916, 78124, 78290 (used 5×: 08-03, 08-10, 09-07, 10-05, 10-12 — definitely do not reuse
again), 78556, 77625, 78206, 77327, 73554, 76143, 77418, 78654, 76922, 74770, 76044 (used 2×:
09-07, 10-05), 77806, 72165, 72141, 77956, 76432 (used 2×: 09-21, 09-28), 74714, 77030, 78515,
77505, 73038.

### Forum threads seen but deliberately skipped (too old, flooded, off-topic, or weaker fit — available only if threads run dry)
72387, 56276, 74342, 78532, 74434, 75996, 76202, 74909, 74767, 78005, 77353, 70068, 74715,
25535, 56786, 78440, 71138, 78438, 78207, 77833, 71158, 77829, 78088, 76663, 76161, 75524,
77223, 78255, 74290, 75224, 76672.

### Blog topics already used — do not reuse (pick from "not yet covered" below instead)
- "Je eerste factuur maken als zzp'er" (used 3×: 07-28, 08-10 dup, 09-28 dup)
- "BTW-aangifte doen als beginnend zzp'er" / near-variants (used 4×: 08-03, 09-07, 10-05,
  10-12 — this topic keeps getting re-picked by regressed runs; **do not use again**)
- "Kleineondernemersregeling (KOR) voor zzp'ers" — 08-17
- "Jaarlijkse IB-aangifte als zzp'er" — 08-24
- "Kilometerregistratie als zzp'er" — 08-31
- "Zakelijke rekening verplicht als zzp'er?" — 09-14
- "Klant betaalt de factuur niet? stappenplan" — 09-21
- "Zzp of eenmanszaak: administratieve verschillen" — 10-19 (this run)

### Blog topics NOT yet covered (candidates for future weeks)
- Urencriterium 1.225 uur uitgelegd (only ever a video topic, 08-17)
- BTW verleggen (only a forum-reply angle 08-31 + video topic 09-14 — never a full post)
- KIA / investeringsaftrek (only a video topic, 09-21 — never a full post)
- BTW bij klanten in het buitenland (EU/niet-EU)
- Wat kost het om zzp'er te worden: eerste-jaar-kosten overzicht
- Zzp en pensioen opbouwen (long-tail, flagged since 09-28, still unused)

### Outreach targets already pitched (do not re-pitch without a follow-up angle)
appwiki.nl (07-28, follow-up 08-31), ikwordzzper.nl (07-28), vergelijk-boekhoudprogramma.nl /
Cloudhints (08-03 — domain's own existence still unconfirmed as of this run), zzp-centrum.nl
(08-17, follow-up 09-21), onderneming.nl (08-17, follow-up 10-19 this run),
boekhoudprogrammagids.nl (08-24), zzpdaily.nl (08-24, no confirmed contact yet),
officetown.nl (08-31, no confirmed contact yet), ondernemeneninternet.nl (09-14),
dezaak.nl (09-14, guest-content angle), mijnzzp.nl (09-21), boekhouder.nl (10-19, this run).

**All 5 of the original comparison sites named in the routine's own brief** (appwiki.nl,
zzp-centrum.nl, onderneming.nl, ikwordzzper.nl, vergelijk-boekhoudprogramma.nl) have been
pitched at least once as of 2026-08-17, with **zero recorded responses after 9+ weeks**. At
some point a founder decision on whether to keep expanding to new sites vs. accept no
response is coming, vs. verifying these ever actually got sent, would help future runs.

### Video script topics already used — do not reuse
3 verplichte factuuronderdelen, kilometerregistratie tip, btw-over-inclusief-bedrag fout, KOR
uitgelegd in 30 sec, jaarlijkse IB-aangifte nieuw voor zzp'ers, zakelijke rekening verplicht
of niet, doorlopende factuurnummering, kilometerregistratie privéauto, btw-aangifte
factuurdatum vs. betaaldatum, urencriterium 1.225 uur, wat te doen bij een niet-betalende
klant, btw bij internationale klanten, wat moet er verplicht op een factuur met de KOR,
zzp-kosten aftrekken twijfelgevallen, waarom facturen 7 jaar bewaren, offerte of factuur het
verschil, bonnetjes weggooien na scannen, aanbetaling factureren, aftrekposten die zzp'ers
vergeten, verplichte gegevens op een factuur, kilometerregistratie voor zzp'ers (09-07
variant), belasting opzij zetten reserveren, btw verleggen wanneer, thuiswerkaftrek, je
boekhouder toegang geven zonder wachtwoorden, KIA uitgelegd, btw-teruggave duurt te lang,
offerte vs. opdrachtbevestiging (10-19), fictieve dienstbetrekking ex-werkgever (10-19),
zelfstandigenaftrek 2026 uitgelegd (10-19).

### Full run log (branch → one-line summary)
- 2026-07-28 — first real run. Created `marketing/`.
- 2026-08-03 — clean, new threads/topic.
- 2026-08-10 — **regressed** ("first run"), duplicated 07-28/08-03 almost entirely.
- 2026-08-17 — recovered: manually reconstructed all history, first flagged the PR backlog.
- 2026-08-24 — clean, new threads/topic, re-flagged backlog.
- 2026-08-31 — clean, discovered `main`/`master` divergence, re-flagged backlog.
- 2026-09-07 — **regressed** ("first run"), reused 2 threads + near-dup blog topic.
- 2026-09-14 — recovered: documented the 09-07 regression, clean new content.
- 2026-09-21 — clean, confirmed pricing nuance + reminders.py + accountants.py details.
- 2026-09-28 — **regressed** ("first run"), no known-issue tracking at all.
- 2026-10-05 — **regressed** ("first run"), duplicated 77718/78290/76044 + BTW-topic.
- 2026-10-12 — **regressed** ("first run"), duplicated 78290/77718 again.
- 2026-10-19 (this run) — recovered via full 12-branch reconstruction; see above.

**Pattern worth the founder's attention:** recovery runs (08-17, 09-14, this run) only
happen when an agent happens to read far enough back to notice the regression. Three
consecutive regressed weeks (09-28 through 10-12) went uncaught until this run. This is
exactly the fragility the "merge STATE.md to main" recommendation above is meant to fix.
