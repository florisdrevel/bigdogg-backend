# Marketing engine — state log

Tracks what each weekly run has already covered so future runs don't repeat the same
forum threads, blog topics, listing-site pitches, or outreach targets. Update this file
at the end of every run, then commit it along with that week's `marketing/drafts/YYYY-MM-DD/`.

## Known constraints for this routine

- Sandbox has no browser, no logged-in accounts, cannot send/post/publish anything —
  output is drafts only, reviewed and posted/sent by the founder.
- Facebook and LinkedIn are out of scope (require login) — do not research or draft for
  them.
- **WebFetch has returned HTTP 403 for every URL tried across at least two consecutive
  runs now (2026-07-28 and 2026-08-03)** — including unrelated test URLs, not just
  higherlevel.nl or Dutch sites. This looks like a persistent tool-level/sandbox
  restriction, not a per-site block, and has not resolved itself between runs. All
  forum/listing-site research has been done via `WebSearch` snippets only, not full page
  fetches — thread details below (open/closed status, exact reply counts, whether a
  thread has since been flooded with replies) are best-effort from search snippets and
  should be spot-checked by the founder before posting, ideally by opening the thread
  directly in a browser. If a future run gets working WebFetch, use it to verify
  everything below before reusing it.
- **IMPORTANT — the `marketing-drafts-2026-07-28` branch/PR was never merged into
  `main` as of this run (2026-08-03).** `marketing/` did not exist on `main` when this
  run started; this STATE.md was reconstructed from `origin/marketing-drafts-2026-07-28`
  history. Check whether prior-week PRs are getting merged or reviewed — if this keeps
  happening, the founder may be missing the notification, or the branch needs a manual
  look.

## Run: 2026-07-28 (first run — `marketing/` created)

**Forum threads drafted (higherlevel.nl)** — do not reuse these same threads in future
replies; if still unanswered next week they were likely skipped by the founder on
purpose, ask before reusing:
- https://www.higherlevel.nl/forums/topic/73546-eerste-keer-omzetbelasting-aangifte-gedaan-hoe-lang-duurt-de-verwerking/ (verwerkingstijd eerste btw-teruggaaf)
- https://www.higherlevel.nl/forums/topic/77718-vakman-zzp-factuur-maken-met-opslag/ (factuur met materiaalopslag)
- https://www.higherlevel.nl/forums/topic/63916-zzp-geen-zakelijke-rekening-alle-priv%C3%A9-uitgaven-in-boekhouding-zetten-of-niet/ (privé-uitgaven in boekhouding zonder zakelijke rekening)

**Threads seen but deliberately skipped** (avoid re-surfacing without a reason):
- topic/72387 (factuurnummering per opdrachtgever) — dated Nov 2021, not "recent".
- topic/56276 and topic/74342 (boekhoudpakket-advies threads) — already flooded with
  software-recommendation replies, per the routine's own instructions to avoid those.
- topic/78532 ("alles-in-één tool voor zzp'ers") and topic/74434 ("ZZP Pulse") — these are
  other builders' own self-promo/feedback threads, not neutral ground for a competing
  founder to reply on.

**Blog post drafted:** "Je eerste factuur maken als zzp'er: complete stappenplan (2026)" —
keyword: eerste factuur maken als zzp'er.

**Listing-site status check** (as of 2026-07-28, via WebSearch only — no account created,
nothing submitted):
- appwiki.nl — not listed on boekhouding/zzp comparison pages. Advertising contact found:
  rubel@appwiki.nl. **Pitched this week.**
- zzp-centrum.nl — not listed on "Top 10 software voor zzp" / boekhouding comparison.
  Not yet pitched at that point.
- onderneming.nl — not listed on "10 Boekhoudprogramma's voor ZZP" page. Not yet pitched
  at that point.
- ikwordzzper.nl — not listed on boekhoudprogramma's/facturatiesoftware comparison.
  Contact: info@ikwordzzper.nl. **Pitched this week** (guest content + listing ask).
- vergelijk-boekhoudprogramma.nl (Cloudhints) — not listed. Contact found:
  info@cloudhints.com. Not yet pitched at that point.

**Cold emails drafted:** appwiki.nl listing pitch, generic boekhouder/accountant referral
template (no specific recipient — founder must pick a real contact), ikwordzzper.nl guest
content pitch.

**Video scripts drafted:** (1) 3 verplichte factuuronderdelen, (2) kilometerregistratie
tip, (3) btw-over-inclusief-bedrag fout.

**PR:** branch `marketing-drafts-2026-07-28`, opened against default branch. **Not yet
merged as of 2026-08-03** — see constraint note above.

## Run: 2026-08-03

**Forum threads drafted (higherlevel.nl)** — new threads, distinct from 2026-07-28's list
above; do not reuse these same threads in future replies without checking if they got a
response first:
- https://www.higherlevel.nl/forums/topic/78124-factuur-sturen-echter-geen-ondernemer-geen-inschrijfverplichting-handelsregister/
  (mag je als niet-ondernemer een "factuur"/kwitantie sturen — Dec 2025)
- https://www.higherlevel.nl/forums/topic/78290-balans-te-vorderente-betalen-btw/
  (te vorderen/te betalen btw op de jaarbalans, bol.com-verkoper — early 2026, unanswered
  per last WebSearch check, good target)
- https://www.higherlevel.nl/forums/topic/78556-mag-een-opdrachtgever-een-factuur-weigeren-omdat-deze-enkele-maanden-later-is-verstuu/
  (opdrachtgever weigert late factuur te betalen — project afgerond dec 2025)

**Threads seen but deliberately skipped this run:**
- topic/75996 ("Belastingdienst vraagt specificaties BTW aangifte") — confirmed via
  WebSearch snippet as "gesloten voor nieuwe reacties" (closed to new replies), can't
  post there.
- topic/76202 ("KOR / loondienst / ZZP / wat moet ik doen?") — dated Feb 2024, not
  "recent" enough.
- topic/78557 ("Vertragingsbrief tot maart 2027 van de Belastingdienst") — recent but is
  a general IB-aangifte-delay grumble thread, not really an invoicing/bookkeeping/
  BTW/admin-tool question a helpful reply would naturally fit.

**Blog post drafted:** "BTW-aangifte doen als beginnend zzp'er: complete uitleg (2026)" —
keyword: btw aangifte doen als beginnend zzp'er. This was one of the adjacent topics
flagged as not-yet-covered by the 2026-07-28 run.
- Adjacent long-tail topics still NOT yet covered, candidates for future runs:
  "kilometerregistratie zzp uitgelegd" (as a full blog post — has only had a short video
  script so far), "KOR kleineondernemersregeling wel of niet zzp" (as a full blog post —
  covered briefly in this week's video script, not as a dedicated post), "zakelijke
  rekening verplicht zzp?" (same — covered as video script this week, not blog),
  "jaarlijkse IB-aangifte zzp'er uitgelegd" (covered as video script this week, not
  blog).

**Listing-site status check** (as of 2026-08-03, via WebSearch only — BigDogg confirmed
absent from all comparison pages checked):
- appwiki.nl — still not listed. Pitched last week (2026-07-28) — do not re-pitch
  until there's a response or several weeks have passed.
- zzp-centrum.nl — still not listed on their "Beste boekhoudprogramma zzp" pages. Not
  yet pitched — candidate for next run.
- onderneming.nl — still not listed on "10 Boekhoudprogramma's voor ZZP". Not yet
  pitched — candidate for next run.
- ikwordzzper.nl — pitched last week (2026-07-28) — do not re-pitch until there's a
  response or several weeks have passed.
- vergelijk-boekhoudprogramma.nl (Cloudhints) — still not listed. **Pitched this week**
  (see cold-emails.md #1), reusing the info@cloudhints.com contact found last week
  (unverified by direct fetch — founder should confirm before sending).
- Next run: rotate to zzp-centrum.nl or onderneming.nl for the comparison-site pitch —
  contact addresses for those two still need to be found (WebSearch didn't surface a
  specific email for either this run, only general contact-page mentions).

**Cold emails drafted:** vergelijk-boekhoudprogramma.nl listing pitch, generic
boekhouder/accountant referral template (no specific recipient — founder must pick a
real contact, same caveat as last week).

**Video scripts drafted:** (1) KOR uitgelegd in 30 seconden, (2) jaarlijkse IB-aangifte
nieuw voor zzp'ers, (3) zakelijke rekening verplicht of niet. Adjacent topics not yet
covered as videos: btw bij internationale klanten/diensten, urencriterium (1225 uur) voor
zelfstandigenaftrek, wat te doen bij een niet-betalende klant.

**PR:** branch `marketing-drafts-2026-08-03`, opened against default branch.
