# Forum reply drafts — week of 2026-09-07 (Higherlevel.nl)

> **Note on sourcing:** this sandbox's network egress proxy blocked direct page fetches to higherlevel.nl this run (WebSearch snippets worked, WebFetch did not). The summaries below are reconstructed from search-result snippets, not a full read of every reply already in the thread. **Before posting, open each thread yourself and re-check that no one has already given this exact answer, and that nothing below is stale.**

---

## 1. Balans: te vorderen / te betalen BTW (bol.com afrekening over de jaargrens)

**Thread:** https://www.higherlevel.nl/forums/topic/78290-balans-te-vorderente-betalen-btw/
**Board:** Financiering
**Context (from thread):** een bol.com-verkoper krijgt een afrekening met factuurdatum 2 januari 2026, die betrekking heeft op verkopen en kosten tussen 8 en 31 december 2025. Vraag: in welk tijdvak/boekjaar hoort de bijbehorende BTW op de balans (te vorderen vs. te betalen)?

**Draft reply (NL):**

> Herkenbaar probleem, en het antwoord is een beetje contra-intuïtief: voor de BTW-aangifte is niet de periode waar de omzet betrekking op heeft leidend, maar de **factuurdatum** (het zogeheten factuurstelsel). Bol.com dateert de verzamelfactuur/afrekening op 2 januari 2026, dus die BTW hoort in beginsel gewoon in Q1 2026, ook al gaat het over verkopen van eind december 2025.
>
> Voor de **winstbepaling (IB)** ligt dat anders: die omzet en kosten reken je op basis van goed koopmansgebruik toe aan 2025, want de prestatie (verkoop/levering) vond daar plaats. Dat los je op met een overlopende post: "nog te ontvangen omzet" / "nog te betalen kosten" per 31-12-2025, die je in januari tegen de bol.com-afrekening wegboekt. Dus twee verschillende regels voor twee verschillende doeleinden — BTW volgt de factuurdatum, resultaat volgt de prestatiedatum.
>
> Dit soort jaargrens-gedoe met bol.com/marketplace-afrekeningen is precies waarom ik uiteindelijk zelf een facturatietool (BigDogg) ben gaan bouwen met een duidelijke BTW-periode-indeling per boeking — maar los van welke tool je gebruikt: leg deze twee bedragen (BTW-tijdvak vs. boekjaar-toerekening) los van elkaar vast, anders sluit je jaarafsluiting nooit lekker aan. Bij twijfel over jouw specifieke cijfers zou ik het wel even langs een boekhouder leggen, want de BTW-nuances bij marketplace-afrekeningen (bol.com rekent soms zelf al BTW-verlegd af) kunnen per situatie verschillen.

---

## 2. Vakman zzp — factuur maken met opslag op materialen

**Thread:** https://www.higherlevel.nl/forums/topic/77718-vakman-zzp-factuur-maken-met-opslag/
**Board:** Administratie en verzekeringen
**Context (from thread):** een beginnende vakman wil arbeidsuren + BTW factureren, plus materialen die hij zelf inkoopt en met een opslag (10%) doorbelast aan de klant. Een andere gebruiker reageert dat hij in de schoonmaakbranche 30-35% marge rekent op geleverde materialen.

**Draft reply (NL):**

> Wat ik zelf zou doen: zet arbeid en materiaal als **losse regels** op de factuur, niet in één bedrag verstopt. Klanten (zeker zakelijke) willen vaak kunnen zien wat arbeid kostte en wat materiaal kostte, en het scheelt gedoe bij garantie- of BTW-vragen achteraf.
>
> Voor de opslag: 10% is aan de lage kant als je bedenkt dat je ook tijd kwijt bent aan inkopen, voorschieten, transport en het risico dat je ergens aan blijft zitten (retour, beschadiging). De 30-35% die hierboven genoemd wordt is in de bouw/installatie/schoonmaak ook niet ongewoon — reken gewoon door wat jouw eigen tijd en risico waard zijn, niet alleen "wat de markt zegt". Zolang je vooraf (in de offerte) duidelijk maakt dát er een opslag op materiaal zit, mag je dat percentage zelf bepalen; er is geen wettelijk maximum voor een zzp'er die materiaal doorverkoopt.
>
> BTW-technisch: over het hele materiaalbedrag (inclusief jouw opslag) reken je gewoon 21% BTW, alsof jij het materiaal aan de klant verkoopt — wat feitelijk ook zo is. Zorg dat je facturatietool losse regels met eigen omschrijving en aparte BTW-berekening per regel ondersteunt (dat is bij BigDogg, wat ik zelf bouw, standaard, maar geldt voor de meeste facturatietools) — dan hoef je dit niet handmatig na te rekenen en klopt de optelsom altijd.

---

## 3. Factuur inboeken over de jaargrens (2 januari, werk verricht in december)

**Thread:** https://www.higherlevel.nl/forums/topic/76044-factuur-inboeken-overlapping-boekjaar/
**Board:** Administratie en verzekeringen
**Context (from thread):** een factuur met factuurdatum 2 januari (nog met een factuurnummer uit de 2023-reeks) betreft werk dat eind december is verricht. Vraag: mag/moet die factuur onder het oude boekjaar geboekt worden voor de BTW-aangifte?

**Draft reply (NL):**

> Dit is precies dezelfde denkfout die vaker voorkomt (zie ook de bol.com-vraag verderop in dit forum): voor de **BTW-aangifte** is de factuurdatum leidend, niet wanneer het werk is uitgevoerd. Een factuur gedateerd 2 januari hoort dus gewoon in het BTW-tijdvak van het nieuwe jaar (Q1), ook al staat er nog een factuurnummer uit de oude reeks op en is het werk in december gedaan. Overigens: probeer die factuurnummer-reeks wel gewoon doorlopend te houden per boekjaar (of in ieder geval logisch/uniek) — de Belastingdienst let daarop bij een controle.
>
> Voor de **winstaangifte (IB)** ligt het anders: de omzet uit werk dat in december is verricht, hoort volgens goed koopmansgebruik in het oude boekjaar te vallen, ook al is de factuur pas in januari verstuurd. Dat corrigeer je met een overlopende post "onderhanden werk" of "nog te factureren omzet" per 31 december. Dus: BTW in het nieuwe jaar aangeven, resultaat in het oude jaar verantwoorden — vervelend dat het twee verschillende antwoorden zijn, maar dat is wel hoe de regels in elkaar zitten. Twijfel je over de exacte boeking, laat een boekhouder er even naar kijken, want bij grotere bedragen of BTW-verleggingsregelingen kan het net iets anders liggen.
