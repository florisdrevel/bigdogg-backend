# BigDogg Marketing — run history

Tracks what each weekly marketing run has covered, so future runs avoid repeating the same
forum threads, blog topics, outreach targets, and directory-listing checks. Update this
file every run — add the new "Run" section at the top, most recent first.

## ⚠️ Known issue: nine weekly PRs in a row are unmerged, and it already caused two duplication incidents

As of this run (2026-09-21), **none of the eight previous weekly marketing PRs have been
merged or closed**: PRs #2 through #9 (weeks 2026-07-28 through 2026-09-14) are all still
open against `main`. This run opens a tenth (PR #10). Because every branch is cut from
`main`, and `main` has never received a `marketing/` merge, **this file does not persist
between runs on its own** — every run has to manually reconstruct it from the open
`marketing-drafts-*` branches before doing new research.

This has caused **two separate duplication incidents** so far:

1. **2026-08-10** couldn't see 2026-07-28's or 2026-08-03's history and re-used the exact
   same 3 forum threads and the same blog topic as prior weeks.
2. **2026-09-07** labeled its `STATE.md` "(first run)" and silently discarded the
   consolidated history the 2026-08-31 run had built, causing it to reuse two already-used
   forum threads and pick a near-duplicate blog topic.

**This run (2026-09-21) reconstructed history from the 2026-09-14 branch's `STATE.md`**,
which was itself already a full 8-week reconstruction (verified reliable — it correctly
documented and corrected the 09-07 regression rather than repeating it). This is now the
**fifth** run flagging this to the founder (previously flagged after every run since
08-17) with no recorded action yet.

**Recommendation, unchanged: merge or close PRs #2–#10.** Once even one lands on `main`,
this file starts working as originally designed and the reconstruction step goes away
entirely. A durable fix worth considering: merge just this file's current (consolidated)
state to `main` on its own, separately from the review-and-post drafts, so future runs
always have continuity regardless of whether the draft content itself gets merged.

**Method for future runs, until this is resolved:** read `marketing/STATE.md` from the
single most recent `marketing-drafts-*` branch first — as of this run, that file is a
verified, trustworthy full reconstruction (the 09-07 regression is documented and was not
repeated by 09-14). Only fall back to reconstructing from multiple older branches if the
latest branch's `STATE.md` looks incomplete, self-contradictory, or labels itself "first
run" while prior branches clearly exist (that combination is exactly what went wrong on
09-07) — in that case, cross-check against at least one or two branches before that one.

## Known constraints for this routine

- Sandbox has no browser, no logged-in accounts, cannot send/post/publish anything — output
  is drafts only, reviewed and posted/sent by the founder.
- Facebook and LinkedIn are out of scope (require login) — do not research or draft for them.
- `WebFetch` to higherlevel.nl has been blocked every single run so far (2026-07-28 through
  2026-09-21 — **9 consecutive runs**, `EGRESS_BLOCKED` every time, confirmed again this
  run). All forum/listing-site research has been done via `WebSearch` snippets only, not
  full page fetches. Thread details (open/closed status, reply counts, exact wording) are
  best-effort from search snippets — the founder should open each thread directly before
  posting.
- `main` and `master` have diverged significantly (confirmed again this run). `origin/main`
  (the base every marketing PR targets, currently at commit `d799a8e`) is old and reflects
  an early state of the app. `origin/master` has ~30 routers, including the real, current
  features. **For any product-feature claim in a future draft, verify against `master`, not
  `main`.** Flagged since 2026-08-31 (now five runs) with no recorded decision on whether
  `main` is intentionally frozen or just stale — worth a founder sanity-check.
- **Pricing correction, found this run:** the brief describes BigDogg as "EUR 9.99/month",
  and `app/routers/subscription.py` on `master` confirms this is accurate **as the
  yearly-plan equivalent** (`PRICE_YEARLY = 11988` cents = €119.88/year = exactly 12 ×
  €9.99, with an explicit code comment: "so marketing can keep 'from €9,99/maand' on the
  yearly plan"). The actual **monthly-billed** price is `PRICE_MONTHLY = 1199` cents =
  **€11.99/month**. This week's blog post uses "vanaf €9,99 per maand bij een
  jaarabonnement" to stay accurate — future drafts should do the same rather than stating
  a bare "€9,99/maand" that could read as the monthly-billing price.
- Confirmed this run: `app/routers/reminders.py` on `master` sends the **user** (the
  BigDogg-using zzp'er) a notification when their invoice is overdue — it does **not**
  auto-email the client. The user taps "Stuur herinnering" to send that. Two prior runs'
  `STATE.md` entries (09-07, 09-14) described this as "automatic overdue-invoice email
  reminders", which overstates it — the automation is the *alert to the user*, not the
  reminder to the client. Future drafts should describe it as: BigDogg flags overdue
  invoices automatically, and lets you send a reminder with one tap — never says it emails
  clients on its own.
- Confirmed this run: `app/routers/accountants.py` on `master` — BigDogg has a token-gated,
  read-only accountant portal (accountant opens a link, no BigDogg account or password
  needed, 14-day validity, revocable by the owner). Not mentioned in any prior week's
  drafts. Used this week as the boekhouder-outreach angle and a video-script topic — a
  concrete alternative to the generic "referral partnership, in overleg" framing every
  prior run used.

---

## Run: 2026-09-21

**Branch:** `marketing-drafts-2026-09-21`
**Drafts folder:** `marketing/drafts/2026-09-21/`

**PR backlog check (via GitHub MCP `list_pull_requests`):** confirmed PRs #2–#9 (weeks
2026-07-28 through 2026-09-14) are all still `open`, none `merged`. Flagged to the founder
via notification after this run (fifth consecutive flag).

**Codebase grounding done this run (against `master`, not `main`):** read
`app/routers/reminders.py`, `app/routers/accountants.py`, `app/routers/referrals.py`,
`app/routers/investments.py`, `app/routers/quotes.py`, `app/routers/trips.py`,
`app/constants/tax_rates.py`, `app/routers/subscription.py` — surfaced the pricing nuance
and the reminders-are-not-fully-automatic correction documented above, plus confirmed the
accountant-portal feature, KIA-adjacent investment/depreciation tracking, and 2026 tax
constants (urencriterium 1225 uur, KM-tarief €0,23, zelfstandigenaftrek €1.200,
MKB-winstvrijstelling 12,7%).

### Forum threads used (higherlevel.nl) — new, not reused from any prior run
- https://www.higherlevel.nl/forums/topic/77956-klant-wil-niet-betalen-zonder-het-ontvangen-van-een-herinnering/ — klant weigert te betalen, beroept zich (onjuist) op art. 6:96 lid 6 BW (Contracten en aanverwante onderwerpen)
- https://www.higherlevel.nl/forums/topic/76432-3-zzpers-rouleren-als-opdrachtgever/ — 3 zzp'ers rouleren wie er als opdrachtgever factureert; schijnzelfstandigheid-risico (Fiscale zaken)
- https://www.higherlevel.nl/forums/topic/74714-naam-op-inkoopfacturen-zzp/ — btw-aftrek bij inkoopfacturen op privénaam i.p.v. handelsnaam (Administratie en verzekeringen)

**New threads seen but skipped this run** (not used by any prior run either, but weaker fit
— kept in reserve for a future week):
- 76161 ("Btw nummer ingetrokken") — genuine and unused, but poster is in financial
  distress after a revoked VAT number; not a considerate spot for a product mention this
  week.
- 75524 ("Zelf jaarrekening en KvK jaarstukken genereren") — about BV jaarrekeningen
  (limited companies), not the eenmanszaak/zzp administration BigDogg serves.
- 77223 ("Automatische verwerking verkoopfacturen via e-boekhouden"), 78255
  ("E-Boekhouden probleem?") — both tied to a specific competitor's own forum/feature
  discussion; awkward entry point for an honest, non-promotional reply.
- 74290 ("Stappenplan klant betaalt factuur niet: hoe te handelen?") — genuine and unused
  as a forum thread, but the non-paying-client topic is already this week's blog post and
  last week's forum reply (72141) — skipped for variety, kept in reserve.
- 74290's older 2023-era cousins (54900, 50020) and other multi-year-old threads
  (66413, 76935, 54587, 55476, 56579, 52813, 71085, 74622) — too old per this routine's
  convention.

**Previously-used threads, not reused** (full list, for cross-reference — see prior run
sections below for detail): 77806, 72165, 72141, 78654, 76922, 74770, 76044, 73554, 76143,
77418, 77625, 78206, 77327, 78005, 77353, 70068, 74715, 25535, 75224, 76672, 77718, 78290,
78124, 78556, 78557, 73546, 63916, 75996, 76202, 72387, 78532, 74434, 56276, 74342, 74909,
74767.

### Blog topic used
- "Klant betaalt de factuur niet? Dit stappenplan werkt (zzp, 2026)" (target keyword: klant
  betaalt factuur niet zzp). Previously only covered as a video-script topic (08-17) and
  briefly in a forum reply (72141, 09-14) — never as a full post. Pairs naturally with this
  week's forum reply on thread 77956. Legal detail (art. 6:96 lid 6 BW scope, wettelijke
  handelsrente) verified via WebSearch across multiple sources; the BigDogg feature mention
  was corrected to match the actual (not fully automatic) behavior of `reminders.py` — see
  "Known constraints" above.
- Remaining not-yet-covered full-post candidates: urencriterium 1225 uur (video only,
  08-17), BTW verleggen (forum-reply angle 08-31 + video topic 09-14, never a full post),
  zzp of eenmanszaak: administratieve verschillen (never used in any format), KIA /
  investeringsaftrek (video topic this week, never a full post).

### Outreach targets contacted (drafted, not sent)
- mijnzzp.nl — listing pitch, **new site this run**. Runs a "Boekhoudsoftware vergelijken"
  page and a redactie/weblogs section. Possible contact `contact@mijnzzp.nl` (found via
  WebSearch, credited to Egbert Wrekenhorst) — unverified, confirm via mijnzzp.nl/Contact
  before sending.
- zzp-centrum.nl — short follow-up (first pitched 08-17, no response recorded in 5 weeks).
  First follow-up sent to this specific site (appwiki.nl was the only site previously
  followed up, on 08-31).
- Independent boekhouder/accountant — referral partnership, **new pitch angle this run**:
  leads with the verified accountant-portal feature (token-gated read-only access, no
  account needed) instead of the generic "in overleg" template every prior run used. Still
  no real recipient identified — same gap flagged by every prior run (9 weeks now).

**All 5 of the original comparison sites named in this routine's instructions** (appwiki.nl,
zzp-centrum.nl, onderneming.nl, ikwordzzper.nl, vergelijk-boekhoudprogramma.nl) plus two
newer targets from prior weeks (ondernemeneninternet.nl, dezaak.nl) have now been pitched.
This run added an eighth target (mijnzzp.nl) rather than re-pitching one without a known
non-response, except for the one deliberate zzp-centrum.nl follow-up above.

### Directory listing status (checked 2026-09-21, via WebSearch only — no account created,
nothing submitted)
| Site | BigDogg listed? |
|---|---|
| appwiki.nl | No |
| zzp-centrum.nl | No |
| onderneming.nl | No |
| ikwordzzper.nl | No |
| vergelijk-boekhoudprogramma.nl | No distinct live site found matching this exact name (unchanged finding across all 9 runs) |
| mijnzzp.nl | No (new site checked this run) |

General searches for "bigdogg" + zzp/facturatie/boekhouden terms also returned no mentions
of BigDogg anywhere — consistent with 9 consecutive runs.

### Video script topics used
- KIA (kleinschaligheidsinvesteringsaftrek) uitgelegd — ties to the real investment/
  depreciation tracking in `app/routers/investments.py` on `master` (describes it
  accurately as depreciation-schedule tracking, does not overclaim it calculates the KIA
  percentage itself, which the code doesn't do)
- Je boekhouder toegang geven zonder wachtwoorden rond te sturen — new topic, showcases the
  accountant-portal feature
- BTW-teruggave duurt te lang — wat kun je doen?

### Ideas / follow-ups for next runs
- **Still priority, flagged a fifth time: ask the founder about merging or closing
  PRs #2–#10.** Root cause of two duplication incidents so far. Flagged via notification
  after this run.
- Consider merging just `marketing/STATE.md` to `main` on its own, decoupled from the
  weekly draft content.
- Re-check `WebFetch` access to higherlevel.nl each run — 9 consecutive runs blocked now.
- Candidate full blog posts not yet written: urencriterium 1225 uur, BTW verleggen, zzp of
  eenmanszaak (administratieve verschillen), KIA/investeringsaftrek.
- Consider whether the founder wants the pricing corrected in the routine's own brief
  (EUR 9.99/month vs. the actual €11.99/month monthly-billed price) so future runs don't
  have to re-derive the yearly-equivalent framing each time.
- Forum topics 76161, 75524, 77223, 78255, 74290 remain available in reserve (see notes
  above on why each was skipped this week) if threads run dry in a future week.

---

## Run: 2026-09-14

**Branch:** `marketing-drafts-2026-09-14`
**Drafts folder:** `marketing/drafts/2026-09-14/`

**PR backlog check:** confirmed PRs #2–#8 all still `open`. Discovered and documented the
09-07 STATE.md regression (see "Known issue" above).

### Forum threads used (higherlevel.nl)
- https://www.higherlevel.nl/forums/topic/77806-behoefte-aan-simpele-facturatietool-zonder-boekhoudcomplexiteit/
- https://www.higherlevel.nl/forums/topic/72165-gevolgen-van-het-niet-voldoen-aan-het-urencriterium/
- https://www.higherlevel.nl/forums/topic/72141-betalingstermijn-op-factuur-overschreden/

### Blog topic used
- "Zakelijke rekening verplicht als zzp'er? Dit zegt de wet (en de praktijk) in 2026"
  (target keyword: zakelijke rekening verplicht zzp)

### Outreach targets contacted (drafted, not sent)
- ondernemeneninternet.nl (new), dezaak.nl (new), independent boekhouder/accountant
  (generic template)

### Directory listing status (checked 2026-09-14)
Not listed on any of the 5 sites (unchanged).

### Video script topics used
- Hoeveel belasting opzij zetten als zzp'er (reserveren)
- BTW verleggen als zzp'er — wanneer moet dat?
- Thuiswerkaftrek: mag je dat als zzp'er?

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
- zzp-centrum.nl (re-pitch), independent boekhouder/accountant (generic), generic zzp
  blog/nieuwsbrief (no specific outlet)

### Directory listing status (checked 2026-09-07)
Same "not listed on any of the 5 sites" result as every other run.

### Video script topics used
- Aftrekposten die zzp'ers vergeten
- Verplichte gegevens op een factuur
- Kilometerregistratie voor zzp'ers

---

## Run: 2026-08-31

**Branch:** `marketing-drafts-2026-08-31`

**PR backlog check:** confirmed PRs #2–#6 all still `open`. First discovered the
`main`/`master` divergence.

### Forum threads used
- topic/78654 (btw verleggen creatieve sector), topic/76922 (foutieve btw-factuur
  corrigeren), topic/74770 (boekhouding een zooitje)

### Blog topic used
- "Kilometerregistratie als zzp'er" (target keyword: kilometerregistratie zzp'er bijhouden)

### Outreach targets
- officetown.nl (new), appwiki.nl (follow-up), independent boekhouder/accountant (generic)

### Video script topics used
- Offerte of factuur? Het verschil
- Mag je bonnetjes weggooien na scannen?
- Aanbetaling vragen? Zo factureer je dat goed

---

## Run: 2026-08-24

**Branch:** `marketing-drafts-2026-08-24`

**PR backlog check:** confirmed PRs #2–#5 all still `open`.

### Forum threads used
- topic/73554 (factuur bij verkoop aan particulieren), topic/76143 (facturen kwijtgeraakt
  bij overstap boekhoudpakket), topic/77418 (creditfactuur-nummering)

### Blog topic used
- "Jaarlijkse IB-aangifte als zzp'er: wat je nodig hebt en hoe je het voorbereidt (2026)"

### Outreach targets
- boekhoudprogrammagids.nl (contact: info@boekhoudprogrammagids.nl, unverified),
  zzpdaily.nl (no contact found), independent boekhouder/accountant (generic)

### Video script topics used
- Wat moet er verplicht op een factuur staan met de KOR
- Zzp-kosten aftrekken: twijfelgevallen
- Waarom je facturen 7 jaar moet bewaren

---

## Run: 2026-08-17

**Branch:** `marketing-drafts-2026-08-17`

### Forum threads used
- topic/77625 (marktkraam btw-split), topic/78206 (factuur met "EU"-btw-nummer,
  KOR-ondernemer), topic/77327 (btw van VVE terugvragen)

### Blog topic used
- "Kleineondernemersregeling (KOR) voor zzp'ers: wel of niet aanmelden in 2026?"

### Outreach targets
- zzp-centrum.nl (contact: info@zzpcentrum.nl, unverified), onderneming.nl (no contact),
  independent boekhouder/accountant (generic)

**All 5 original directory sites pitched at least once as of this run.**

### Video script topics used
- Urencriterium (1.225 uur) voor zelfstandigenaftrek
- Wat te doen bij een niet-betalende klant
- BTW bij internationale klanten/diensten

---

## Run: 2026-08-10

**Branch:** `marketing-drafts-2026-08-10`

**Note (added retroactively by the 08-17 run):** duplicated 07-28/08-03 almost exactly
(couldn't see their history, since neither PR had been merged). First occurrence of the
duplication problem.

### Forum threads used — duplicates of 07-28/08-03
topic/77718, topic/78124, topic/78290

### Blog topic used — duplicate of 07-28
"Eerste factuur maken als zzp'er"

---

## Run: 2026-08-03

**Branch:** `marketing-drafts-2026-08-03`

### Forum threads used
topic/78124 (factuur/kwitantie zonder ondernemerschap), topic/78290 (te vorderen/te betalen
btw op jaarbalans), topic/78556 (opdrachtgever weigert late factuur)

### Blog topic used
"BTW-aangifte doen als beginnend zzp'er: complete uitleg (2026)"

### Outreach targets
vergelijk-boekhoudprogramma.nl/Cloudhints (info@cloudhints.com, unverified), independent
boekhouder/accountant (generic)

---

## Run: 2026-07-28 (first run — `marketing/` created)

**Branch:** `marketing-drafts-2026-07-28`

### Forum threads used
topic/73546 (verwerkingstijd eerste btw-teruggaaf), topic/77718 (factuur met
materiaalopslag), topic/63916 (privé-uitgaven zonder zakelijke rekening)

### Blog topic used
"Je eerste factuur maken als zzp'er: complete stappenplan (2026)"

### Outreach targets
appwiki.nl (contact: rubel@appwiki.nl), independent boekhouder/accountant (generic),
ikwordzzper.nl (contact: info@ikwordzzper.nl)

### Video script topics used
3 verplichte factuuronderdelen, kilometerregistratie tip, btw-over-inclusief-bedrag fout
