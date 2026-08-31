# BigDogg Marketing — run history

Tracks what each weekly marketing run has covered, so future runs avoid repeating the same
forum threads, blog topics, outreach targets, and directory-listing checks. Update this
file every run — add the new "Run" section at the top, most recent first.

## ⚠️ Known issue: six weekly PRs in a row are still unmerged

As of this run (2026-08-31), **none of the five previous weekly marketing PRs have been
merged or closed**: `marketing-drafts-2026-07-28` (PR #2), `marketing-drafts-2026-08-03`
(PR #3), `marketing-drafts-2026-08-10` (PR #4), `marketing-drafts-2026-08-17` (PR #5), and
`marketing-drafts-2026-08-24` (PR #6) are all still open against `main`. This run opens a
sixth (PR #7). Because each week's branch is cut from `main`, and `main` has never received
a merge, **`marketing/` still does not exist on `main`** — every run so far has branched off
a version of the repo with no memory of prior weeks' `STATE.md` and had to manually
reconstruct it from the open branches.

This caused a real duplication problem once already: the 2026-08-10 run could not see
2026-07-28's or 2026-08-03's history and ended up re-using the exact same 3 forum threads,
the same blog topic, and re-pitching a site already pitched twice. Every run since
2026-08-17 has avoided repeating that by reading `STATE.md` from all open
`marketing-drafts-*` branches before starting new research (see method below) — but this is
a workaround, not a fix, and it gets more fragile and more expensive every week this stays
unresolved: six branches now need to be reconciled by hand instead of one.

**Flagged to the founder via notification after this run, again: please merge or close PRs
#2–#7.** Once at least one lands on `main`, `marketing/STATE.md` starts working as
originally designed and this reconstruction step goes away. This has now been flagged in
three consecutive runs (08-17, 08-24, 08-31) with no action yet.

**Method for future runs, until this is resolved:** run `git branch -a` /
`git show origin/marketing-drafts-<date>:marketing/STATE.md` for every open
`marketing-drafts-*` branch (not just the latest one) to reconstruct full history before
doing any new research. Don't rely on only the most recent branch's `STATE.md`, since it may
itself be based on an incomplete reconstruction if a run was ever skipped.

## Known constraints for this routine

- Sandbox has no browser, no logged-in accounts, cannot send/post/publish anything — output
  is drafts only, reviewed and posted/sent by the founder.
- Facebook and LinkedIn are out of scope (require login) — do not research or draft for them.
- `WebFetch` to higherlevel.nl has been blocked every run so far (2026-07-28 through
  2026-08-31 — 6 consecutive runs, `EGRESS_BLOCKED` every time). All forum/listing-site
  research has been done via `WebSearch` snippets only, not full page fetches. Thread
  details (open/closed status, reply counts, exact wording) are best-effort from search
  snippets — the founder should open each thread directly before posting.
- **New this run (2026-08-31): `main` and `master` have diverged significantly, and `main`
  is far behind.** `origin/main` (the repo's actual default branch, and the base every
  marketing PR targets) sits at commit `d799a8e` with only 4 routers in `app/routers/`
  (`auth.py`, `overview.py`, `products.py`, `reports.py`) and an old `requirements.txt`.
  `master` is much further ahead (commit `4970a7c` at time of this run) with 30 routers,
  including real features like `trips.py` (kilometerregistratie), `quotes.py` (offertes),
  `reminders.py` (automatic overdue-invoice notifications), and `banking.py`/`bank.py`
  (bank-transaction import + PDF reports). **This means the 08-24 run's claim that "no
  mileage/kilometerregistratie feature exists in the codebase" was based on checking `main`
  only — it's wrong: the feature exists on `master`, confirmed by reading
  `app/routers/trips.py` and `app/constants/tax_rates.py` (2026 rate: €0,23/km) this run.**
  For product-feature accuracy in future drafts, check `master`, not `main` — that appears
  to be where the real, current app lives. This branch (`marketing-drafts-2026-08-31`) was
  still cut from `main`, matching the existing PRs' base, since a marketing-only PR doesn't
  need app code and staying consistent with PRs #2–#6 avoids yet another divergence — but
  the founder should be aware `main` looks stale/frozen relative to `master`, in case that's
  not intentional (e.g. if `main` is meant to be kept in sync, or if it's a leftover branch
  that should be deleted/archived).

---

## Run: 2026-08-31

**Branch:** `marketing-drafts-2026-08-31`
**Drafts folder:** `marketing/drafts/2026-08-31/`

**PR backlog check (via GitHub MCP `list_pull_requests`):** confirmed PRs #2–#6 (weeks
2026-07-28 through 2026-08-24) are all still `open`, none `merged`. Flagged to the founder —
see "Known issue" section above. Also discovered the `main`/`master` divergence described
above while checking codebase accuracy for the blog post — flagged in "Known constraints".

### Forum threads used (higherlevel.nl) — new, not reused from any prior run
- https://www.higherlevel.nl/forums/topic/78654-btw-verleggen-als-zzper-in-de-creatieve-sector/ — btw verleggen als zzp'er in de creatieve sector (illustratie/animatie)
- https://www.higherlevel.nl/forums/topic/76922-foutieve-btw-factuur/ — foutieve btw op een verstuurde factuur, hoe corrigeren
- https://www.higherlevel.nl/forums/topic/74770-boekhouding-een-zooitje/ — net gestarte zzp'er (keukenmonteur) vraagt feedback op rommelige boekhouding

**Threads seen but skipped this run** (already used by a prior run, off-topic, or a weaker
fit than the 3 chosen):
- 73554, 76143, 77418, 77625, 78206, 77327, 77718, 78124, 78290, 78556, 78557, 73546, 63916,
  75996, 76202, 72387, 78532, 74434, 56276, 74342, 74909, 74767, 56786, 78440, 71138, 78438,
  78207, 77833, 71158, 77829, 78088, 78005 — used or explicitly skipped by a prior run (see
  those sections below).
- 77353 ("Creditfactuur voor 2024 uitreiken in 2025") and 70068 ("Creditnota en btw uit
  voorgaande kwartaal") — genuine credit-note questions, but too close in subject to
  08-24's forum reply on thread 77418 (creditfactuur-nummering); skipped in favor of
  variety. Candidates for a future run if credit-note threads run dry elsewhere.
- 74715 ("voorschotbetalingen zonder factuur en aangifte IB") and 25535 ("Aanbetaling wel of
  niet vooraf factureren") — genuine, but 25535's topic ID suggests a much older thread
  (pre-2020 range based on prior runs' ID/age pattern) and 74715 reads more corporate/complex
  (bol.com-style advance-payment accounting) than a good "genuinely helpful founder answer"
  fit; used the aanbetaling angle as a video script topic instead this run (see below).
- 71182, 60762, 73906, 54625, 37332, 75491, 53038, 51806, 50708, 58552, 43244, 59306, 13874,
  57137 — older BTW/factuur threads surfaced this run via broader search, all below the
  ~73500 topic-ID range prior runs treated as "too old"; not used.

### Blog topic used
- "Kilometerregistratie als zzp'er: zo hou je je zakelijke kilometers bij" (target keyword:
  kilometerregistratie zzp'er bijhouden). This was one of the not-yet-covered blog-post
  candidates flagged since 08-17. Confirmed accurate to a real BigDogg feature this run by
  reading `app/routers/trips.py` and `app/constants/tax_rates.py` on `master` (per-trip
  mileage log, €0,23/km for 2026) — see "Known constraints" above re: `main` vs `master`.
  This corrects the 08-24 run's incorrect claim that no mileage feature exists.
- Remaining not-yet-covered blog-post candidates: zakelijke rekening verplicht zzp?,
  urencriterium 1225 uur uitgelegd, wat te doen bij een niet-betalende klant, offerte vs.
  factuur (new candidate, used as a video script this run — see below).

### Outreach targets contacted (drafted, not sent)
- officetown.nl — listing/review pitch, new site this run (surfaced across 08-17/08-24 as
  "not yet pitched"). No reliable direct contact address found via WebSearch — founder needs
  to find the right address via officetown.nl's contact page before sending.
- appwiki.nl — short follow-up email (not a re-pitch), since it was first pitched 2026-07-28
  (contact: rubel@appwiki.nl) with no recorded response in ~5 weeks. New approach this run:
  a brief "checking in" note rather than repeating the full pitch.
- Independent boekhouder/accountant — referral partnership (generic template, no real
  recipient — same caveat as every prior run).
- Still not pitched, no confirmed contact: boekhouder.nl, ondernemeneninternet.nl,
  zzpdaily.nl (contact still needs confirming per 08-24's note).

### Directory listing status (checked 2026-08-31, via WebSearch only — no account created,
nothing submitted)
| Site | BigDogg listed? |
|---|---|
| appwiki.nl | No |
| zzp-centrum.nl | No |
| onderneming.nl | No |
| ikwordzzper.nl | No |
| vergelijk-boekhoudprogramma.nl | Still no live/distinct site found matching this exact name — closest match remains vergelijkboekhoudprogramma.com, also no BigDogg listing (unchanged from prior runs) |

Also searched generally for "BigDogg" + zzp/facturatie/boekhouden — no results referencing
this product anywhere (expected, consistent with an unlaunched/pre-listing product).

### Video script topics used
- Offerte of factuur? Het verschil (ties to the real offerte→factuur conversion feature in
  `app/routers/quotes.py`, confirmed this run)
- Mag je bonnetjes weggooien na scannen? (digitale bewaarplicht — ties to the real
  receipt-photo-upload + AI-parse feature in `app/routers/expenses.py`, confirmed this run)
- Aanbetaling vragen? Zo factureer je dat goed (voorschotfactuur)

### Ideas / follow-ups for next runs
- **Priority, unchanged since 08-17, now flagged a third time: ask the founder about
  merging or closing PRs #2–#7.** Six unmerged weekly PRs now — flagged via notification
  after this run.
- **New: flag the `main`/`master` divergence to the founder** (see "Known constraints")
  — worth a quick sanity check on whether `main` being ~26 commits behind `master` is
  intentional.
- Re-check `WebFetch` access to higherlevel.nl each run — 6 consecutive runs blocked now.
- Candidate full blog posts not yet written: zakelijke rekening verplicht zzp?, urencriterium
  1225 uur uitgelegd, wat te doen bij een niet-betalende klant, offerte vs. factuur.
- Directory sites not yet pitched or with no confirmed contact yet: boekhouder.nl,
  ondernemeneninternet.nl, zzpdaily.nl.
- Credit-note-adjacent forum threads (77353, 70068) and older aanbetaling threads (74715,
  25535) remain available if threads run dry in a future week, per the notes above.
- Once `main`/`master` clarity exists, re-verify which branch actually reflects "what
  BigDogg does today" before writing future product-feature claims in blog posts or video
  scripts — this run used `master`.

---

## Run: 2026-08-24

**Branch:** `marketing-drafts-2026-08-24`
**Drafts folder:** `marketing/drafts/2026-08-24/`

**PR backlog check (via GitHub MCP `list_pull_requests`):** confirmed PRs #2, #3, #4, #5
(weeks 2026-07-28 through 2026-08-17) are all still `open`, none `merged`. Flagged to the
founder — see "Known issue" section above.

### Forum threads used (higherlevel.nl) — new, not reused from any prior run
- https://www.higherlevel.nl/forums/topic/73554-is-een-factuur-voor-de-administratie-altijd-verplicht/ — is een factuur bij verkoop aan particulieren verplicht?
- https://www.higherlevel.nl/forums/topic/76143-vraagje-ivm-archivering-facturen-en-verantwoordelijkheid-boekhouder/ — facturen kwijtgeraakt bij overstap boekhoudpakket, wiens verantwoordelijkheid?
- https://www.higherlevel.nl/forums/topic/77418-creditfactuur-niet-toegepast/ — creditfactuur-nummering en gevolgen voor winst-en-verliesrekening

**Threads seen but skipped this run** (already used by a prior run, off-topic for this
routine's scope, or not a good fit):
- 77625, 78206, 77327, 77718, 78124, 78290, 73546, 63916, 78556, 78557, 75996, 76202, 72387,
  78532, 74434, 56276, 74342, 74909, 74767 — used by a prior run (07-28 through 08-17; see
  those sections below).
- 78005 ("BTW op buitenlandse diensten... cadeaubonnen") — still a candidate per 08-17's
  note, but skipped again this run in favor of 3 more broadly-relatable threads; still
  available for a future run if threads run dry.
- Explored the "Ondernemingsplan en businessplanning" and "Rechtsvormen, vennootschaps- en
  ondernemingsrecht" boards per 08-17's suggestion (topics 71138, 78438, 78207, 77833,
  71158, 77829, 78088, etc.) — none were a good fit for this routine's scope (invoicing/
  bookkeeping/BTW/admin tools specifically); they're legal-structure or business-planning
  questions, not administratie questions. Not recommending these boards for future runs
  unless the routine's scope is deliberately widened.
- 56786, 78440 (VOF/company-structure and old threads) — off-topic or too old.

### Blog topic used
- "Jaarlijkse IB-aangifte als zzp'er: wat je nodig hebt en hoe je het voorbereidt (2026)"
  (target keyword: jaarlijkse IB-aangifte zzp'er voorbereiden). This was one of the
  not-yet-covered candidates flagged by the 08-17 run; it also ties naturally to BigDogg's
  real annual-overview/report feature (`app/routers/overview.py`, `app/routers/reports.py`
  — confirmed by reading the actual codebase this run, not assumed), so the product mention
  in the post is accurate to what BigDogg actually does today (invoicing + auto BTW
  calculation + quarterly/annual report PDF). No mileage/kilometerregistratie feature exists
  in the codebase — avoided claiming that in any draft this run.

  **Correction added by the 2026-08-31 run: this codebase check was done against `main`,
  which turned out to be far behind `master`. The mileage/kilometerregistratie feature
  DOES exist on `master` (`app/routers/trips.py`). See "Known constraints" at the top of
  this file.**
- Remaining not-yet-covered candidates for future blog posts: kilometerregistratie zzp
  uitgelegd, zakelijke rekening verplicht zzp?, urencriterium 1225 uur uitgelegd, wat te doen
  bij een niet-betalende klant.

### Outreach targets contacted (drafted, not sent)
- boekhoudprogrammagids.nl — listing/review pitch, new site this run (surfaced by 08-17 as
  unevaluated). Contact: info@boekhoudprogrammagids.nl (found via WebSearch, unverified by
  direct fetch — confirm on their /contact page before sending).
- zzpdaily.nl — listing/review pitch, new site this run. No reliable contact address found
  via WebSearch (only a generic firstname@zzpdaily.nl pattern guess, not sent-worthy) —
  founder needs to find the right address via zzpdaily.nl/ons-team/ or the contact form
  before sending.
- Independent boekhouder/accountant — referral partnership (generic template, no real
  recipient — same caveat as every prior run).
- officetown.nl surfaced again this run (per 08-17's list) but not pitched — no contact
  found yet; candidate for a future run.

### Directory listing status (checked 2026-08-24, via WebSearch only — no account created,
nothing submitted)
| Site | BigDogg listed? |
|---|---|
| appwiki.nl | No |
| zzp-centrum.nl | No |
| onderneming.nl | No |
| ikwordzzper.nl | No |
| vergelijk-boekhoudprogramma.nl | Still no live/distinct site found matching this exact name — closest match remains vergelijkboekhoudprogramma.com, also no BigDogg listing (unchanged from prior runs) |

Also spot-checked via a combined site-search across appwiki.nl / zzp-centrum.nl /
onderneming.nl / ikwordzzper.nl for any mention of "BigDogg" or "bigdogg.nl" — none found,
consistent with the per-site table above.

### Video script topics used
- Wat moet er verplicht op een factuur staan met de KOR (KOR-specifieke factuureisen —
  different angle from the general "3 verplichte factuuronderdelen" video from 07-28)
- Zzp-kosten aftrekken: twijfelgevallen (werkplek thuis, opleidingen, telefoon/internet)
- Waarom je facturen 7 jaar moet bewaren (pairs with this run's forum reply on thread 76143)

### Ideas / follow-ups for next runs
- **Priority, unchanged from 08-17: ask the founder about merging or closing PRs #2–#6.**
  This is now 5 unmerged weekly PRs — the backlog is the main open risk to this routine
  actually being useful. Flagged via notification after this run.
- Re-check `WebFetch` access to higherlevel.nl each run — 5 consecutive runs blocked now.
- Candidate full blog posts not yet written: kilometerregistratie zzp uitgelegd, zakelijke
  rekening verplicht zzp?, urencriterium 1225 uur uitgelegd, wat te doen bij een
  niet-betalende klant.
- Directory sites not yet pitched or with no confirmed contact yet: officetown.nl, zzpdaily.nl
  (contact still needs confirming).
- Forum topic/78005 (BTW buitenlandse diensten/cadeaubonnen) remains available if threads
  run dry in a future week — niche but genuine.

---

## Run: 2026-08-17

**Branch:** `marketing-drafts-2026-08-17`
**Drafts folder:** `marketing/drafts/2026-08-17/`

### Forum threads used (higherlevel.nl) — new, not reused from any prior run
- https://www.higherlevel.nl/forums/topic/77625-vreemde-btw-situatie-die-ik-niet-begrijp-en-hoe-te-verwerken-in-mijn-boekhouding/ — marktkraam huur, deels btw-vrijgesteld/deels 21%
- https://www.higherlevel.nl/forums/topic/78206-factuur-van-bedrijf-met-btw-nummer-startend-met-eu-met-21-btw-maar-kor-ondernemer/ — factuur met "EU"-btw-nummer, KOR-ondernemer
- https://www.higherlevel.nl/forums/topic/77327-btw-van-vve-in-eigen-administratie/ — btw van VVE terugvragen (0 reacties op moment van search — good target)

**Threads seen but skipped this run** (already used by a prior run, or off-topic/too old/
already flooded):
- 73546, 77718, 63916, 78124, 78290, 78556, 78557 — used by 2026-07-28, 2026-08-03, or
  2026-08-10 (see below).
- 75996 — confirmed closed to new replies (per 2026-08-03 note).
- 76202, 72387, 78532, 74434, 56276, 74342 — skipped by 2026-07-28/08-03 for being too old
  or already flooded with software recommendations (see those sections below).
- 74909 ("Dienst geleverd, klant betaalt niet") — closed, dated April 2023, too old.
- 74767 ("Factuurnummer dubbel gebruikt") — dated 2023, too old.
- 78005 ("BTW op buitenlandse diensten... cadeaubonnen") — genuine but fairly niche/
  corporate (VAT-exempt gift-card company + OSS reverse charge on ad spend), less
  relatable than the 3 chosen above; candidate for a future run if thread topics run dry.

### Blog topic used
- "Kleineondernemersregeling (KOR) voor zzp'ers: wel of niet aanmelden in 2026?" (target
  keyword: kleineondernemersregeling zzp wel of niet). This was flagged as a not-yet-covered
  candidate by both the 2026-07-28 and 2026-08-03 runs.
- Adjacent long-tail topics still NOT covered as full blog posts (only as video scripts so
  far): "kilometerregistratie zzp uitgelegd", "zakelijke rekening verplicht zzp?",
  "jaarlijkse IB-aangifte zzp'er uitgelegd", "urencriterium 1225 uur uitgelegd" (new video
  topic this week, could become a full post), "wat te doen bij een niet-betalende klant"
  (new video topic this week, could become a full post).

### Outreach targets contacted (drafted, not sent)
- zzp-centrum.nl — listing/review pitch (contact: info@zzpcentrum.nl, found via WebSearch,
  unverified by direct fetch — confirm before sending)
- onderneming.nl — listing/review pitch (no specific contact found via WebSearch this run —
  founder needs to find the right address via onderneming.nl/contact)
- Independent boekhouder/accountant — referral partnership (generic template, no real
  recipient — same caveat as every prior run)

**All 5 original directory sites have now been pitched at least once** across the 4 runs
to date: appwiki.nl (07-28), ikwordzzper.nl (07-28), vergelijk-boekhoudprogramma.nl/
Cloudhints (08-03), zzp-centrum.nl (08-17, this run), onderneming.nl (08-17, this run).
Next runs should wait for responses before re-pitching any of these, or look for new
directory/comparison sites not on the original list (e.g. zzpdaily.nl, boekhoudprogrammagids.nl,
boekhouder.nl, ondernemeneninternet.nl, officetown.nl — all surfaced this run as other
Dutch boekhoudprogramma-comparison sites, not yet evaluated or pitched).

### Directory listing status (checked 2026-08-17, via WebSearch only — no account created,
nothing submitted)
| Site | BigDogg listed? |
|---|---|
| appwiki.nl | No |
| zzp-centrum.nl | No |
| onderneming.nl | No |
| ikwordzzper.nl | No |
| vergelijk-boekhoudprogramma.nl | Domain still does not appear to be live/relevant as such — closest match remains vergelijkboekhoudprogramma.com, also no BigDogg listing |

### Video script topics used
- Urencriterium (1.225 uur) voor zelfstandigenaftrek
- Wat te doen bij een niet-betalende klant (herinnering → aanmaning → incasso)
- BTW bij internationale klanten/diensten (EU-zakelijk = btw verlegd)

### Ideas / follow-ups for next runs
- **Priority: ask the founder about merging or closing PRs #2, #3, #4** — this is the root
  cause of last week's duplicated work. Until resolved, keep reconstructing history from all
  open `marketing-drafts-*` branches, not just `main`.
- Re-check `WebFetch` access to higherlevel.nl each run — 4 consecutive runs blocked now.
- New directory/comparison sites surfaced this run, not yet evaluated: zzpdaily.nl,
  boekhoudprogrammagids.nl, boekhouder.nl, ondernemeneninternet.nl, officetown.nl.
- Candidate full blog posts not yet written: kilometerregistratie zzp uitgelegd,
  zakelijke rekening verplicht zzp?, jaarlijkse IB-aangifte zzp'er uitgelegd,
  urencriterium 1225 uur uitgelegd, wat te doen bij een niet-betalende klant.
- Candidate forum board not yet explored via WebSearch: "Ondernemingsplan en
  businessplanning" and "Rechtsvormen, vennootschaps- en ondernemingsrecht" boards turned up
  a few results this run (e.g. topic 78556) — worth a dedicated look next run for variety
  beyond "Administratie en verzekeringen"/"Fiscale zaken".

---

## Run: 2026-08-10

**Branch:** `marketing-drafts-2026-08-10`
**Drafts folder:** `marketing/drafts/2026-08-10/`

**Note (added retroactively by the 2026-08-17 run):** this run's `STATE.md` said "first
run" and its forum threads/blog topic/outreach target **duplicate 2026-07-28 and
2026-08-03** almost exactly (same 3 forum threads as 2026-08-03: 77718, 78124, 78290; same
blog topic as 2026-07-28: "eerste factuur maken"; re-pitched appwiki.nl). This happened
because this run branched from `main`, which never had `marketing/` merged into it, so it
had no visibility into the two prior runs. See the "Known issue" section at the top of
this file.

### Forum threads used (higherlevel.nl) — duplicates, see note above
- https://www.higherlevel.nl/forums/topic/77718-vakman-zzp-factuur-maken-met-opslag/
- https://www.higherlevel.nl/forums/topic/78124-factuur-sturen-echter-geen-ondernemer-geen-inschrijfverplichting-handelsregister/
- https://www.higherlevel.nl/forums/topic/78290-balans-te-vorderente-betalen-btw/

### Blog topic used — duplicate, see note above
- "Eerste factuur maken als zzp'er" (target keyword: eerste factuur maken als zzp'er)

### Outreach targets contacted — duplicate, see note above
- appwiki.nl — listing/review pitch (already pitched 2026-07-28)
- Independent boekhouder/accountant — referral partnership (generic template)

### Directory listing status (checked 2026-08-10)
| Site | BigDogg listed? |
|---|---|
| appwiki.nl | No |
| zzp-centrum.nl | No |
| onderneming.nl | No |
| ikwordzzper.nl | No |
| vergelijk-boekhoudprogramma.nl | Domain does not appear to exist as such — closest match vergelijkboekhoudprogramma.com, also no listing |

### Video script topics used
- Doorlopende factuurnummering
- Kilometerregistratie voor zakelijk gebruik privéauto
- BTW-aangifte: factuurdatum vs. betaaldatum

---

## Run: 2026-08-03

**Branch:** `marketing-drafts-2026-08-03`
**Drafts folder:** `marketing/drafts/2026-08-03/`

### Forum threads used (higherlevel.nl)
- https://www.higherlevel.nl/forums/topic/78124-factuur-sturen-echter-geen-ondernemer-geen-inschrijfverplichting-handelsregister/ (mag je als niet-ondernemer een "factuur"/kwitantie sturen)
- https://www.higherlevel.nl/forums/topic/78290-balans-te-vorderente-betalen-btw/ (te vorderen/te betalen btw op de jaarbalans, bol.com-verkoper)
- https://www.higherlevel.nl/forums/topic/78556-mag-een-opdrachtgever-een-factuur-weigeren-omdat-deze-enkele-maanden-later-is-verstuu/ (opdrachtgever weigert late factuur te betalen)

**Threads seen but deliberately skipped:**
- topic/75996 — confirmed closed to new replies.
- topic/76202 — dated Feb 2024, not recent enough.
- topic/78557 — recent but a general IB-aangifte-delay grumble thread, not a good fit for
  a helpful invoicing/bookkeeping/BTW/admin-tool reply.

### Blog topic used
- "BTW-aangifte doen als beginnend zzp'er: complete uitleg (2026)" (target keyword: btw
  aangifte doen als beginnend zzp'er)

### Listing-site status check (2026-08-03)
- appwiki.nl — pitched 2026-07-28, not re-pitched.
- zzp-centrum.nl / onderneming.nl — not yet pitched at that point (now pitched 2026-08-17).
- ikwordzzper.nl — pitched 2026-07-28, not re-pitched.
- vergelijk-boekhoudprogramma.nl (Cloudhints) — pitched this run (info@cloudhints.com,
  unverified by direct fetch).

### Cold emails drafted
- vergelijk-boekhoudprogramma.nl listing pitch, generic boekhouder/accountant referral
  template.

### Video scripts drafted
- KOR uitgelegd in 30 seconden, jaarlijkse IB-aangifte nieuw voor zzp'ers, zakelijke
  rekening verplicht of niet.

---

## Run: 2026-07-28 (first run — `marketing/` created)

**Branch:** `marketing-drafts-2026-07-28`
**Drafts folder:** `marketing/drafts/2026-07-28/`

### Forum threads used (higherlevel.nl)
- https://www.higherlevel.nl/forums/topic/73546-eerste-keer-omzetbelasting-aangifte-gedaan-hoe-lang-duurt-de-verwerking/ (verwerkingstijd eerste btw-teruggaaf)
- https://www.higherlevel.nl/forums/topic/77718-vakman-zzp-factuur-maken-met-opslag/ (factuur met materiaalopslag)
- https://www.higherlevel.nl/forums/topic/63916-zzp-geen-zakelijke-rekening-alle-priv%C3%A9-uitgaven-in-boekhouding-zetten-of-niet/ (privé-uitgaven in boekhouding zonder zakelijke rekening)

**Threads seen but deliberately skipped:**
- topic/72387 (factuurnummering per opdrachtgever) — dated Nov 2021, not recent.
- topic/56276 and topic/74342 (boekhoudpakket-advies threads) — already flooded with
  software-recommendation replies.
- topic/78532 ("alles-in-één tool voor zzp'ers") and topic/74434 ("ZZP Pulse") — other
  builders' own self-promo/feedback threads, not neutral ground for a competing founder.

### Blog topic used
- "Je eerste factuur maken als zzp'er: complete stappenplan (2026)" (target keyword:
  eerste factuur maken als zzp'er)

### Listing-site status check (2026-07-28)
- appwiki.nl — not listed. Contact: rubel@appwiki.nl. **Pitched this run.**
- zzp-centrum.nl — not listed. Not yet pitched at that point (now pitched 2026-08-17).
- onderneming.nl — not listed. Not yet pitched at that point (now pitched 2026-08-17).
- ikwordzzper.nl — not listed. Contact: info@ikwordzzper.nl. **Pitched this run** (guest
  content + listing ask).
- vergelijk-boekhoudprogramma.nl (Cloudhints) — not listed. Contact: info@cloudhints.com.
  Not yet pitched at that point (pitched 2026-08-03).

### Cold emails drafted
- appwiki.nl listing pitch, generic boekhouder/accountant referral template,
  ikwordzzper.nl guest content pitch.

### Video scripts drafted
- 3 verplichte factuuronderdelen, kilometerregistratie tip, btw-over-inclusief-bedrag fout.
