# BigDogg Marketing — run history

Tracks what each weekly marketing run has covered, so future runs avoid repeating the same
forum threads, blog topics, outreach targets, and directory-listing checks. Update this
file every run — add the new "Run" section at the top, most recent first.

## ⚠️ Known issue: prior weekly PRs are still unmerged

As of this run (2026-08-17), **none of the three previous weekly marketing PRs have been
merged**: `marketing-drafts-2026-07-28` (PR #2), `marketing-drafts-2026-08-03` (PR #3), and
`marketing-drafts-2026-08-10` (PR #4) are all still open against `main`. Because each
week's branch is cut from `main`, and `main` has never received a merge, **`marketing/`
does not exist on `main`** — every run so far has branched off a version of the repo with
no memory of prior weeks' `STATE.md`.

This caused a real duplication problem: the 2026-08-10 run could not see 2026-07-28's or
2026-08-03's history and ended up **re-using the exact same 3 forum threads** as
2026-08-03 (topics 77718, 78124, 78290), **re-using the same blog topic** ("eerste factuur
maken") as 2026-07-28, and **re-pitching appwiki.nl**, which had already been pitched twice
before. That work was wasted.

This run (2026-08-17) reconstructed full history by reading the `STATE.md` from all three
unmerged branches directly (`git show origin/marketing-drafts-<date>:marketing/STATE.md`)
before doing any new research, and consolidated it below. **If the founder merges (or
closes) PRs #2, #3, and #4, this consolidation step won't be needed going forward** — future
runs will just read `marketing/STATE.md` on `main` as originally designed. Until then,
future runs should keep doing this manual reconstruction across all open
`marketing-drafts-*` branches, not just read `main`.

## Known constraints for this routine

- Sandbox has no browser, no logged-in accounts, cannot send/post/publish anything — output
  is drafts only, reviewed and posted/sent by the founder.
- Facebook and LinkedIn are out of scope (require login) — do not research or draft for them.
- `WebFetch` to higherlevel.nl has been blocked every run so far (2026-07-28 through
  2026-08-17 — 4 consecutive runs, `EGRESS_BLOCKED` this run specifically). All forum/
  listing-site research has been done via `WebSearch` snippets only, not full page fetches.
  Thread details (open/closed status, reply counts, exact wording) are best-effort from
  search snippets — the founder should open each thread directly before posting.

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
