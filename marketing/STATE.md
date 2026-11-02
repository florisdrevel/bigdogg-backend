# BigDogg Marketing — run history

Tracks what each weekly marketing run has covered, so future runs avoid repeating the
same forum threads, blog topics, outreach targets, and directory-listing checks.

**Goal:** 0 → 2,000 paying users by end of 2026. Free channels only, no paid ads. This
routine only researches and drafts — it never posts, sends, signs up, or touches
payment details.

## 🚨 Critical, unresolved since 2026-08-17: every weekly PR is still open, unreviewed, and the continuity mechanism keeps failing

As of this run (2026-11-02), **PRs #2 through #18 — all 17 prior weekly marketing
PRs, 2026-07-28 through 2026-10-26 — are still open against `main`, none merged, none
closed** (confirmed via the GitHub MCP `list_pull_requests` tool this run). This run
opens an 18th (expected to land as PR #19). This has been flagged to the founder
after nearly every run since 2026-08-17 — this is at least the tenth time — with no
recorded action visible from this sandbox.

**New this run: the continuity mechanism broke again.** The 2026-10-26 run's
`STATE.md` did *not* reconstruct history from prior branches (no "first run" label,
but no cross-branch check either) and, as a direct result:
- It reused higherlevel.nl thread **78290** ("Balans: Te vorderen/te betalen BTW") for
  a **6th time** (2026-08-03, 08-10, 09-07, 10-05, 10-12, and now 10-26) — the 2026-10-19
  run had explicitly flagged this exact thread as "definitely do not reuse again."
- It reused the blog topic **"Je eerste factuur maken als zzp'er"** for a **4th time**
  (2026-07-28, 08-10, 09-28, and now 10-26) — also explicitly flagged as "do not use
  again" by the 2026-10-19 consolidation.
- Its own "not yet used" candidate list for next week's blog topic (BTW-aangifte,
  kilometervergoeding, KOR) was itself stale — all three have already been used
  multiple times in earlier weeks. Do not trust a single prior week's "candidates"
  list without checking the full history below.

This run (2026-11-02) rebuilt the reference lists below by reading `marketing/STATE.md`
from the 2026-10-19 branch (which itself did a full 12-branch reconstruction) plus the
2026-10-26 branch directly, rather than trusting 10-26 at face value. **This is now the
fourth time a full or partial manual reconstruction has been needed** because a
previous week's `STATE.md` was incomplete or wrong (after 09-07, 09-28, 10-05, 10-12,
and now 10-26 — five regressions in eleven weeks).

**Recommendation, unchanged and still unacted on:** merge or close PRs #2–#19. A
durable fix worth considering, repeated by several prior runs: merge just a
consolidated `marketing/STATE.md` to `main` on its own, decoupled from the
review-and-post draft content, so future runs stop depending on a correct cross-branch
reconstruction every single week — a step that has now failed five times. Flagged to
the founder via push notification alongside this run.

**Method for future runs, until this is resolved:** do not trust the single most
recent branch's `STATE.md` at face value. Cross-check forum-thread IDs and blog-topic
wording against the consolidated lists below (which already account for the known
10-26 regression) before picking anything "new."

## Known constraints for this routine

- Sandbox has no browser, no logged-in accounts, cannot send/post/publish anything —
  output is drafts only, reviewed and posted/sent by the founder.
- Facebook and LinkedIn are out of scope (require login) — do not research or draft
  for them.
- `WebFetch` to higherlevel.nl has failed every single run so far — **18 consecutive
  weeks** now (2026-07-28 through 2026-11-02, confirmed again this run:
  `getaddrinfo ENOTFOUND www.higherlevel.nl`). The domain is not reachable from this
  sandbox. All forum research is WebSearch-snippets-only; full thread content, exact
  dates, and reply counts are **not** independently verified — the founder should open
  each thread directly before posting any reply.
- `main` and `master` have diverged significantly (confirmed repeatedly since
  2026-08-31). `origin/main` — the base every marketing PR targets — is old and
  reflects an early state of the app. `origin/master` has the real, current app.
  **For any product-feature or pricing claim in a draft, verify against `master`, not
  `main`.** Re-verified this run.
- **Pricing:** `app/routers/subscription.py` on `master` — `PRICE_MONTHLY = 1199`
  cents = **€11.99/month** actual monthly billing. `PRICE_YEARLY = 11988` cents =
  €119.88/year, exactly 12 × €9.99 (explicit code comment confirms this is
  intentional, "so marketing can keep 'from €9,99/maand' on the yearly plan").
  Drafts should say "vanaf €9,99 per maand bij een jaarabonnement," not a bare
  "€9,99/maand." Re-verified this run, unchanged.
- **Reminders feature:** `app/routers/reminders.py` flags overdue invoices and lets
  the *user* send a reminder with one tap — it does not auto-email the client on its
  own.
- **Accountant-portal feature:** `app/routers/accountants.py` — a token-gated,
  read-only link an accountant can open without a BigDogg account or password, 14-day
  validity, revocable/extendable by the owner. Re-verified this run.
- **Referral program:** `app/routers/referrals.py` + `subscription.py` —
  `bonus_months_max = 3`, matches the brief (2 referrals = 1 bonus month, capped at 3
  bonus months total). Re-verified this run.
- **Tax constants** (`app/constants/tax_rates.py`, master, "last verified for tax year
  2026" per its own header): urencriterium 1.225 uur, KM-tarief €0,23/km,
  zelfstandigenaftrek €1.200, MKB-winstvrijstelling 12,7%. File explicitly flags these
  must be re-verified every tax year — re-verified unchanged this run.
- Never fabricate specific recipient names, email addresses, or exact current prices
  on third-party sites — always leave placeholders for the founder to fill in after
  verifying manually.

---

## Run: 2026-11-02 (this run)

**Branch:** `marketing-drafts-2026-11-02`
**Drafts folder:** `marketing/drafts/2026-11-02/`

**PR backlog check (via GitHub MCP `list_pull_requests`):** confirmed PRs #2–#18
(2026-07-28 through 2026-10-26) all `open`, none `merged`, none `closed`. See the
critical section above.

**History reconstruction:** read `marketing/STATE.md` from the 2026-10-19 branch (full
12-week reconstruction) and the 2026-10-26 branch (this week's predecessor, found to
have regressed — see above), then cross-checked every forum-thread ID and blog-topic
choice below against both before picking anything new.

**`WebFetch` status:** still broken — `getaddrinfo ENOTFOUND www.higherlevel.nl`. 18th
consecutive week. All forum research below is WebSearch-snippets-only.

### Forum threads used (higherlevel.nl) — verified against full history, genuinely new
- https://www.higherlevel.nl/forums/topic/52122-btw-en-factuur-van-non-eu-land/ — btw
  en factuur van non-EU land (Administratie en verzekeringen)
- https://www.higherlevel.nl/forums/topic/56579-zzper-en-btw-aangifte/ — zzp'er en btw
  aangifte (Fiscale zaken)
- https://www.higherlevel.nl/forums/topic/50398-factuur-ontvangen-zonder-mijn-bedrijfsnaam-erop/
  — factuur ontvangen zonder bedrijfsnaam van de leverancier (Fiscale zaken)

### Blog topic used
- "Btw factureren naar het buitenland als zzp'er: EU en niet-EU simpel uitgelegd"
  (target keyword: btw factureren buitenland zzp). Confirmed genuinely unused as a full
  blog post across all 18 prior weeks before using it this run (it had only ever
  appeared as a "not yet covered" candidate, first flagged 2026-10-19).

### Outreach targets contacted (drafted, not sent)
- zzp-centrum.nl — listing/review pitch, rotated back in (last pitched 2026-08-17,
  follow-up 2026-09-21, nothing since; deliberately not appwiki.nl again, which was
  pitched both 2026-08-31 and 2026-10-26 — two weeks running).
- onderneming.nl — light-touch follow-up only (last contacted 2026-10-19, so kept this
  one brief; founder can skip sending if it's too soon).
- Independent boekhouder/accountant — referral partnership, accountant-portal angle.
  Still a generic template, no real recipient — same gap every prior run has had.

**Note for the founder:** all 5 comparison sites from the routine's original brief
have now been pitched at least once, several more than once, with zero recorded
responses after 14+ weeks. Worth a decision on whether to keep re-pitching the same
five or branch out — not acted on by this run, just flagged again.

### Directory listing status (checked 2026-11-02, via WebSearch only — no account
created, nothing submitted; direct fetch of these sites was not attempted this run
since higherlevel.nl's failure already confirms the sandbox's network policy blocks
this category of site)
| Site | BigDogg listed? |
|---|---|
| appwiki.nl | No (appwiki's own published top-10 boekhoudpakketten list, syndicated via Emerce, does not mention BigDogg) |
| zzp-centrum.nl | No distinct evidence found either way this week — treat as "not confirmed listed," consistent with all prior weeks |
| onderneming.nl | No distinct evidence found either way this week — consistent with all prior weeks |
| ikwordzzper.nl | No distinct evidence found either way this week — consistent with all prior weeks |
| vergelijk-boekhoudprogramma.nl | Still no live site matching this exact name surfaced in search — unchanged finding across all 18 runs |

### Video script topics used
- Zzp en pensioen: waarom nu al opzij zetten
- Btw-nummer van een buitenlandse klant checken (VIES) vóór je zonder btw factureert
- Wat kost het eerste jaar als zzp'er je écht?

---

## Consolidated reference lists (deduplicated across all 18 weeks, 2026-07-28 → 2026-11-02)

Use these lists first on future runs.

### Forum threads already used — do not reuse (topic IDs, higherlevel.nl)
73546, 77718 (used 5×: 07-28, 08-10, 09-07, 10-05, 10-12), 63916, 78124, 78290 (used
**6×**: 08-03, 08-10, 09-07, 10-05, 10-12, 10-26 — definitely do not reuse again),
78556, 77625, 78206, 77327, 73554, 76143, 77418, 78654, 76922, 74770, 76044 (used 2×:
09-07, 10-05), 77806, 72165, 72141, 77956, 76432 (used 2×: 09-21, 09-28), 74714, 77030,
78515, 77505, 73038, 77347 (10-26), 52122 (11-02, this run), 56579 (11-02, this run),
50398 (11-02, this run).

### Forum threads seen but deliberately skipped (too old, flooded, off-topic, or a
competing product asking for feedback — available only if genuinely new threads run
dry)
72387, 56276, 74342, 78532 (competing product "ZZP Pulse"/alles-in-één tool asking for
feedback — seen again 10-26 and 11-02, still a bad target), 74434, 75996, 76202,
74909, 74767, 78005, 77353, 70068, 74715, 25535, 56786, 78440, 71138, 78438, 78207,
77833, 71158, 77829, 78088, 76663, 76161, 75524, 77223, 78255, 74290, 75224, 76672,
65902, 78434 (same competing-app thread referenced under a different ID by 10-26),
78352 (off-topic — bestelbussen/rijtijden regulation, not invoicing/bookkeeping).

### Blog topics already used — do not reuse (pick from "not yet covered" below instead)
- "Je eerste factuur maken als zzp'er" (used **4×**: 07-28, 08-10, 09-28, 10-26 —
  this topic keeps getting re-picked by regressed runs; **do not use again, ever**)
- "BTW-aangifte doen als beginnend zzp'er" / near-variants (used 4×: 08-03, 09-07,
  10-05, 10-12 — same problem; **do not use again**)
- "Kleineondernemersregeling (KOR) voor zzp'ers" — 08-17
- "Jaarlijkse IB-aangifte als zzp'er" — 08-24
- "Kilometerregistratie als zzp'er" — 08-31
- "Zakelijke rekening verplicht als zzp'er?" — 09-14
- "Klant betaalt de factuur niet? stappenplan" — 09-21
- "Zzp of eenmanszaak: administratieve verschillen" — 10-19
- "Btw factureren naar het buitenland als zzp'er (EU/niet-EU)" — 11-02 (this run)

### Blog topics NOT yet covered (candidates for future weeks)
- Urencriterium 1.225 uur uitgelegd (only ever a video topic, 08-17)
- BTW verleggen, as a dedicated post (only a forum-reply angle + video topic so far —
  never a full post; note it now overlaps partly with this week's blog post, so angle
  it differently, e.g. purely domestic reverse-charge situations)
- KIA / investeringsaftrek (only a video topic, 09-21 — never a full post)
- Wat kost het om zzp'er te worden: eerste-jaar-kosten overzicht (used as a *video
  script* this run, 11-02 — still open as a full blog post with more depth/numbers)
- Zzp en pensioen opbouwen (used as a *video script* this run, 11-02 — still open as a
  full blog post)
- Thuiswerkaftrek voor zzp'ers uitgelegd
- Wat moet er op een factuur staan bij de KOR (combines two used-separately topics,
  genuinely not yet a dedicated post)

### Outreach targets already pitched (do not re-pitch without a follow-up angle, or
without checking the gap listed here first)
appwiki.nl (07-28, follow-up 08-31, follow-up 10-26 — pitched 3× total, consider
pausing on this one for a few weeks), ikwordzzper.nl (07-28), vergelijk-boekhoudprogramma.nl
/ Cloudhints (08-03 — domain's own existence still unconfirmed as of this run),
zzp-centrum.nl (08-17, follow-up 09-21, follow-up 11-02 this run), onderneming.nl
(08-17, follow-up 10-19, light follow-up 11-02 this run), boekhoudprogrammagids.nl
(08-24), zzpdaily.nl (08-24, no confirmed contact yet), officetown.nl (08-31, no
confirmed contact yet), ondernemeneninternet.nl (09-14), dezaak.nl (09-14, guest-content
angle), mijnzzp.nl (09-21), boekhouder.nl (10-19).

**All 5 of the original comparison sites named in the routine's own brief** have been
pitched at least once, with **zero recorded responses after 14+ weeks**. Still no
founder decision recorded on whether to keep expanding to new sites, pause, or verify
these are actually being sent at all.

### Video script topics already used — do not reuse
3 verplichte factuuronderdelen, kilometerregistratie tip (used multiple variants:
08-31 full post + several video reuses including 09-07 and 10-26), btw-over-inclusief-
bedrag fout, KOR uitgelegd in 30 sec, jaarlijkse IB-aangifte nieuw voor zzp'ers,
zakelijke rekening verplicht of niet, doorlopende factuurnummering,
kilometerregistratie privéauto, btw-aangifte factuurdatum vs. betaaldatum,
urencriterium 1.225 uur, wat te doen bij een niet-betalende klant, btw bij
internationale klanten (generic), wat moet er verplicht op een factuur met de KOR,
zzp-kosten aftrekken twijfelgevallen, waarom facturen 7 jaar bewaren, offerte of
factuur het verschil, bonnetjes weggooien na scannen, aanbetaling factureren,
aftrekposten die zzp'ers vergeten, verplichte gegevens op een factuur, belasting opzij
zetten reserveren, btw verleggen wanneer, thuiswerkaftrek, je boekhouder toegang geven
zonder wachtwoorden, KIA uitgelegd, btw-teruggave duurt te lang, offerte vs.
opdrachtbevestiging, fictieve dienstbetrekking ex-werkgever, zelfstandigenaftrek 2026
uitgelegd, btw-tarief keuze (10-26), creditfactuur/dubbele factuur (10-26), zzp en
pensioen: waarom nu al opzij zetten (11-02), btw-nummer buitenlandse klant checken /
VIES (11-02), wat kost het eerste jaar als zzp'er je echt (11-02).

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
- 2026-10-19 — recovered via full 12-branch reconstruction.
- 2026-10-26 — **regressed again** (no "first run" label this time, but no
  cross-branch check either): reused thread 78290 a 6th time and blog topic "eerste
  factuur" a 4th time, both explicitly flagged "do not reuse" by 10-19.
- 2026-11-02 (this run) — recovered via reconstruction from 10-19 + 10-26; documented
  the 10-26 regression above; re-flagged the now-18-PR backlog.

**Pattern worth the founder's attention, restated:** recovery runs (08-17, 09-14,
10-19, this run) only happen when an agent happens to read far back enough to notice a
regression — and even then, as 10-26 shows, a single clean-looking run after a
recovery can still regress without an obvious "first run" tell. This is exactly the
fragility the "merge STATE.md to main" recommendation above is meant to fix, and it
remains unresolved after 18 weeks.
