# Forum reply drafts — higherlevel.nl — week van 2026-08-10

**Belangrijke noot voor Floris:** de sandbox waarin dit is opgesteld kon higherlevel.nl niet direct openen (egress naar dat domein is geblokkeerd in deze omgeving) — de threads zijn gevonden en samengevat via zoekresultaten, niet door de pagina's zelf te lezen. Lees elke thread dus zelf helemaal door voordat je reageert, zodat de reply exact aansluit op wat er al gezegd is en je niemand herhaalt. Pas toon/details aan waar nodig.

---

## 1. Vakman zzp, factuur maken met opslag op materiaal

**Bron:** https://www.higherlevel.nl/forums/topic/77718-vakman-zzp-factuur-maken-met-opslag/
**Board:** Administratie en verzekeringen
**Context (uit zoekresultaten):** een beginnende zzp-vakman vraagt hoe hij een factuur opbouwt wanneer hij zowel uren als ingekocht materiaal doorberekent, met een opslag (marge) op dat materiaal.

**Concept-reactie:**

> Herkenbaar, dit is een van de eerste dingen waar je tegenaan loopt als je begint. Een paar dingen die voor mij hielpen toen ik hiermee worstelde:
>
> - Zet uren en materiaal als **aparte regels** op de factuur, niet bij elkaar opgeteld. Dus: "Arbeid, X uur à €Y" op de ene regel, "Materiaal (inkoop + opslag)" op de andere. Dat is voor je klant transparanter en scheelt discussie achteraf, zeker bij particulieren die vaak willen zien wat de inkoopprijs was.
> - De opslag zelf mag je vrij bepalen (er is geen wettelijk maximum), maar reken hem gewoon mee in het regelbedrag — je hoeft de opslag niet apart te specificeren als percentage, tenzij je klant daarom vraagt.
> - Let op: over het **totale factuurbedrag** (arbeid + materiaal + opslag) reken je gewoon BTW, ook al heb je op de inkoop van het materiaal zelf al BTW betaald. Die inkoop-BTW trek je apart terug via je aangifte, dat heeft niets te maken met wat je aan je klant factureert.
> - Bewaar de inkoopbonnen van het materiaal gewoon bij de factuur in je administratie, ook al hoeft dat niet apart op de factuur te staan — scheelt gedoe bij een controle.
>
> Ik heb zelf BigDogg gebouwd juist omdat ik tegen dit soort factuuropbouw-gedoe aanliep als zzp'er — daar kun je materiaal- en urenregels los invoeren en de BTW/opslag rekent-ie automatisch door. Zeg ik er niet bij om het te pitchen, maar puur omdat het exact dit probleem oplost. Succes in ieder geval met de eerste facturen!

---

## 2. Factuur sturen, maar (nog) geen ingeschreven onderneming

**Bron:** https://www.higherlevel.nl/forums/topic/78124-factuur-sturen-echter-geen-ondernemer-geen-inschrijfverplichting-handelsregister/
**Board:** Administratie en verzekeringen
**Context (uit zoekresultaten):** iemand wil een factuur sturen voor werk/diensten, maar is (nog) niet ingeschreven bij het Handelsregister/KvK en vraagt of dat mag en hoe dat dan administratief moet.

**Concept-reactie:**

> Even kort de kern, los van jouw specifieke situatie (die ken ik niet helemaal, dus lees ook de reacties van anderen hierboven goed):
>
> - Voor een KvK-inschrijving geldt een ondergrens qua duurzaamheid/omvang van de activiteit — niet iedereen die één keer iets factureert, is verplicht zich in te schrijven. Maar zodra het structureel wordt (meerdere klanten, herhaling, winstoogmerk), ben je al snel wél ondernemer voor de wet, ook zonder KvK-nummer, en moet je je alsnog inschrijven — vaak met terugwerkende kracht.
> - Facturen die je stuurt zonder KvK-nummer/btw-id zijn voor de Belastingdienst niet automatisch "geldig" als zakelijke factuur — dat kan later gedoe geven bij de aftrek van BTW door je opdrachtgever, en bij je eigen aangifte als blijkt dat je toch ondernemer was.
> - Twijfel je of je onder de "hobbymatig" grens blijft of eigenlijk al ondernemer bent? Bel gewoon even gratis met de Belastingdienst of KvK, die stellen een paar vragen en zeggen je vrij snel waar je staat. Beter nu bellen dan achteraf een correctie.
>
> Ik loop zelf tegen dit soort grensgevallen aan met gebruikers van BigDogg (het factuurprogramma dat ik gebouwd heb) — vaak starten mensen met facturen sturen voordat ze goed snappen of/wanneer ze zich moeten inschrijven. Zeg dit niet om iets te verkopen, maar het is precies waarom ik het nu standaard vraag aan nieuwe gebruikers: sta je al ingeschreven, en zo niet, weet je zeker dat dat nog niet hoeft?

---

## 3. Balans: te vorderen / te betalen BTW

**Bron:** https://www.higherlevel.nl/forums/topic/78290-balans-te-vorderente-betalen-btw/
**Board:** Financiering
**Context (uit zoekresultaten):** vraag over hoe een BTW-post op de balans verwerkt moet worden, met een voorbeeld van een bol.com-factuur gedateerd 2 januari 2026 die betrekking heeft op een bestelling/transactie uit december 2025 — dus een kwartaal-grensgeval.

**Concept-reactie:**

> Dit soort jaarwisseling-facturen zijn altijd verwarrend, dus goede vraag. Een paar vuistregels die ik zelf aanhoud:
>
> - Voor de BTW-aangifte is niet de betaaldatum leidend, maar de **factuurdatum** (of, bij ontvangen facturen, het moment waarop je de prestatie/levering hebt ontvangen — meestal valt dat samen met de factuurdatum). Een factuur gedateerd 2 januari 2026 hoort dus in principe in Q1 2026, ook al ging de bestelling nog over december.
> - Op de balans zet je "te vorderen BTW" (voorbelasting die je nog terugkrijgt) en "te betalen BTW" (BTW die je nog moet afdragen) als aparte posten onder kortlopende vorderingen/schulden, tot het moment dat de aangifte daadwerkelijk is ingediend en verrekend — dan boek je ze weg tegen de bank.
> - Bij twijfel over een randgeval zoals dit: consistent zijn is belangrijker dan "perfect" zijn. Kies een regel (bijv. altijd factuurdatum aanhouden) en pas die het hele jaar toe, dat voorkomt gedoe bij een controle achteraf.
>
> Ik zie deze jaarwisseling-vraag wel vaker langskomen bij BigDogg-gebruikers (het boekhoud-/factuurprogramma dat ik zelf heb gebouwd) rond deze tijd van het jaar — vandaar dat ik dit vrij scherp op het netvlies had. Geen quickfix, maar hopelijk helpt het net iets in de goede richting.

