# Forum reply drafts — higherlevel.nl (week of 2026-10-19)

**Research note:** `WebFetch` to higherlevel.nl failed again this run (`getaddrinfo ENOTFOUND www.higherlevel.nl` — this sandbox still cannot reach the domain at all). This is now the **13th consecutive week** this has happened (first flagged 2026-07-28). All three threads below were found via `WebSearch` snippets only — titles, boards, and approximate ages are confirmed from the snippets, but full thread content, exact dates, and current reply counts were **not** independently verified. Please open each thread directly before posting to confirm it's still open and the tone still fits.

None of these three threads have been used in any prior week's drafts (checked against the full history in `STATE.md`, which now covers 12 prior weeks).

---

## 1. Hoe houden jullie als online verkoper je boekhouding bij met meerdere platforms?

**Thread:** https://www.higherlevel.nl/forums/topic/78515-hoe-houden-jullie-als-online-verkoper-je-boekhouding-bij-met-meerdere-platforms/
**Board:** Administratie en verzekeringen
**Context:** A zzp'er selling on multiple platforms (e.g. Etsy, Payhip) asks how others keep their bookkeeping straight when payouts bundle revenue from several channels, fees, and refunds into one lump sum.

**Draft reply (Dutch):**

> Herkenbaar probleem — ik heb dit zelf ook jarenlang met losse Excel-sheets opgelost voordat ik BigDogg bouwde, en de kern van wat werkt is eigenlijk steeds hetzelfde: zorg dat je per uitbetaling de onderdelen uit elkaar trekt vóórdat het in je boekhouding komt, niet erna.
>
> Concreet wat ik zou doen:
> - Kijk of het platform een transactie- of verkooprapport exporteert (los van de uitbetaling). Etsy en de meeste marketplaces hebben dit, Payhip iets minder uitgebreid.
> - Boek bruto-omzet, platformkosten en eventuele terugbetalingen als losse regels, niet als één nettobedrag. Anders klopt je btw-aangifte niet (je moet btw afdragen over de omzet, niet over wat er na kosten overblijft).
> - Eén map/ordner per platform per kwartaal met de exports helpt enorm als de Belastingdienst ooit vraagt om onderbouwing.
>
> Ik heb dit soort multi-platform afrekeningen uiteindelijk ook als los onderdeel in BigDogg (de facturatie-app die ik heb gebouwd) ingebouwd, puur omdat ik het zelf steeds opnieuw moest uitzoeken — maar los van welke tool je gebruikt, is "nooit een lump sum boeken zonder uitsplitsing" denk ik de belangrijkste regel hier.

---

## 2. Vraag over eigen vermogen inkomstenbelasting

**Thread:** https://www.higherlevel.nl/forums/topic/77505-vraag-over-eigen-vermogen-inkomstenbelasting/
**Board:** Fiscale zaken
**Context:** A question about how a zzp'er's eigen vermogen (equity/capital) in the business interacts with their personal income tax position — a recurring confusion point for sole proprietors who don't have a formal balance sheet the way a BV does.

**Draft reply (Dutch):**

> Dit is een van die dingen die bij een eenmanszaak makkelijk door elkaar lopen, omdat er geen harde scheiding is tussen "jouw geld" en "bedrijfsgeld" zoals bij een bv.
>
> Een paar punten die voor mij hielpen dit scherp te krijgen:
> - Je eigen vermogen in de zaak is fiscaal geen aparte "pot" — het is een rekenkundig gevolg van je balans (bezittingen min schulden), niet iets waarover je apart belasting betaalt.
> - Winst wordt belast via de IB-aangifte (box 1, resultaat uit onderneming), los van of je die winst uit de zaak haalt of laat staan. Geld opnemen voor privé verandert dus niets aan wat er belast wordt — het verandert alleen je eigen vermogen op de balans.
> - Waar het wél meespeelt: je ondernemersaftrekken (zelfstandigenaftrek, MKB-winstvrijstelling) werken via de winst, niet via het vermogen. Dus een hoog eigen vermogen op zich levert geen extra aftrek op.
>
> Ik zou dit zeker nog even check bij een boekhouder of de Belastingdienst-rekenhulp als het om een concreet bedrag gaat — maar het "waarom" achter de regel is denk ik vooral dat een eenmanszaak fiscaal geen rechtspersoon is, dus er is geen aparte belasting op het vermogen zelf zoals bij een bv (vpb) — alleen op de winst.

---

## 3. Kan ik sponsoring van open-source projecten opvoeren als kosten voor mijn ZZP?

**Thread:** https://www.higherlevel.nl/forums/topic/73038-kan-ik-sponsoring-van-open-source-projecten-opvoeren-als-kosten-voor-mijn-zzp/
**Board:** Fiscale zaken
**Context:** A zzp'er (likely a developer/technical freelancer) asks whether sponsoring an open-source project they use professionally counts as a deductible business expense.

**Draft reply (Dutch):**

> Ik heb dit zelf ook uitgezocht (ik bouw software, dus leun zelf ook op een paar open-source libraries) en de vuistregel die ik ervan heb overgehouden: het draait om het zakelijke karakter van de uitgave, niet om de vorm ("sponsoring" klinkt als iets anders dan een gewone inkoopfactuur, maar fiscaal is het dat niet per se).
>
> Wat volgens mij telt:
> - Gebruik je de software/het project daadwerkelijk zakelijk (in je eigen dienstverlening of product)? Dan is een redelijke sponsorbijdrage te verdedigen als zakelijke kosten, net als een betaalde licentie zou zijn.
> - Is er een reclame-/naamsvermelding-component (bijv. je logo op hun sponsorpagina)? Dan ligt "zakelijke kosten" nog meer voor de hand — het heeft dan ook een marketingkant.
> - Puur sponsoren uit sympathie, zonder zakelijk gebruik of vermelding, is lastiger te onderbouwen als het ter discussie komt bij een controle.
>
> Bewaar in elk geval de factuur/bevestiging van het sponsorplatform (GitHub Sponsors, Open Collective, etc.) net zoals je elke andere inkoopfactuur zou bewaren — dat is denk ik het belangrijkste praktische punt, los van de discussie over de aftrekbaarheid zelf. Voor de zekerheid zou ik dit wel één keer concreet langs een boekhouder leggen, want "nieuw" soort kosten zoals dit wordt niet altijd eenduidig beoordeeld.
