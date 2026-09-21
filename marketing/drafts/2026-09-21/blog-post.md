# Blog post — week of 2026-09-21

**Suggested title:** Klant betaalt de factuur niet? Dit stappenplan werkt (zzp, 2026)
**Meta description:** Een klant die niet betaalt is vervelend, maar je hebt als zzp'er meer
opties dan je denkt. Dit stappenplan laat zien wat je wanneer kunt doen — van herinnering
tot incassobureau.
**Target keyword:** klant betaalt factuur niet zzp

Topic chosen because: it's a long-tail search a zzp'er only types when they're already
stressed about it (high intent), it was previously only covered as a video-script topic
(08-17) and touched on briefly in one forum reply (72141, 09-14) — never as a full post —
and it pairs naturally with this week's forum reply on thread 77956, which hits the exact
same problem. Legal points (art. 6:96 lid 6 BW, wettelijke handelsrente) verified via
WebSearch against multiple sources; feature claims verified against `app/routers/reminders.py`
on `master` (not `main`, which is stale — see STATE.md).

---

# Klant betaalt de factuur niet? Dit stappenplan werkt (zzp, 2026)

Je hebt het werk gedaan, de factuur verstuurd, en dan: stilte. Geen betaling, geen reactie,
of een smoesje dat steeds terugkomt. Als zzp'er is een klant die niet (op tijd) betaalt een
van de meest voorkomende — en meest stressvolle — administratieve problemen. Het goede
nieuws: er is een vaste volgorde van stappen die werkt, en je hebt als ondernemer meer
rechten dan veel starters denken.

## Stap 1: check de betalingstermijn — en wat er in je voorwaarden staat

Voordat je actie onderneemt: is de betalingstermijn eigenlijk al verstreken? Staat er geen
termijn op je factuur of in je algemene voorwaarden, dan geldt wettelijk een termijn van 30
dagen na factuurdatum voor overeenkomsten tussen bedrijven (b2b). Bij consumenten geldt
dezelfde 30 dagen, tenzij je een langere termijn hebt afgesproken.

Heb je een kortere termijn afgesproken (14 dagen is bij zzp'ers gebruikelijk)? Dan is dát de
termijn die telt, zolang je klant daarmee akkoord is gegaan (bijvoorbeeld door de offerte te
accepteren of je voorwaarden te aanvaarden). Dit is meteen de reden waarom het de moeite
waard is om altijd een betalingstermijn en je voorwaarden expliciet op de factuur te zetten —
niet omdat het verplicht is, maar omdat het je positie later sterker maakt.

## Stap 2: de vriendelijke herinnering

Zodra de termijn is verstreken, stuur je een eerste herinnering. Houd deze toon zakelijk maar
niet dreigend — in veel gevallen is een gemiste betaling gewoon een kwestie van vergeten of
een interne administratieve vertraging bij de klant, geen onwil.

Wat een goede herinnering bevat:
- Het factuurnummer en de vervallen datum
- Het openstaande bedrag
- Een vriendelijk verzoek om alsnog binnen bijvoorbeeld 7 dagen te betalen
- Je bankgegevens nogmaals, voor het geval de eerste factuur is kwijtgeraakt

Reageert de klant niet binnen die nieuwe termijn, dan ga je door naar stap 3.

## Stap 3: de aanmaning (en wat er juridisch verandert)

Een aanmaning is formeler dan een herinnering: je stelt de klant hier expliciet in gebreke
en geeft een laatste termijn (meestal 14 dagen) om te betalen, vóórdat je verdere stappen
onderneemt zoals het in rekening brengen van incassokosten en wettelijke rente.

Belangrijk om te weten: die verplichte "14-dagenbrief" vóórdat je incassokosten mag
berekenen (art. 6:96 lid 6 BW) geldt **alleen als je klant een consument is** — een
particulier die niet handelt vanuit een beroep of bedrijf. Factureer je aan een ander
bedrijf of een andere zzp'er die zakelijk heeft afgenomen, dan gelden gewoon de voorwaarden
die jij zelf hanteert. Veel zzp'ers weten dit niet, en soms proberen (zakelijke) klanten dit
artikel juist aan te halen om onder een betaling uit te komen terwijl het helemaal niet op
hen van toepassing is. Twijfel je of jouw situatie hieronder valt, laat het dan kort door een
jurist of je rechtsbijstandsverzekering checken — vooral bij grotere bedragen.

Na een geldige aanmaning mag je bij een zakelijke klant:
- Wettelijke handelsrente rekenen (voor 2026 doorgaans hoger dan de "gewone" wettelijke
  rente — check het actuele percentage op belastingdienst.nl of rijksoverheid.nl, want dit
  wordt halfjaarlijks aangepast)
- Redelijke incassokosten in rekening brengen, mits dat in je voorwaarden staat

## Stap 4: incassobureau of naar de rechter?

Blijft betaling ondanks aanmaning uit, dan heb je twee vervolgroutes:

**Incassobureau.** Sneller en goedkoper dan een rechtszaak. Een incassobureau neemt het
contact met je klant over en werkt vaak op no-cure-no-pay-basis voor kleinere bedragen. Voor
de meeste zzp'ers is dit de logische volgende stap bij bedragen die de moeite waard zijn om
te incasseren, maar niet groot genoeg zijn om zelf tijd in een juridische procedure te
steken.

**Gerechtelijke procedure.** Bij grotere bedragen, of als een klant de vordering inhoudelijk
betwist, kan een gang naar de kantonrechter (tot €25.000) nodig zijn. Dit kost meer tijd en
vaak ook geld (griffierecht), dus weeg dit af tegen het bedrag en de kans dat je het
uiteindelijk toch geïnd krijgt.

## Voorkomen is makkelijker dan innen

Een paar dingen die het risico op niet-betalende klanten vooraf al verkleinen:

- **Zet altijd een duidelijke betalingstermijn en je voorwaarden op de factuur.** Dit is
  geen bureaucratie — het is precies wat je sterker maakt zodra het misgaat.
- **Vraag bij grotere opdrachten een aanbetaling.** Zo loop je nooit het volle risico over
  het hele bedrag.
- **Volg openstaande facturen actief op, niet pas als het je toevallig opvalt.** Veel
  zzp'ers merken een verlopen factuur pas op als ze toch even in hun boekhouding kijken —
  tegen die tijd is er soms al veel tijd verstreken.

Dat laatste punt is precies waarom ik BigDogg heb gebouwd zoals het nu werkt: zodra een
factuur de betalingstermijn passeert, krijg je automatisch een melding dat hij openstaat —
maar BigDogg mailt je klant nooit uit zichzelf. Jij ziet de melding, en met één tik op
"Stuur herinnering" gaat de mail naar je klant, in het Nederlands of Engels, met het bedrag
en het aantal dagen dat de factuur al open staat. Geen spreadsheet bijhouden welke factuur
je al wel of niet hebt nagebeld — en geen risico dat een klant automatisch een mail krijgt
zonder dat jij dat wilde.

## Kort samengevat

1. Check de betalingstermijn (wettelijk 30 dagen, tenzij anders afgesproken)
2. Stuur een vriendelijke herinnering
3. Stuur een formele aanmaning met een laatste termijn — let op: de "14-dagenbrief"-regel
   geldt alleen bij consumenten, niet bij zakelijke klanten
4. Zet bij aanhoudende non-betaling een incassobureau in, of overweeg de kantonrechter bij
   grotere bedragen
5. Voorkom het risico vooraf met duidelijke voorwaarden, een aanbetaling bij grote klussen,
   en actieve opvolging van openstaande facturen

Een niet-betalende klant is nooit leuk, maar met een duidelijke, rustige opvolging kom je in
de meeste gevallen alsnog aan je geld — zonder dat het je weken kwijt hoeft te maken.

---

*BigDogg is boekhouden en facturatie voor Nederlandse zzp'ers — vanaf €9,99 per maand bij
een jaarabonnement, 30 dagen gratis proberen zonder creditcard.*
