# Blog post draft — for bigdogg.nl/blog (week of 2026-10-19)

**Suggested title:** Zzp of eenmanszaak: wat is het verschil (en wat betekent dat voor je administratie)?
**Meta description:** Zzp is geen rechtsvorm — de meeste zzp'ers zijn een eenmanszaak. Wat betekent dat voor je administratie, boekhouding en belasting? Een helder overzicht voor 2026.
**Target keyword:** zzp of eenmanszaak administratieve verschillen

**Note on topic selection:** this is a new long-tail topic, not previously used as a blog post, video script, or forum reply in any of the 12 prior weeks (see `marketing/STATE.md`). It was flagged as a candidate back in the very first run (2026-07-28) and has stayed on the "not yet covered" list ever since. Product-feature mentions below are grounded in the real `master` branch codebase (`app/routers/invoices.py`, `app/routers/overview.py`, `app/constants/tax_rates.py`, `app/routers/subscription.py`) — not the stale `main` branch every marketing PR currently targets (see `STATE.md` for why that distinction matters).

---

## Zzp of eenmanszaak: wat is het verschil (en wat betekent dat voor je administratie)?

Je noemt jezelf zzp'er, je collega's noemen je zzp'er, en de Belastingdienst stuurt je post gericht aan je eenmanszaak. Verwarrend? Dat is het ook — en het is een van de meest gestelde vragen van startende zelfstandigen. Het korte antwoord: **zzp is geen rechtsvorm**. Het is een manier om over jezelf te praten, geen juridische status. Wat je wél hebt, is een rechtsvorm — en voor de overgrote meerderheid van zzp'ers is dat een eenmanszaak.

In dit artikel leggen we uit wat het verschil precies betekent, welke administratieve verplichtingen erbij horen, en waar mensen in de praktijk het vaakst over struikelen.

### Zzp is een manier van werken, geen rechtsvorm

"Zzp'er" staat voor zelfstandige zonder personeel. Het zegt iets over hoe je werkt (zelfstandig, zonder mensen in dienst), niet over hoe je juridisch bent ingeschreven. Bij de Kamer van Koophandel kun je je dan ook niet inschrijven als "zzp" — je kiest een rechtsvorm, en in de praktijk is dat voor zzp'ers vrijwel altijd de **eenmanszaak**.

Een eenmanszaak is de simpelste rechtsvorm die Nederland kent: één eigenaar, geen aparte rechtspersoon, geen notaris nodig om te starten. Jij en je onderneming zijn juridisch en fiscaal één en hetzelfde. Dat heeft grote gevolgen voor je administratie — in positieve en in minder positieve zin.

### Wat betekent dit voor je boekhouding?

Omdat een eenmanszaak geen rechtspersoon is, geldt er geen verplichting tot het opstellen en deponeren van een officiële jaarrekening, zoals bij een bv wel moet. Je houdt een **enkelvoudige boekhouding** bij: inkomsten, uitgaven, een eenvoudige winst- en verliesrekening en een balans. Geen dubbel boekhouden, geen accountantscontrole verplicht.

Wat blijft wel verplicht, voor iedere ondernemer, eenmanszaak of niet:
- Je houdt je administratie **7 jaar** bewaard (facturen, bonnetjes, bankafschriften).
- Je administratie moet controleerbaar zijn voor de Belastingdienst — dus overzichtelijk, volledig en op tijd bijgewerkt.
- Je stuurt facturen die aan de wettelijke eisen voldoen (NAW-gegevens, KvK-nummer, btw-nummer, factuurnummer, btw-bedrag apart vermeld).
- Je doet (meestal per kwartaal) btw-aangifte, tenzij je de KOR (kleineondernemersregeling) hebt gekozen.

Het verschil met een bv zit vooral in de **zwaarte** van die administratie, niet in de basisverplichtingen. Een bv moet een jaarrekening opstellen en deponeren bij de KvK, heeft te maken met vennootschapsbelasting naast de eigen inkomstenbelasting van de eigenaar, en is als rechtspersoon strikter gescheiden van je privévermogen. Dat laatste is meteen ook het grootste nadeel van de eenmanszaak: je bent **persoonlijk aansprakelijk** voor de schulden van je onderneming, met je privévermogen. Bij een bv is die aansprakelijkheid in principe beperkt tot het bedrijfsvermogen.

### Fiscaal: hoe werkt de belasting bij een eenmanszaak?

Bij een eenmanszaak wordt de winst van je onderneming gewoon bij je persoonlijke inkomen opgeteld en belast via de **inkomstenbelasting** (box 1, resultaat uit onderneming). Je betaalt dus geen apart tarief zoals de vennootschapsbelasting die een bv betaalt — maar daardoor val je ook sneller in een hoger belastingtarief als je onderneming goed loopt.

Daar staat tegenover dat je als eenmanszaak-ondernemer recht hebt op een aantal fiscale voordelen die een bv niet heeft:
- **Zelfstandigenaftrek** — een vast bedrag dat van je winst wordt afgetrokken, mits je voldoet aan het urencriterium (minimaal 1.225 uur per jaar aan je onderneming besteed). Let op: dit bedrag daalt jaarlijks — voor 2026 is het nog €1.200, tegen €2.470 in 2025.
- **MKB-winstvrijstelling** — een percentage van je resterende winst dat onbelast blijft.
- **Startersaftrek** — een extra aftrek in je eerste jaren als ondernemer, als je aan de voorwaarden voldoet.

Een eigen vermogen opbouwen in je eenmanszaak heeft overigens geen directe invloed op hoeveel belasting je betaalt — dat is gekoppeld aan je winst, niet aan wat er op de "balans" van je onderneming staat. Geld dat je uit de zaak haalt voor privégebruik verandert niets aan de belasting die je al verschuldigd bent over de winst van dat jaar.

### Hoeveel administratie heb je nu eigenlijk echt?

In de praktijk komt het bij een eenmanszaak neer op drie dingen die je structureel moet bijhouden:

1. **Facturen versturen en bewaren** — uitgaand én inkomend (inkoopfacturen voor je eigen kosten).
2. **Btw bijhouden en periodiek afdragen** — de btw die je int is niet van jou, die moet je apart zien van je eigen omzet.
3. **Een overzicht van je winst**, zodat je aan het einde van het jaar weet wat je aan inkomstenbelasting kunt verwachten — en niet voor een onverwachte naheffing komt te staan.

Dat laatste punt is waar veel startende zzp'ers tegen een muur lopen: ze zien pas bij de jaarlijkse IB-aangifte hoeveel belasting ze moeten betalen, terwijl het geld al lang is uitgegeven. Een reservering opzij zetten zodra je een factuur betaald krijgt — in plaats van achteraf schrikken — is verreweg het beste gewoonte die je als startende eenmanszaak-ondernemer kunt aanleren.

### Hoe BigDogg hierbij helpt

BigDogg is gebouwd voor precies deze situatie: een eenmanszaak die simpele, nette administratie wil zonder een volledig boekhoudpakket te moeten leren. Facturen maken die automatisch aan de wettelijke eisen voldoen, btw die automatisch wordt berekend en los wordt gehouden van je omzet, en een overzicht dat een indicatie geeft van hoeveel je opzij zou moeten zetten voor de inkomstenbelasting (gebaseerd op de actuele zelfstandigenaftrek en belastingschijven) — zodat je nooit voor een verrassing komt te staan bij je jaarlijkse aangifte.

Je kunt BigDogg 30 dagen gratis proberen, zonder dat je een betaalmethode moet invoeren. En als je andere zzp'ers kent die ook op zoek zijn naar simpele administratie: via het referral-programma krijg je een gratis maand voor elke 2 vrienden die zich aanmelden, tot maximaal 3 gratis maanden.

---

*Dit artikel is geschreven voor zzp'ers die willen weten waar ze precies aan toe zijn — niet als vervanging van fiscaal advies. Twijfel je over je specifieke situatie? Een boekhouder of de Belastingdienst zelf kan je altijd verder helpen met de details die voor jou van toepassing zijn.*
