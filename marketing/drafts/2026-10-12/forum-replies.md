# Forumreacties — week van 2026-10-12

> **Let op voor Floris:** de sandbox waarin dit is opgesteld heeft geen
> werkende browser/WebFetch (DNS/netwerktoegang naar higherlevel.nl was
> geblokkeerd). De threads hieronder zijn gevonden en samengevat via
> websearch-snippets, niet door de volledige draad te lezen. **Open elke
> link zelf voordat je plaatst** om te checken of de vraag inmiddels al
> beantwoord is, of de toon nog klopt, en of er geen context ontbreekt die
> niet in de snippet stond.

---

## 1. Balans: Te vorderen/te betalen BTW

**Bron:** https://www.higherlevel.nl/forums/topic/78290-balans-te-vorderente-betalen-btw/
**Board:** Financiering

**Context (uit snippet):** vraag over hoe je te vorderen en te betalen BTW
correct op de balans verwerkt, rond de jaarovergang/kwartaalaansluiting.

**Draft reactie:**

> Herkenbaar, dit loopt bij veel starters door elkaar. Even de basis:
>
> - **Te vorderen BTW** = de voorbelasting die je zelf betaald hebt aan
>   leveranciers/inkopen. Dit boek je als vlottend actief (vordering op de
>   Belastingdienst).
> - **Te betalen BTW** = de BTW die je in rekening hebt gebracht aan je
>   klanten. Dit boek je als kortlopende schuld.
>
> Per kwartaal (of jaar, bij de KOR) bereken je het saldo: betaal je méér
> dan je terugkrijgt, dan betaal je het verschil; is het andersom, dan
> krijg je geld terug. Op de balans zet je die twee meestal als losse
> grootboekrekeningen (bijv. "BTW te vorderen" en "BTW te betalen/af te
> dragen"), en zodra je de aangifte hebt ingediend én betaald, boek je ze
> tegen elkaar weg zodat ze weer op nul staan voor de nieuwe periode.
>
> Veel voorkomende valkuil: mensen vergeten de correctie te boeken als de
> werkelijke aangifte iets afwijkt van wat er in het boekhoudsysteem stond
> (bijv. door privégebruik-correcties of een afrondingsverschil). Zet die
> correctie altijd los, dan blijft je balans kloppend en kun je het
> makkelijk terugvinden bij de jaarafsluiting.
>
> Ik heb dit zelf lang handmatig bijgehouden in een spreadsheet voordat ik
> met BigDogg begon (de facturatie/boekhoudtool die ik nu bouw) — werkt
> prima zolang je die twee rekeningen maar netjes gescheiden houdt en elk
> kwartaal check of het saldo aansluit op wat je daadwerkelijk aangeeft.

---

## 2. Controle Ritregistratie

**Bron:** https://www.higherlevel.nl/forums/topic/77030-controle-ritregistratie/
**Board:** Fiscale zaken

**Context (uit snippet):** vraag over wat de Belastingdienst precies
controleert bij een controle van de ritregistratie/kilometerregistratie.

**Draft reactie:**

> Bij een controle kijkt de Belastingdienst vooral naar **aannemelijkheid**,
> niet naar een waterdicht sluitend logboek (dat is wettelijk niet voor
> iedereen verplicht, afhankelijk van je situatie — check dat specifiek
> voor jouw geval). Waar ze wel op letten:
>
> - Datum, vertrek- en aankomstadres, kilometerstand begin en eind van de
>   rit, en het doel (zakelijk of privé) — per rit, niet achteraf in één
>   keer ingevuld.
> - Consistentie: sluit je kilometerstand aan bij onderhoudsbonnen, APK of
>   tankbonnen? Als je logboek zegt dat je 8.000 km zakelijk hebt gereden
>   maar de garage noteert een heel andere kilometerstand, krijg je
>   vragen.
> - Onderbouwing met je agenda: afspraken/opdrachten die matchen met de
>   gereden ritten zijn sterk bewijs.
> - Consequente scheiding privé/zakelijk — met name het woon-werkverkeer
>   is een punt waar mensen het vaak mis hebben (voor de IB telt dat als
>   zakelijk, voor de BTW juist als privé).
>
> Praktisch: gebruik een rittenregistratie-app die automatisch via GPS
> logt, dan vergeet je nooit een rit en heb je sowieso een tijdstempel en
> locatie als bewijs. Ik hou dat zelf los van mijn facturatie/boekhouden
> (daarvoor bouw ik BigDogg) — voor kilometers gebruik ik een losse
> rittenregistratie-app. Sommige boekhoudpakketten hebben een
> kilometer-module erin; even checken of die exporteert in een vorm die je
> ook echt bij een controle kunt tonen.

---

## 3. Vakman zzp, factuur maken met opslag

**Bron:** https://www.higherlevel.nl/forums/topic/77718-vakman-zzp-factuur-maken-met-opslag/
**Board:** Administratie en verzekeringen

**Context (uit snippet):** beginnende vakman-zzp'er vraagt hoe hij op de
factuur zijn uren én ingekochte materialen met een opslagpercentage
(marge) moet verwerken.

**Draft reactie:**

> Je hoeft op de factuur helemaal niet te laten zien wát je inkoopprijs was
> en hoeveel opslag je rekent — de klant heeft recht op jouw
> verkoopprijs, niet op inzage in je marge. Twee manieren die in de
> praktijk allebei vaak gebruikt worden:
>
> 1. **Eén regel "materialen"** met je eigen (verkoop)prijs erin verwerkt.
>    Simpelst, en voor de meeste particuliere/kleine klanten de normale
>    gang van zaken.
> 2. **Materialen + aparte regel "coördinatie/opslag materialen"**, vooral
>    handig bij grotere klussen of zakelijke klanten die prijsopbouw
>    willen zien. Ook dan zet je gewoon een bedrag neer, geen percentage
>    dat teruggerekend kan worden naar je inkoopprijs.
>
> Beide regels vallen onder hetzelfde BTW-tarief als je dienst (meestal
> 21%, let op verlegde BTW als je voor een aannemer/hoofdaannemer werkt).
>
> Qua hoogte van de opslag: 10% is in de praktijk vaak te laag om
> prijsstijgingen, retouren/kapot materiaal en de extra administratietijd
> te dekken — 15–20% is gangbaarder, afhankelijk van je vak en hoe vaak je
> materialen voorschiet.
>
> Dit soort factuuropbouw-vragen was precies waarom ik zelf met BigDogg
> begonnen ben (een facturatietool die ik aan het bouwen ben) — maar het
> werkt ook met gewoon een duidelijke regel in elk ander factuurprogramma
> of zelfs Word, zolang de omschrijving maar klopt met wat je levert.
