# BigDogg Marketing — run history

Tracks what each weekly marketing run has covered, so future runs avoid repeating the same
forum threads, blog topics, outreach targets, and directory-listing checks. Update this
file every run — add the new "Run" section at the top, most recent first.

## ⚠️ Known issue: eight weekly PRs in a row are unmerged, and it already caused two duplication incidents

As of this run (2026-09-14), **none of the seven previous weekly marketing PRs have been
merged or closed**: PRs #2 through #8 (weeks 2026-07-28 through 2026-09-07) are all still
open against `main`. This run opens a ninth (PR #9). Because every branch is cut from
`main`, and `main` has never received a `marketing/` merge, **this file does not persist
between runs on its own** — every run has to manually reconstruct it from the open
`marketing-drafts-*` branches before doing new research.

This has now caused **two separate duplication incidents**, not one:

1. **2026-08-10** couldn't see 2026-07-28's or 2026-08-03's history and re-used the exact
   same 3 forum threads and the same blog topic as prior weeks.
2. **2026-09-07** did something worse: its `STATE.md` labeled itself "(first run)" and
   contained *only* that week's data — it silently discarded the fully-consolidated history
   that the 2026-08-31 run had carefully rebuilt (six weeks of forum threads, blog topics,
   skipped/flooded threads, outreach targets, and the divergence note below). As a direct
   result, the 2026-09-07 run reused forum threads 78290 and 77718 (both used multiple times
   before) and picked a blog topic ("Je eerste BTW-aangifte doen als zzp'er") that nearly
   duplicates the 2026-08-03 run's topic ("BTW-aangifte doen als beginnend zzp'er").

**This run (2026-09-14) reconstructed history from ALL EIGHT branches** (07-28, 08-03,
08-10, 08-17, 08-24, 08-31, 09-07, plus this week), not just the most recent one, precisely
to avoid repeating the 09-07 mistake. This is now the third time this reconstruction has had
to happen from scratch. **This is a workaround, not a fix — every week this stays unmerged,
the reconstruction gets more fragile and more expensive, and the 09-07 incident shows the
workaround itself can silently fail.** This has been flagged to the founder after every run
since 08-17 (four times now) with no recorded action.

**Recommendation, unchanged: merge or close PRs #2–#9.** Once even one lands on `main`, this
file starts working as originally designed and the reconstruction step goes away entirely.
A durable fix worth considering: merge just this file's current (consolidated) state to
`main` on its own, separately from the review-and-post drafts, so future runs always have
continuity regardless of whether the draft content itself gets merged.

**Method for future runs, until this is resolved:** run `git branch -a` /
`git show origin/marketing-drafts-<date>:marketing/STATE.md` for every open
`marketing-drafts-*` branch (not just the latest one) to reconstruct full history before
doing any new research. Do not trust the most recent branch's `STATE.md` alone — cross-check
it against at least one or two branches before that, since a run can silently reset it (as
09-07 did).

## Known constraints for this routine

- Sandbox has no browser, no logged-in accounts, cannot send/post/publish anything — output
  is drafts only, reviewed and posted/sent by the founder.
- Facebook and LinkedIn are out of scope (require login) — do not research or draft for them.
- `WebFetch` to higherlevel.nl has been blocked every single run so far (2026-07-28 through
  2026-09-14 — **8 consecutive runs**, `EGRESS_BLOCKED` every time, confirmed again this
  run). All forum/listing-site research has been done via `WebSearch` snippets only, not
  full page fetches. Thread details (open/closed status, reply counts, exact wording) are
  best-effort from search snippets — the founder should open each thread directly before
  posting.
- `main` and `master` have diverged significantly (confirmed again this run). `origin/main`
  (the base every marketing PR targets, currently at commit `d799a8e`) has only 4 routers
  and reflects an old state of the app. `origin/master` has 30 routers, including the real,
  current features: `trips.py` (kilometerregistratie, €0,23/km for 2026), `quotes.py`
  (offertes), `reminders.py` (automatic overdue-invoice email reminders), `banking.py`/
  `bank.py` (bank-transaction import with per-line zakelijk/privé tagging + BTW/annual PDF
  reports), `hours.py` (urenregistratie), `referrals.py` (referral codes), and
  `app/constants/tax_rates.py` (the belasting-reserve estimate used in this week's video
  script 1). **For any product-feature claim in a future draft, verify against `master`, not
  `main`.** This has been flagged since 2026-08-31 (three runs now) with no recorded
  decision on whether `main` is intentionally frozen or just stale — worth a founder
  sanity-check.

---

## Run: 2026-09-14

**Branch:** `marketing-drafts-2026-09-14`
**Drafts folder:** `marketing/drafts/2026-09-14/`

**PR backlog check (via GitHub MCP `list_pull_requests`):** confirmed PRs #2–#8 (weeks
2026-07-28 through 2026-09-07) are all still `open`, none `merged`. Also discovered the
09-07 STATE.md regression described above while reconstructing history — see "Known issue".
Flagged to the founder via notification after this run.

### Forum threads used (higherlevel.nl) — new, not reused from any prior run
- https://www.higherlevel.nl/forums/topic/77806-behoefte-aan-simpele-facturatietool-zonder-boekhoudcomplexiteit/ — zzp'er zoekt simpele facturatietool zonder boekhoudcomplexiteit (Administratie en verzekeringen). Natural, on-topic BigDogg mention.
- https://www.higherlevel.nl/forums/topic/72165-gevolgen-van-het-niet-voldoen-aan-het-urencriterium/ — gevolgen van het niet halen van het urencriterium voor een laat-in-het-jaar gestarte zzp'er (Fiscale zaken)
- https://www.higherlevel.nl/forums/topic/72141-betalingstermijn-op-factuur-overschreden/ — wat te doen als een klant de betalingstermijn overschrijdt (Administratie en verzekeringen)

**Threads seen but skipped this run** (already used by a prior run, per the consolidated
history below, or a weaker fit):
- 73546, 77718, 63916, 78124, 78290, 78556, 78557, 77625, 78206, 77327, 73554, 76143, 77418,
  78654, 76922, 74770, 76044 — used by a prior run (see sections below). 77718 and 78290 were
  incorrectly re-used by the 09-07 run; not reusing them again this week.
- 75224 ("Als ZZP-er factureren naar de onderneming van mijn man") — genuine topic but dated
  July 2023, too old per this routine's established convention (skip anything that reads as
  multi-year-old).
- 76672 ("Boekhouden: overlappende betalingen over boekjaar heen") — too similar to 09-07's
  already-used thread 76044 (factuur inboeken overlapping boekjaar); skipped for variety.
- 76663 ("Kleineondernemersregeling (KOR): Voor- en nadelen") — genuine and unused as a forum
  thread, but the KOR topic itself was already used as a full blog post (08-17); kept in
  reserve for a future week rather than doubling up in the same week as other KOR-adjacent
  content.
- 75996 (confirmed closed to replies, per 08-03's note), 76202/72387/56276/74342/78532/74434
  (too old or self-promo threads, per 07-28's note), 74909/74767 (too old, per 08-17's note),
  78005/77353/70068/74715/25535 (niche or subject-overlap, per 08-17/08-31 notes) — all
  still on the "not recommended" list from prior runs, listed here again for continuity.

### Blog topic used
- "Zakelijke rekening verplicht als zzp'er? Dit zegt de wet (en de praktijk) in 2026"
  (target keyword: zakelijke rekening verplicht zzp). This was a candidate flagged as
  not-yet-covered since 2026-08-17 (repeated in 08-24 and 08-31's "ideas for next run"
  sections). Confirmed via WebSearch this run that it's not legally required for an
  eenmanszaak (multiple independent sources agreed), and grounded the BigDogg feature
  mention (bank-transaction import + per-line zakelijk/privé tagging) in the actual
  `app/routers/banking.py` code on `master`.
- Remaining not-yet-covered candidates: urencriterium 1225 uur (full post — only ever done
  as a video topic so far, on 08-17), wat te doen bij een niet-betalende klant (full post —
  only ever done as a video topic, on 08-17), BTW verleggen (full post — only used as a
  forum-reply angle in 08-31 and a video topic this week), zzp of eenmanszaak:
  administratieve verschillen (never used in any format).

### Outreach targets contacted (drafted, not sent)
- ondernemeneninternet.nl — listing/review pitch, new site this run. Possible contact
  `info@zietuwel.nl` surfaced via search (unverified — the site's own /contact/ page is the
  safer route; confirm before sending).
- dezaak.nl — guest content/expert-quote pitch, new site this run, chosen because they
  published a 2026 article on this exact week's blog topic (zakelijke rekening voor
  starters). No contact found yet — founder needs to locate one via their contact/redactie
  page.
- Independent boekhouder/accountant — referral partnership (generic template, no real
  recipient — same caveat as every prior run; still nobody has picked a specific firm).

**All 5 of the original comparison sites named in this routine's instructions** (appwiki.nl,
zzp-centrum.nl, onderneming.nl, ikwordzzper.nl, vergelijk-boekhoudprogramma.nl) have now been
pitched at least once (see full history below) with no recorded response from any of them.
This run intentionally moved to two new targets (ondernemeneninternet.nl, dezaak.nl) instead
of re-pitching one of the five without a known non-response — but at some point a founder
decision on whether/how to follow up on the original five would help future runs avoid just
endlessly finding new sites instead of following through on old pitches.

### Directory listing status (checked 2026-09-14, via WebSearch only — no account created,
nothing submitted)
| Site | BigDogg listed? |
|---|---|
| appwiki.nl | No |
| zzp-centrum.nl | No |
| onderneming.nl | No |
| ikwordzzper.nl | No |
| vergelijk-boekhoudprogramma.nl | No distinct live site found matching this exact name (unchanged finding across all 8 runs) |

Also searched generally for "BigDogg" across these five sites — no mentions found,
consistent with an unlisted, pre-launch-marketing product (8 consecutive runs, same result).

### Video script topics used
- Hoeveel belasting opzij zetten als zzp'er (reserveren) — ties to the real tax-reserve
  estimate feature in `app/constants/tax_rates.py` on `master`
- BTW verleggen als zzp'er — wanneer moet dat?
- Thuiswerkaftrek: mag je dat als zzp'er?

**Candidate video topics for future weeks:** wat is het verschil tussen een offerte en een
opdrachtbevestiging, KIA (kleinschaligheidsinvesteringsaftrek) uitgelegd, btw-teruggave
duurt te lang wat nu, fictieve dienstbetrekking bij werken voor je ex-werkgever.

### Ideas / follow-ups for next runs
- **Priority, now flagged a fourth time: ask the founder about merging or closing PRs
  #2–#9.** This is the root cause of two separate duplication incidents now (08-10 and
  09-07) — not a hypothetical risk anymore. Flagged via notification after this run.
- **Consider merging just `marketing/STATE.md` to `main` on its own**, decoupled from the
  weekly draft content, so future runs stop depending on perfect cross-branch reconstruction
  every single week.
- Re-check `WebFetch` access to higherlevel.nl each run — 8 consecutive runs blocked now.
- Candidate full blog posts not yet written: urencriterium 1225 uur, wat te doen bij een
  niet-betalende klant, BTW verleggen, zzp of eenmanszaak (administratieve verschillen).
- Follow up on (or get a founder decision about) the original 5 comparison-site pitches,
  none of which have a recorded response after being pitched for 5-8 weeks.
- Forum topics 76663 (KOR voor- en nadelen), 78005, 77353, 70068 remain available in
  reserve if threads run dry in a future week.

---

## Run: 2026-09-07

**Branch:** `marketing-drafts-2026-09-07`
**Drafts folder:** `marketing/drafts/2026-09-07/`

**Note (added retroactively by the 2026-09-14 run):** this run's `STATE.md` incorrectly
labeled itself "(first run)" and did not carry forward the consolidated history the
2026-08-31 run had built. As a result it reused forum threads 78290 (used 08-03, 08-10) and
77718 (used 07-28, 08-10), and picked a blog topic essentially duplicating 08-03's. See the
"Known issue" section at the top of this file for the full explanation.

### Forum threads used (higherlevel.nl) — includes duplicates, see note above
- https://www.higherlevel.nl/forums/topic/78290-balans-te-vorderente-betalen-btw/ — duplicate of 08-03/08-10 usage
- https://www.higherlevel.nl/forums/topic/77718-vakman-zzp-factuur-maken-met-opslag/ — duplicate of 07-28/08-10 usage
- https://www.higherlevel.nl/forums/topic/76044-factuur-inboeken-overlapping-boekjaar/ — genuinely new

### Blog topic used — near-duplicate of 08-03, see note above
- "Je eerste BTW-aangifte doen als zzp'er" (target keyword: btw aangifte doen als beginnend zzp'er)

### Outreach targets contacted (drafted, not sent)
- zzp-centrum.nl — listing pitch (re-pitch; already pitched 08-17)
- Independent boekhouder/accountant — referral partnership (generic template)
- Generic zzp blog/nieuwsbrief — guest content pitch (no specific outlet identified)

### Directory listing status (checked 2026-09-07)
Same "not listed on any of the 5 sites" result as every other run.

### Video script topics used
- Aftrekposten die zzp'ers vergeten (thuiswerkplek, software, reiskosten)
- Verplichte gegevens op een factuur
- Kilometerregistratie voor zzp'ers

---

## Run: 2026-08-31

**Branch:** `marketing-drafts-2026-08-31`
**Drafts folder:** `marketing/drafts/2026-08-31/`

**PR backlog check:** confirmed PRs #2–#6 (weeks 2026-07-28 through 2026-08-24) all still
`open`. This run first discovered the `main`/`master` divergence (see "Known constraints").

### Forum threads used (higherlevel.nl) — new, not reused from any prior run
- https://www.higherlevel.nl/forums/topic/78654-btw-verleggen-als-zzper-in-de-creatieve-sector/ — btw verleggen in de creatieve sector
- https://www.higherlevel.nl/forums/topic/76922-foutieve-btw-factuur/ — foutieve btw op een verstuurde factuur, hoe corrigeren
- https://www.higherlevel.nl/forums/topic/74770-boekhouding-een-zooitje/ — net gestarte zzp'er vraagt feedback op rommelige boekhouding

**Threads seen but skipped:** 73554, 76143, 77418, 77625, 78206, 77327, 77718, 78124, 78290,
78556, 78557, 73546, 63916, 75996, 76202, 72387, 78532, 74434, 56276, 74342, 74909, 74767,
78440, 71138, 78438, 78207, 77833, 71158, 77829, 78088, 78005 (used or explicitly skipped by
a prior run); 77353, 70068 (too similar to 08-24's creditfactuur thread); 74715, 25535
(weaker fit or too old); 71182, 60762, 73906, 54625, 37332, 75491, 53038, 51806, 50708,
58552, 43244, 59306, 13874, 57137 (older threads, not used).

### Blog topic used
- "Kilometerregistratie als zzp'er: zo hou je je zakelijke kilometers bij" (target keyword:
  kilometerregistratie zzp'er bijhouden). Confirmed against `app/routers/trips.py` +
  `app/constants/tax_rates.py` on `master` (per-trip log, €0,23/km for 2026) — corrected
  08-24's incorrect claim that no mileage feature exists (that check was done against `main`
  only).

### Outreach targets contacted (drafted, not sent)
- officetown.nl — listing pitch, no confirmed contact found
- appwiki.nl — brief follow-up (first pitched 07-28, contact rubel@appwiki.nl, no response
  in ~5 weeks)
- Independent boekhouder/accountant — referral partnership (generic template)

### Directory listing status (checked 2026-08-31)
Not listed on any of the 5 sites (unchanged).

### Video script topics used
- Offerte of factuur? Het verschil (ties to `app/routers/quotes.py`)
- Mag je bonnetjes weggooien na scannen? (ties to `app/routers/expenses.py`)
- Aanbetaling vragen? Zo factureer je dat goed

---

## Run: 2026-08-24

**Branch:** `marketing-drafts-2026-08-24`
**Drafts folder:** `marketing/drafts/2026-08-24/`

**PR backlog check:** confirmed PRs #2–#5 all still `open`.

### Forum threads used (higherlevel.nl) — new
- https://www.higherlevel.nl/forums/topic/73554-is-een-factuur-voor-de-administratie-altijd-verplicht/ — factuur bij verkoop aan particulieren verplicht?
- https://www.higherlevel.nl/forums/topic/76143-vraagje-ivm-archivering-facturen-en-verantwoordelijkheid-boekhouder/ — facturen kwijtgeraakt bij overstap boekhoudpakket
- https://www.higherlevel.nl/forums/topic/77418-creditfactuur-niet-toegepast/ — creditfactuur-nummering en gevolgen voor winst-en-verliesrekening

**Threads seen but skipped:** 77625, 78206, 77327, 77718, 78124, 78290, 73546, 63916, 78556,
78557, 75996, 76202, 72387, 78532, 74434, 56276, 74342, 74909, 74767 (used or too
old/off-topic); 78005 (niche, kept in reserve); explored but rejected "Ondernemingsplan" and
"Rechtsvormen" boards as off-scope (71138, 78438, 78207, 77833, 71158, 77829, 78088); 56786,
78440 (off-topic/too old).

### Blog topic used
- "Jaarlijkse IB-aangifte als zzp'er: wat je nodig hebt en hoe je het voorbereidt (2026)"
  (target keyword: jaarlijkse IB-aangifte zzp'er voorbereiden). **Correction added by the
  08-31 run:** this run's codebase check for feature accuracy was done against `main` only,
  which is far behind `master` — its claim that no mileage feature exists was wrong.

### Outreach targets contacted (drafted, not sent)
- boekhoudprogrammagids.nl — listing pitch (contact: info@boekhoudprogrammagids.nl,
  unverified)
- zzpdaily.nl — listing pitch, no reliable contact found
- Independent boekhouder/accountant — referral partnership (generic template)

### Directory listing status (checked 2026-08-24)
Not listed on any of the 5 sites (unchanged).

### Video script topics used
- Wat moet er verplicht op een factuur staan met de KOR
- Zzp-kosten aftrekken: twijfelgevallen
- Waarom je facturen 7 jaar moet bewaren

---

## Run: 2026-08-17

**Branch:** `marketing-drafts-2026-08-17`
**Drafts folder:** `marketing/drafts/2026-08-17/`

### Forum threads used (higherlevel.nl) — new
- https://www.higherlevel.nl/forums/topic/77625-vreemde-btw-situatie-die-ik-niet-begrijp-en-hoe-te-verwerken-in-mijn-boekhouding/ — marktkraam huur, deels btw-vrijgesteld
- https://www.higherlevel.nl/forums/topic/78206-factuur-van-bedrijf-met-btw-nummer-startend-met-eu-met-21-btw-maar-kor-ondernemer/ — factuur met "EU"-btw-nummer, KOR-ondernemer
- https://www.higherlevel.nl/forums/topic/77327-btw-van-vve-in-eigen-administratie/ — btw van VVE terugvragen

**Threads seen but skipped:** 73546, 77718, 63916, 78124, 78290, 78556, 78557 (used
earlier); 75996 (confirmed closed); 76202, 72387, 78532, 74434, 56276, 74342 (too old/
flooded); 74909, 74767 (too old); 78005 (niche, kept in reserve).

### Blog topic used
- "Kleineondernemersregeling (KOR) voor zzp'ers: wel of niet aanmelden in 2026?" (target
  keyword: kleineondernemersregeling zzp wel of niet)

### Outreach targets contacted (drafted, not sent)
- zzp-centrum.nl — listing pitch (contact: info@zzpcentrum.nl, unverified)
- onderneming.nl — listing pitch, no contact found
- Independent boekhouder/accountant — referral partnership (generic template)

**All 5 original directory sites pitched at least once as of this run.**

### Directory listing status (checked 2026-08-17)
Not listed on any of the 5 sites (unchanged).

### Video script topics used
- Urencriterium (1.225 uur) voor zelfstandigenaftrek
- Wat te doen bij een niet-betalende klant
- BTW bij internationale klanten/diensten

---

## Run: 2026-08-10

**Branch:** `marketing-drafts-2026-08-10`
**Drafts folder:** `marketing/drafts/2026-08-10/`

**Note (added retroactively by the 08-17 run):** this run's `STATE.md` said "first run" and
duplicated 07-28/08-03 almost exactly (couldn't see their history, since neither PR had been
merged). First occurrence of the duplication problem this routine has had.

### Forum threads used — duplicates of 07-28/08-03
- topic/77718, topic/78124, topic/78290

### Blog topic used — duplicate of 07-28
- "Eerste factuur maken als zzp'er"

### Outreach targets — duplicate
- appwiki.nl (already pitched 07-28), independent boekhouder/accountant referral (generic)

### Video script topics used
- Doorlopende factuurnummering, kilometerregistratie voor zakelijk gebruik privéauto,
  BTW-aangifte factuurdatum vs. betaaldatum

---

## Run: 2026-08-03

**Branch:** `marketing-drafts-2026-08-03`
**Drafts folder:** `marketing/drafts/2026-08-03/`

### Forum threads used
- topic/78124 (factuur/kwitantie zonder ondernemerschap), topic/78290 (te vorderen/te
  betalen btw op jaarbalans), topic/78556 (opdrachtgever weigert late factuur)

**Skipped:** topic/75996 (closed), topic/76202 (too old), topic/78557 (weak fit)

### Blog topic used
- "BTW-aangifte doen als beginnend zzp'er: complete uitleg (2026)" (target keyword: btw
  aangifte doen als beginnend zzp'er)

### Outreach targets
- vergelijk-boekhoudprogramma.nl/Cloudhints listing pitch (info@cloudhints.com, unverified),
  independent boekhouder/accountant referral (generic)

### Video script topics used
- KOR uitgelegd in 30 seconden, jaarlijkse IB-aangifte nieuw voor zzp'ers, zakelijke
  rekening verplicht of niet

---

## Run: 2026-07-28 (first run — `marketing/` created)

**Branch:** `marketing-drafts-2026-07-28`
**Drafts folder:** `marketing/drafts/2026-07-28/`

### Forum threads used
- topic/73546 (verwerkingstijd eerste btw-teruggaaf), topic/77718 (factuur met
  materiaalopslag), topic/63916 (privé-uitgaven in boekhouding zonder zakelijke rekening)

**Skipped:** topic/72387 (too old), topic/56276 + topic/74342 (flooded with software
recs), topic/78532 + topic/74434 (other builders' self-promo threads)

### Blog topic used
- "Je eerste factuur maken als zzp'er: complete stappenplan (2026)" (target keyword: eerste
  factuur maken als zzp'er)

### Outreach targets
- appwiki.nl listing pitch (contact: rubel@appwiki.nl), independent boekhouder/accountant
  referral (generic), ikwordzzper.nl guest content + listing pitch (contact:
  info@ikwordzzper.nl)

### Video script topics used
- 3 verplichte factuuronderdelen, kilometerregistratie tip, btw-over-inclusief-bedrag fout
