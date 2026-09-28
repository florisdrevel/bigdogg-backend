# BigDogg Marketing — Run State

Tracking file so each weekly run avoids repeating the same forum threads,
blog topics, listing-site pitches, or video-script tips. Update this file
every run under a new dated section (newest first). Never delete history —
future runs need it to avoid duplicates.

**Goal:** 0 → 2,000 paying users by end of 2026. Free channels only, no paid
ads. This session only researches and drafts — it never posts, sends,
signs up, or touches payment details.

---

## 2026-09-28 (first run)

**Environment note (important for future runs):** this sandbox's network
egress policy blocks `higherlevel.nl` outright (`WebFetch` → `EGRESS_BLOCKED`;
raw `curl` → `403` on the CONNECT tunnel). This is an org-level policy block,
not a transient error — don't waste time retrying it or trying to route
around it with a different tool. `WebSearch` still works and returns
titles/URLs/snippets, which is what this run's forum-reply drafts are based
on. **Full thread content, current reply count, and posting dates could not
be verified.** If this is still blocked next run, keep using WebSearch-only
research for forum threads and keep flagging the same caveat in
`forum-replies.md`. If a future run finds the block lifted, verify full
thread content before drafting and drop the caveat.

**Forum threads used (higherlevel.nl) — do not reuse these same threads:**
- `topic/78124-factuur-sturen-echter-geen-ondernemer-geen-inschrijfverplichting-handelsregister` — factuur sturen zonder KvK-inschrijving
- `topic/73546-eerste-keer-omzetbelasting-aangifte-gedaan-hoe-lang-duurt-de-verwerking` — verwerkingstijd eerste BTW-aangifte
- `topic/76432-3-zzpers-rouleren-als-opdrachtgever` — roulerend factureren tussen zzp'ers

**Other higherlevel.nl threads seen but NOT used this week** (candidates for
future weeks, or explicitly skip if reasoning given):
- `topic/60730-eerste-keer-aangifte-inkomstenbelasting-ib-als-zzper` — eerste IB-aangifte (income tax, less core to invoicing — good backup)
- `topic/78264-hoe-toon-ik-belgische-btw-aan-om-terug-te-vorderen` — cross-border BTW reclaim, fairly niche
- `topic/78234-zo-overleef-je-je-eerste-btw-aangifte...` — this is a Higherlevel *article* (by accountant Thijmen), not a discussion thread — not suitable for a forum reply, could be a good backlink/comment target instead
- `topic/78532-wat-vinden-jullie-van-mijn-alles-in-een-tool-voor-zzpers` — **skip**: someone else promoting their own competing tool in the thread; not an appropriate/organic place for us to reply
- `topic/56579-zzper-en-btw-aangifte`, `topic/56127-inkomstenbelasting-zzp` — older threads, check if still active before reusing

**Blog topic used:** "Je eerste factuur maken als zzp'er" (keyword: *eerste
factuur maken als zzp'er*). File: `marketing/drafts/2026-09-28/blog-post.md`.

**Blog topics NOT yet covered (use one per future week, don't repeat):**
- BTW aangifte doen als beginnend zzp'er (mentioned in the original brief — good pick for next week)
- Zelfstandigheidsverklaring / schijnzelfstandigheid uitleg voor zzp'ers
- Kilometervergoeding en reiskosten aftrekken als zzp'er
- Zzp en pensioen opbouwen (long-tail, high search intent, low competition)
- Eerste jaar zzp: welke kosten mag je aftrekken
- Btw-vrijstelling (KOR) uitleg: wel of niet kiezen als starter

**Comparison-site listing status checked this week** (via public web search,
no login — see caveat above, could not view every page in full):
- **appwiki.nl** — no mention of BigDogg found; active general software-comparison site
- **onderneming.nl** (`/boekhoudprogramma/zzp/`) — no mention of BigDogg found; active "10 boekhoudprogramma's" list
- **ikwordzzper.nl** — no mention of BigDogg found; very active, comparison page updated September 2026 — **pitched this week** (see `cold-emails.md`)
- **zzp-centrum.nl** — no mention of BigDogg found; has a "Top 10 software voor zzp" page
- **vergelijk-boekhoudprogramma.nl** — did **not** surface in search results at all this week (not even as a dead/old page). Could not confirm the domain exists or is still live. **Action for next run:** try again, and if it still doesn't turn up, treat it as defunct and drop it from the brief's target list.

**Listing pitch sent (drafted) this week:** ikwordzzper.nl (primary),
onderneming.nl (backup draft included). **Next week:** pitch a different
site (zzp-centrum.nl or appwiki.nl) — don't re-pitch the same site same week
after week without a reply.

**Cold-email boekhouder/accountant outreach:** generic template drafted this
week (`cold-emails.md` #2), no specific firm targeted (task instructions say
don't fabricate recipient names — founder should pick a real local
boekhouder they know or find one). **Next week:** if the founder mentions
having contacted anyone, note who here so we don't draft a duplicate to the
same person.

**Video script tips used:** (1) BTW — aftrekbare voorbelasting op zakelijke
kosten, (2) facturatie — betaaltermijn + factuurnummer voorkomt laat betalen,
(3) kilometerregistratie — bijhouden per rit, €0,23/km 2026-tarief.
**Note:** BigDogg does not currently have a dedicated mileage-tracking
feature (checked the app's routers — only products/invoicing, BTW quarterly
report, financial overview exist in the backend). The km script treats
mileage as a manual expense line, not a built-in tracker — don't overclaim
in future scripts either, unless the feature actually ships.

**Product facts used this run** (given in the task brief, not all verified
against this backend repo — confirm before external use if they change):
€9.99/month, 30-day trial with no card required, referral: 2 friends
referred = 1 free month, capped at 3 bonus months.

**Next run should:**
1. Re-check whether higherlevel.nl is still blocked; adjust research approach accordingly.
2. Pick 2-3 *different* higherlevel.nl threads (see "not used" list above, or find new ones).
3. Use a blog topic from the "not yet covered" list above.
4. Try `vergelijk-boekhoudprogramma.nl` again; pitch a different comparison site.
5. Ask the founder (via PR description or a note) whether any of last week's drafts were actually posted/sent, and if so, what response they got — useful signal for what to try next.
