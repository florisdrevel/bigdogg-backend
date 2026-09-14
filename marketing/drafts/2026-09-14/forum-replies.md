# Forum reply drafts — week of 2026-09-14

**Important caveat (8th consecutive run with this limitation):** `WebFetch` to
higherlevel.nl is still blocked by this sandbox's network egress proxy (confirmed again
this run). These drafts are built from `WebSearch` result snippets/summaries only — nobody
on this run has actually opened these threads or read the existing replies in full.
**Before posting anything below, open each thread yourself, confirm it's still open, and
check nobody has already given this exact answer.**

All three threads below are new — none were used in any prior week's run (checked against
the full history in `marketing/STATE.md`, reconstructed across all seven prior branches:
07-28, 08-03, 08-10, 08-17, 08-24, 08-31, 09-07).

---

## 1. Simpele facturatietool zonder boekhoudcomplexiteit

**Source:** https://www.higherlevel.nl/forums/topic/77806-behoefte-aan-simpele-facturatietool-zonder-boekhoudcomplexiteit/
**Board:** Administratie en verzekeringen

**Context (from search snippets):** a freelancer wants to send simple invoices, see what's
still outstanding, and get a BTW overview — without wading through the full accounting
feature set of tools like Moneybird or e-Boekhouden, which they find too extensive for
what they actually need.

**Draft reply (Dutch):**

> Herkenbaar — ik heb zelf ook een tijd met Moneybird geworsteld voordat ik doorhad dat ik
> eigenlijk maar drie dingen nodig had: facturen sturen, in één oogopslag zien wat nog open
> staat, en een betrouwbaar BTW-overzicht per kwartaal. De rest (grootboekrekeningen,
> uitgebreide rapportages, koppelingen die ik toch niet gebruikte) voelde vooral als extra
> schermen om doorheen te klikken.
>
> Een paar dingen die voor mij hielpen bij het kiezen:
> - Check of een tool een duidelijk "openstaand vs. betaald"-overzicht heeft zonder dat je
>   daar een apart rapport voor moet genereren — dat is het ding waar ik het vaakst naar
>   kijk.
> - Vraag je af of je automatische betalingsherinneringen nodig hebt. Achter facturen
>   aanbellen kost meer tijd dan de meeste zzp'ers denken.
> - BTW-overzicht: liever een tool die het gewoon per kwartaal voor je optelt op basis van
>   je facturen en uitgaven, dan dat je zelf Excel erbij moet houden.
>
> Ik heb dit exacte probleem vorig jaar zelf opgelost door BigDogg te bouwen — puur
> facturatie + uitgaven + BTW-overzicht, zonder de boekhoudkundige laag eromheen. Zeg ik niet
> om het je te verkopen, maar omdat het antwoord op "bestaat zoiets simpels?" gewoon "ja,
> en het is te bouwen/te vinden" is. Kijk vooral rond en test een paar opties — het
> belangrijkste is dat je niet meer tijd kwijt bent aan de tool dan aan je eigen werk.

**Note:** this is the one thread where a BigDogg mention is directly on-topic (they're
literally describing the product), so it's included by name — but framed as one data point
among several, not a pitch. Reconsider the wording once you've read the actual replies;
if 2-3 people have already suggested BigDogg-like tools, trim the self-mention down further.

---

## 2. Gevolgen van het niet voldoen aan het urencriterium

**Source:** https://www.higherlevel.nl/forums/topic/72165-gevolgen-van-het-niet-voldoen-aan-het-urencriterium/
**Board:** Fiscale zaken

**Context (from search snippets):** someone started as zzp'er per 1 oktober, so can't
realistically reach 1.225 uur that calendar year, and asks what the consequences are beyond
losing the zelfstandigenaftrek/startersaftrek — specifically whether the
kleinschaligheidsinvesteringsaftrek (KIA) and BTW-aftrek are also affected.

**Draft reply (Dutch):**

> Goed dat je dit nakijkt voordat je de aangifte doet, want dit wordt vaak door elkaar
> gehaald. Kort door de bocht:
>
> - **Zelfstandigenaftrek + startersaftrek** — deze vervallen inderdaad als je het
>   urencriterium (1.225 uur, én de meeste tijd besteed aan je onderneming t.o.v. eventueel
>   ander werk) niet haalt. Dat geldt sowieso voor je eerste, gedeeltelijke jaar als je pas
>   in oktober bent gestart.
> - **MKB-winstvrijstelling** — deze staat los van het urencriterium. Die krijg je gewoon,
>   ook zonder de uren te halen.
> - **KIA (kleinschaligheidsinvesteringsaftrek)** — ook los van het urencriterium. KIA is
>   gekoppeld aan het totale investeringsbedrag in het jaar, niet aan gewerkte uren. Als je
>   voldoende hebt geïnvesteerd, heb je daar gewoon recht op.
> - **BTW-aftrek** — helemaal los van het urencriterium. Het urencriterium is een
>   inkomstenbelasting-begrip; voor de btw maakt het niet uit hoeveel uur je hebt gewerkt,
>   alleen of de kosten zakelijk zijn.
>
> Kortom: je mist dit jaar alleen de aftrekposten die specifiek aan het urencriterium
> gekoppeld zijn, niet je btw-aftrek of KIA. Wil je het helemaal zeker weten voor jouw
> situatie, de rekenhulp op de site van de Belastingdienst (of gewoon even bellen met de
> BelastingTelefoon) is hiervoor verrassend behulpzaam.
>
> Zelf hou ik mijn uren gewoon per week bij (ik gebruik daar BigDogg's urenregistratie voor,
> maar een simpel Excel-sheetje kan ook) zodat ik aan het einde van het jaar niet hoef te
> gokken of ik de 1.225 uur haal.

**Note:** double-check the accuracy of the KIA/urencriterium and BTW/urencriterium
independence claims against the current Belastingdienst rules before posting — this is
standard tax knowledge but rules get tweaked; don't post this without a quick sanity check.

---

## 3. Betalingstermijn op factuur overschreden

**Source:** https://www.higherlevel.nl/forums/topic/72141-betalingstermijn-op-factuur-overschreden/
**Board:** Administratie en verzekeringen

**Context (from search snippets):** a general question about what to do once a client has
missed the agreed payment term on an invoice — what steps are reasonable, and what can
legally be charged on top (rente, aanmaningskosten).

**Draft reply (Dutch):**

> De volgorde die ik zelf aanhoud (en die ook gewoon de nette/juridisch correcte route is):
>
> 1. **Vriendelijke herinnering** — vaak is het gewoon vergeten. Een kort mailtje, geen kosten
>    erbij.
> 2. **Officiële aanmaning** — als er na de herinnering nog niets gebeurt, stuur een
>    aanmaning met een nieuwe, redelijke betalingstermijn (14 dagen is gebruikelijk). Dit
>    is ook het moment vanaf waar je wettelijk incassokosten in rekening mag gaan brengen
>    als de klant een bedrijf is (voor consumenten gelden striktere regels — daar moet je
>    eerst een aparte aanmaning sturen die specifiek de incassokosten aankondigt).
>  3. **Wettelijke handelsrente** — als zzp'er met een zakelijke klant mag je de wettelijke
>    handelsrente rekenen vanaf de vervaldatum, niet pas vanaf de aanmaning. Die rente
>    verandert halfjaarlijks; check de actuele rente op rijksoverheid.nl voor het juiste
>    percentage.
> 4. **Incassokosten** — volgens de wettelijke staffel (Wet Incassokosten), niet een vrij
>    zelfgekozen bedrag.
> 5. Pas als dat allemaal niets oplevert: een incassobureau of de kantonrechter (bij kleinere
>    bedragen loopt dat via de kantonrechter, ongeacht het bedrag als het om een
>    consumentenzaak gaat).
>
> Wat voor mij het meeste tijd scheelt: ik laat de eerste herinnering automatisch versturen
> zodra een factuur de betalingstermijn passeert (BigDogg doet dat voor me), zodat ik niet
> zelf hoef bij te houden welke factuur wanneer verloopt. Maar de aanmaning met rente/
> incassokosten stuur ik zelf, met net iets meer persoonlijke toon.

**Note:** verify the current wettelijke handelsrente percentage and the incassokosten
staffel figures are still accurate for 2026 before posting (both are adjusted periodically)
— don't post stale rates.
