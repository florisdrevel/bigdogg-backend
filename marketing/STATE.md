# Marketing engine — state log

Tracks what each weekly run has already covered so future runs don't repeat the same
forum threads, blog topics, listing-site pitches, or outreach targets. Update this file
at the end of every run, then commit it along with that week's `marketing/drafts/YYYY-MM-DD/`.

## Known constraints for this routine

- Sandbox has no browser, no logged-in accounts, cannot send/post/publish anything —
  output is drafts only, reviewed and posted/sent by the founder.
- Facebook and LinkedIn are out of scope (require login) — do not research or draft for
  them.
- 2026-07-28 run: `WebFetch` returned 403 for every URL tried, including non-Dutch,
  unrelated test URLs (e.g. example.com) — this looks like a tool-level issue in the
  sandbox that session, not a per-site block. All forum/listing-site research that run
  was done via `WebSearch` snippets only, not full page fetches. If this recurs, note it
  again here; if a future run gets working WebFetch, use it to verify the details below
  (exact thread dates, current reply counts, whether threads are still open) before
  reusing anything.

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
- Adjacent long-tail topics NOT yet covered, candidates for future runs: "BTW aangifte
  doen als beginnend zzp'er", "kilometerregistratie zzp uitgelegd", "KOR
  kleineondernemersregeling wel of niet zzp", "zakelijke rekening verplicht zzp?".

**Listing-site status check** (as of 2026-07-28, via WebSearch only — no account created,
nothing submitted):
- appwiki.nl — BigDogg not listed on their boekhouding/zzp comparison pages. Free
  vendor self-registration portal exists; advertising contact found: rubel@appwiki.nl.
  **Pitched this week** (see cold-emails.md #1).
- zzp-centrum.nl — BigDogg not listed on their "Top 10 software voor zzp" / boekhouding
  comparison pages. Not yet pitched — candidate for next run.
- onderneming.nl — BigDogg not listed on their "10 Boekhoudprogramma's voor ZZP" page.
  Not yet pitched — candidate for next run.
- ikwordzzper.nl — BigDogg not listed on their boekhoudprogramma's/facturatiesoftware
  comparison pages. Contact: info@ikwordzzper.nl. **Pitched this week** (guest content +
  listing ask, see cold-emails.md #3).
- vergelijk-boekhoudprogramma.nl (Cloudhints) — BigDogg not listed. Contact found:
  info@cloudhints.com. Not yet pitched — candidate for next run.

**Cold emails drafted:** appwiki.nl listing pitch, generic boekhouder/accountant referral
template (no specific recipient — founder must pick a real contact), ikwordzzper.nl guest
content pitch.
- Next run: rotate to zzp-centrum.nl, onderneming.nl, or vergelijk-boekhoudprogramma.nl
  for the comparison-site pitch (don't repeat appwiki.nl/ikwordzzper.nl until there's a
  response or enough time has passed).

**Video scripts drafted:** (1) 3 verplichte factuuronderdelen, (2) kilometerregistratie
tip, (3) btw-over-inclusief-bedrag fout. Adjacent topics not yet covered: KOR uitleg,
jaarlijkse IB-aangifte voor zzp'ers, zakelijk vs. privé bankrekening.

**PR:** branch `marketing-drafts-2026-07-28`, opened against default branch.
