# Forum replies — Higherlevel.nl (week of 2026-09-28)

> **⚠️ Research limitation, read before posting:** the sandbox this run executed
> in has an organization-level network policy that blocks outbound access to
> `higherlevel.nl` (confirmed: direct `curl` gets `403 CONNECT tunnel failed`
> from the egress proxy, and `WebFetch` returns `EGRESS_BLOCKED`). Web search
> still works and surfaced real thread titles/URLs and short snippets, but the
> full thread text, current reply count, and whether other people already
> dropped software recommendations could **not** be verified this run.
>
> **Before posting any of these:** open each thread yourself, confirm it's
> still open/relevant, check nobody already gave the same answer, and adjust
> tone/details to match what's actually been said. Treat the drafts below as
> a strong starting point based on the thread's subject, not a verified
> reply-in-context.

---

## 1. Factuur sturen zonder ingeschreven ondernemer

**Thread:** [Factuur sturen, echter geen ondernemer (geen inschrijfverplichting Handelsregister)](https://www.higherlevel.nl/forums/topic/78124-factuur-sturen-echter-geen-ondernemer-geen-inschrijfverplichting-handelsregister/) — Administratie en verzekeringen

**Context (from title/snippet):** iemand wil een factuur sturen maar is (nog) niet verplicht ingeschreven bij het Handelsregister — een klassieke vraag van net-startende zzp'ers/bijverdieners.

**Draft reply:**

> Herkenbaar, dit is precies waar ik zelf tegenaan liep toen ik begon. Een paar dingen die voor mij hielpen scheiden:
>
> - Voor de **Belastingdienst** (BTW/inkomstenbelasting) hoef je niet per se in het Handelsregister te staan om als ondernemer voor de omzetbelasting te gelden — dat is een aparte toets (zelfstandigheid, duurzaamheid, omvang van de werkzaamheden, etc.). Check dat met de vragenlijst "Ondernemersvragen omzetbelasting" op de site van de Belastingdienst, of bel de BelastingTelefoon, want dit bepaalt of je BTW moet berekenen op je factuur.
> - Als je (nog) geen KvK-nummer hebt, mag je factuur toch gewoon geldig zijn zolang de verplichte gegevens erop staan: naam + adres van jou en de klant, datum, factuurnummer (oplopend/uniek), omschrijving, bedrag ex/incl. BTW, en BTW-nummer als je die hebt.
> - Zodra het structureel wordt (meerdere klanten, met regelmaat), is inschrijven bij de KvK meestal geen vraag meer maar een noodzaak — ook voor aansprakelijkheid en om btw-nummer/OB-nummer te krijgen.
>
> Ik heb zelf BigDogg gebouwd (een simpel facturatieprogramma voor zzp'ers) juist omdat ik in het begin worstelde met dit soort randzaken naast het "gewoon een nette factuur maken" — dus geen keiharde promotie, maar mocht je zoeken naar een manier om dit soort dingen op orde te houden zodra je wél start, denk erover na wat voor jou werkt (Excel is ook prima in het begin).

---

## 2. Hoe lang duurt verwerking van je eerste BTW-aangifte

**Thread:** [Eerste keer omzetbelasting aangifte gedaan, hoe lang duurt de verwerking?](https://www.higherlevel.nl/forums/topic/73546-eerste-keer-omzetbelasting-aangifte-gedaan-hoe-lang-duurt-de-verwerking/) — Fiscale zaken

**Context (from title/snippet):** iemand heeft net zijn/haar eerste omzetbelastingaangifte gedaan en vraagt zich af hoelang de verwerking duurt.

**Draft reply:**

> Bij mijn eerste aangifte duurde het destijds een paar weken voordat er iets zichtbaar veranderde in Mijn Belastingdienst Zakelijk — dat is normaal, zeker bij de allereerste keer omdat je dossier nog "aangemaakt" moet worden. Een paar dingen die rust gaven:
>
> - Zolang je de **ontvangstbevestiging** hebt (na het verzenden via het portaal), is je aangifte binnen. Verwerking en eventuele teruggave/naheffing volgen apart.
> - Bij een *teruggave* (vaker bij startende zzp'ers met veel opstartkosten) duurt uitbetaling doorgaans een paar weken tot ~3 maanden; bij een *te betalen* bedrag krijg je gewoon een naheffing/acceptgiro met betaaltermijn, geen reden tot paniek als dat nog niet meteen zichtbaar is.
> - Bewaar sowieso de ontvangstbevestiging en je eigen berekening (omzet, voorbelasting, saldo) los van de aangifte zelf — scheelt een hoop als de Belastingdienst achteraf vraagt hoe je op een bedrag kwam.
>
> Ik loop zelf ook nog steeds even te twijfelen elk kwartaal of het wel goed is doorgekomen 😅 — heb daarom voor mezelf (en inmiddels ook in BigDogg, de tool die ik bouw) een simpel kwartaaloverzicht gemaakt zodat ik het bedrag dat ik ga aangeven al zwart-op-wit heb vóórdat ik het portaal open. Los van welke tool je gebruikt: reken het altijd even na met je eigen omzet/kosten-overzicht, dat portaal toont soms pas later het definitieve bedrag.

---

## 3. Roulerend factureren tussen zzp'ers

**Thread:** [3 ZZP'ers rouleren als opdrachtgever](https://www.higherlevel.nl/forums/topic/76432-3-zzpers-rouleren-als-opdrachtgever/) — Fiscale zaken

**Context (from title/snippet):** drie zzp'ers werken samen en rouleren wie er als "opdrachtgever" naar de eindklant factureert.

**Draft reply:**

> Dit soort constructies kunnen prima werken, maar let op een paar addertjes onder het gras die ik zelf (of via andere zzp'ers) ben tegengekomen:
>
> - De Belastingdienst kijkt naar de **feitelijke situatie**, niet naar wie er toevallig factureert. Als er structureel maar één opdrachtgever/eindklant is en jullie zijn feitelijk gewoon met z'n drieën voor diezelfde klant aan het werk, kan dat vragen oproepen richting schijnzelfstandigheid — ook als de facturatie netjes rouleert.
> - Zorg dat **iedereen apart** factureert voor zijn eigen deel van het werk (eigen uren/prijs/product), ook al gaat het geld via één factuur naar de eindklant. Onderling verrekenen jullie dan met elkaar via aparte facturen (jij factureert aan degene die naar de eindklant factureert, voor jouw deel).
> - Leg de afspraak sowieso schriftelijk vast (wie factureert wanneer, hoe wordt verrekend, wat als iemand uitvalt) — niet voor de Belastingdienst per se, maar omdat dit soort constructies bij onenigheid snel vervelend wordt.
>
> Ik zou het in ieder geval niet zien als "BTW-technisch een trucje" maar gewoon als drie losse ondernemers die onderling factureren — praktisch gezien is dat ook makkelijker te administreren (en eerlijk gezegd precies het soort puzzel die me deed besluiten om BigDogg te bouwen, simpel factureren tussen zzp'ers onderling is verrassend omslachtig in de meeste tools). Loop het voor de zekerheid wel even langs bij een boekhouder/adviseur die de exacte situatie kent, want de details (hoeveelheid opdrachtgevers, duur van de samenwerking) maken hier echt verschil.
