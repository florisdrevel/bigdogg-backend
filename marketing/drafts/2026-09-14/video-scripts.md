# Video script drafts — week of 2026-09-14

3 short (30-45s) Dutch TikTok/Reels scripts. Each stands on its own as a useful tip — no
hard pitch — with BigDogg shown naturally in the last few seconds. All three topics are new
this week (checked against `STATE.md` history from all seven prior runs).

---

## Script 1: Hoeveel belasting moet je opzij zetten als zzp'er?

**Hook (0-3s):** *(tekst op scherm: "Hoeveel belasting zet JIJ opzij?")*
"De meeste startende zzp'ers zetten of veel te weinig, of veel te veel opzij voor de
belasting. Beide zijn vervelend."

**Body (3-30s):**
"Een simpele vuistregel: reserveer ergens tussen de 25 en 35% van je winst, afhankelijk van
hoeveel je verdient en of je de zelfstandigenaftrek en MKB-winstvrijstelling kunt toepassen.
Bij een laag jaarwinst — pak 'm beet rond de €3.500 — kan het door de heffingskortingen zelfs
uitkomen op bijna €0 aan te betalen belasting. Bij een hogere winst loop je sneller richting
de 30-35%, omdat je dan in een hogere belastingschijf terechtkomt.
Belangrijk: als je náást je zzp-werk ook nog in loondienst werkt, heb je je
heffingskortingen vaak al gebruikt via je salaris — dan moet je dus wél als een hoger
percentage reserveren."

**CTA/BigDogg-moment (30-40s):**
*(scherm: overzichtspagina met belastingreservering)*
"Ik laat dit gewoon automatisch berekenen op basis van mijn facturen en uitgaven in
BigDogg — scheelt me elk kwartaal een rekensommetje, en ik weet meteen of ik op schema lig."

**On-screen caption suggestie:** "Dit is een richtlijn, geen belastingaangifte — check je
eigen situatie."

---

## Script 2: BTW verleggen als zzp'er — wanneer moet dat?

**Hook (0-3s):** *(tekst: "Waarom staat er geen BTW op deze factuur?")*
"Als je weleens een factuur krijgt of stuurt zonder BTW-bedrag, maar wel met 'BTW verlegd'
erop — dit is waarom."

**Body (3-32s):**
"BTW verleggen betekent dat niet jij, maar je klant de BTW aangeeft en betaalt aan de
Belastingdienst. Dat gebeurt in een paar situaties: als je zakendoet met een
btw-plichtig bedrijf in een ander EU-land, bij bepaalde onderaannemersconstructies in de
bouw, of in een paar specifieke sectoren waar de wet dat voorschrijft.
Op je factuur zet je dan geen BTW-bedrag, maar wél de tekst 'BTW verlegd' plus het
BTW-nummer van je klant. Vergeet je dat, dan kan de Belastingdienst er alsnog van uitgaan
dat jij die BTW verschuldigd bent — dus check dit per klant en per situatie, niet standaard."

**CTA/BigDogg-moment (32-42s):**
*(scherm: factuur met verlegde BTW in BigDogg)*
"In BigDogg zet ik dit gewoon aan per factuur, en de BTW-verlegd-tekst en het klant-BTW-
nummer komen er automatisch op te staan."

**On-screen caption suggestie:** "Twijfel je of het op jou van toepassing is? Check
belastingdienst.nl of vraag het je boekhouder."

---

## Script 3: Thuiswerkaftrek — mag je dat als zzp'er?

**Hook (0-3s):** *(tekst: "Werk je thuis? Dit mag je (waarschijnlijk niet) aftrekken")*
"Veel zzp'ers denken dat ze zomaar een deel van de huur of hypotheek kunnen aftrekken omdat
ze thuis werken. Meestal klopt dat niet."

**Body (3-30s):**
"De regel: als je thuiswerkruimte geen eigen ingang heeft en niet duidelijk gescheiden is
van de rest van je woning — denk aan een hoekje van de woonkamer of een slaapkamer die ook
als kantoor dient — dan mag je die ruimte fiscaal niet als 'zelfstandige werkruimte'
aanmerken. Geen aparte ingang? Dan geen aftrek van een deel van je woonlasten.
Wat je wél gewoon mag aftrekken: een bureau, een monitor, kantoorbenodigdheden, een
(zakelijk deel van je) internetabonnement, en een deel van je energiekosten als je kunt
onderbouwen hoeveel daarvan zakelijk is. Dat is vaak meer dan mensen denken — ze focussen
op de huur/hypotheek en vergeten de kleinere, wél aftrekbare kosten."

**CTA/BigDogg-moment (30-40s):**
*(scherm: uitgave toevoegen/categoriseren in BigDogg)*
"Ik zet dat soort kosten gewoon meteen in de juiste categorie in BigDogg zodra ik ze maak,
dan hoef ik aan het einde van het kwartaal niet te puzzelen wat ik nou precies kan
aftrekken."

**On-screen caption suggestie:** "Twijfelgeval? Check de regels voor 'werkruimte in de
eigen woning' op belastingdienst.nl."

---

**Note on accuracy:** the 25-35% tax-reserve range in script 1 is grounded in the actual
reserve-calculation logic in `app/constants/tax_rates.py` on the `master` branch (which
models zelfstandigenaftrek + MKB-winstvrijstelling + box-1 brackets + heffingskortingen),
not guessed — but as with the blog post, verify the specific behavior described (e.g. the
near-€0 reserve at low profit) is what's actually live before filming, since `master` is
ahead of `main`.
