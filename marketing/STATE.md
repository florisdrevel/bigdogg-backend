# BigDogg Marketing Engine — state tracker

This file tracks what each weekly run has already covered, so future runs don't repeat
the same forum threads, blog topics, outreach targets, or listing-site pitches. Update
this file at the end of every run, before committing.

## Run log

### 2026-10-26

- **Forum threads replied to (higherlevel.nl)** — do not reuse these threads in future
  weeks, and don't re-pitch the same boards back-to-back without checking for new
  threads first:
  - https://www.higherlevel.nl/forums/topic/78290-balans-te-vorderente-betalen-btw/ (Financiering — BTW balans aansluiting)
  - https://www.higherlevel.nl/forums/topic/77347-wat-te-doen-met-ingeboekte-doch-oninbare-factuur/ (Fiscale zaken — oninbare vordering / btw terugvragen)
  - https://www.higherlevel.nl/forums/topic/77418-creditfactuur-niet-toegepast/ (Fiscale zaken — creditfactuur / factuurnummering)
  - Threads explicitly *avoided* as "flooded with software recommendations" or otherwise
    not a good fit — don't re-suggest these as "new" without checking why they were
    skipped: topic 56276 ("Welk boekhoudpakket voor ZZP-ers?"), topic 65902 ("Aanschaf
    software boekhouden"), topic 78434 ("ZZP Pulse — offline administratie-app... eerlijke
    feedback gezocht" — this is someone else's competing app asking for feedback, not a
    good target to answer/pitch into).

- **Blog post topic:** "Je eerste factuur maken als zzp'er" (target keyword: eerste
  factuur maken als zzp'er). Next weeks should pick a *different* long-tail topic, e.g.
  candidates not yet used: "BTW aangifte doen als beginnend zzp'er", "kilometervergoeding
  zzp 2026", "KOR regeling uitleg voor zzp'ers", "zzp administratie opzetten in een
  middag", "eerste jaar als zzp'er: belastingaangifte stappenplan".

- **Comparison/listing site status check** (via web search only — direct browsing of
  these sites was blocked by the sandbox's network policy, so this is a best-effort check,
  not a guaranteed absence; re-verify manually before relying on it):
  - appwiki.nl — no BigDogg listing found.
  - zzp-centrum.nl — no BigDogg listing found.
  - onderneming.nl — no BigDogg listing found.
  - ikwordzzper.nl — no BigDogg listing found.
  - vergelijk-boekhoudprogramma.nl — could not confirm the site's own content via search
    at all (no indexed pages surfaced); status still unconfirmed, re-check next time with
    a different search approach or ask the founder to check manually.
  - **Conclusion:** BigDogg appears to have zero presence on all five sites as of this
    week.

- **Cold email outreach drafted:**
  - Listing/review pitch sent to: **appwiki.nl** (this week's site — rotate to a
    different one next week, e.g. zzp-centrum.nl or onderneming.nl, don't repeat
    appwiki.nl two weeks running unless there's a specific follow-up reason).
  - Boekhouder/accountant referral pitch: generic template, no specific accountant
    targeted yet (placeholder only) — founder needs to pick an actual local
    boekhoudkantoor before sending. Future runs could suggest a different angle (e.g.
    targeting bookkeeping communities/Facebook groups is out of scope per this routine's
    instructions — accountant outreach is the only People channel in scope besides the
    comparison sites).

- **Video scripts:** BTW-tarief keuze, creditfactuur/dubbele factuur, kilometerregistratie.
  Future weeks: rotate to new topics — ideas not yet used: KOR-regeling uitleg, eerste
  jaar belastingaangifte, uren bijhouden als zzp'er, zakelijke vs. privé kosten scheiden,
  wat te doen bij een niet-betalende klant.

## Known constraints for future runs

- No browser, no logged-in accounts, no ability to post/send/publish — this routine only
  drafts; a human (the founder) reviews and personally posts/sends everything.
- Facebook and LinkedIn are out of scope (require login) — don't attempt to research or
  draft for them.
- Direct `WebFetch`/`curl` access to higherlevel.nl (and possibly other target sites) is
  blocked by the sandbox's outbound network policy (403 from the agent proxy — the
  destination host isn't allowlisted). Forum thread research for this run was done
  entirely via web search snippets, not by reading full threads. **Always tell the founder
  to read the full thread before posting a drafted reply** — search snippets may miss
  replies that already answered the question, corrected a wrong assumption, or linked the
  existing solution.
- Never fabricate specific recipient names, email addresses, or exact current prices on
  third-party sites — always leave placeholders for the founder to fill in after
  verifying manually.
