# Cartea de rețete

Sistem personal de rețete: fișiere text versionate cu git, o carte HTML generată, fără server și fără bază de date.
Sursa de adevăr sunt fișierele din `retete/`. `carte/index.html` e generat și read-only: nicio editare în browser.

## Fișiere

| Fișier | Rol |
|---|---|
| `retete/<slug>.md` | o rețetă = un fișier (frontmatter YAML + pași) |
| `ingrediente.csv` | valori nutriționale per 100 g crud, cu sursă obligatorie |
| `conversii.md` | lingură / linguriță / bucată → grame; se folosește la scriere |
| `build.py` | validare + calcul + generare |
| `sablon.html` | șablonul cărții (HTML + CSS + JS); `build.py` îi injectează rețetele ca JSON |
| `carte/index.html` | generat; se commit-uiește (se deschide de pe telefon, merge offline) |
| `IDEI.md` | backlog; ideile se parchează aici, nu se construiesc |

## Comenzi

```bash
python build.py --check   # validează toate rețetele și CSV-ul; raportează toate erorile odată
python build.py           # check + calcul + generează carte/index.html
```

Cerințe: Python 3 și PyYAML (`pip install pyyaml`). Nimic altceva. Pe Windows, dacă `python` deschide Microsoft Store, folosește `py build.py` (launcher-ul Python).

## Fluxul de lucru

**Rețetă nouă.** Claude propune 2–3 surse testate (sau o rețetă clasică, `sursa: claude`), eu aleg. Claude o scrie în schemă, convertește totul în grame cu `conversii.md` (cantitatea originală merge în `nota`), adaugă ingredientele lipsă în `ingrediente.csv` cu sursă, rulează `--check`, commit `reteta <slug> v1`.

**După gătit.** Din telefon: în rețetă, sub „Jurnal”, aleg gustul, efortul, dacă a fost greșeala mea, scriu observațiile și ce schimb data viitoare, apoi „scrie în jurnal”. Intrarea se adaugă în `retete/<slug>.md`, ca un commit făcut de mine prin API-ul GitHub (același token ca la poze), iar GitHub Actions rulează `build.py` și regenerează cartea în 2–3 minute. Sau îi scriu lui Claude o propoziție: „piept-pui-orez: gust 7, efort 3, prea sărat, data viitoare jumătate sare”; dacă am greșit eu, spun „greșeala mea: am ars ceapa”, și el adaugă intrarea, rulează build, commit `<slug> v1: gust 7 efort 3` și `git push`. Dacă propoziția e completă, nu pune întrebări.

**Versiune nouă.** Se aplică `urmatoarea_data` din ultima intrare, se incrementează `versiune`, se modifică ingredientele și pașii în același fișier; git păstrează istoricul. Commit `<slug> v2`.

**Idee nouă.** Se scrie în `IDEI.md`. Nu se construiește nimic până nu există 10 rețete cu cel puțin o intrare în jurnal.

## Schema rețetei

Fișierul `retete/<slug>.md` începe cu frontmatter YAML între două linii `---`, apoi pașii numerotați (`1. `, un pas pe linie) și opțional o secțiune `## Note`. Fiecare pas care are un timp are și un indiciu senzorial: „~4 min, până se rumenește pe margini”.

```markdown
---
titlu: Piept de pui cu orez
slug: piept-pui-orez
categorie: pranz-cina          # mic-dejun | pranz-cina | garnitura | desert | sos
tags: [rapid, pui]
sursa: claude                  # url | claude | propriu
portii: 4
timp_activ_min: 20
timp_total_min: 35             # sesiunea de gătit, de la început până în farfurie; fără așteptările din din_timp
din_timp: marinare 4–6 h       # opțional, text liber: ce trebuie făcut înainte de sesiunea de gătit; apare pe card
versiune: 1
status_manual:                 # gol = calculat din jurnal; altfel test | imbunatatire | carte | gunoi
greutate_gatita_g:             # opțional: greutatea mâncării gata; dacă e completată, „per 100 g” din carte e pe gătit
ingrediente:
  - id: piept_pui              # trebuie să existe în ingrediente.csv
    g: 500
  - id: ulei_masline
    g: 13
    nota: 1 lingură
    grup: Marinada             # opțional; în carte, lista de ingrediente se împarte pe grupuri
jurnal:
  - data: 2026-09-08
    versiune: 1
    gust: 7
    efort: 3
    executie: ok               # ok | greseala_mea
    observatii: prea sărat, orezul puțin crud
    urmatoarea_data: jumătate din sare, +5 min la orez
---
## Pregătire
1. Încinge uleiul în tigaie, ~1 min, până unduiește.
2. ...

## Note
Ce nu e sigur: timpi, sare, temperatura cuptorului.
```

Titlurile `## …` dintre pași grupează pașii pe etape; numerotarea continuă (se folosește numărul scris în fișier). În carte, pașii se bifează prin atingere, iar orice „8 minute” sau „30–60 de secunde” dintr-un pas pornește un cronometru cu sunet la final. Timpul total se afișează în ore și minute. Toate cantitățile în grame. Nume de fișiere și id-uri: ASCII, fără diacritice. Conținutul: română cu diacritice. `sursa` e un URL complet (cu `http://` sau `https://`), `claude` sau `propriu`.

## Poze

Poza unei rețete e fișierul `retete/poze/<slug>.jpg`; dacă există, cartea o arată pe card și în detaliu, altfel rămâne inițiala. Build-ul refuză pozele care nu corespund unei rețete.

Din telefon: în rețetă, „📷 poză” alege sau face o poză, o micșorează (~1200 px) și o trimite direct în repo, ca un commit, prin API-ul GitHub. Pentru asta (și pentru jurnal) cartea are nevoie de un token personal, pe care îl faci o singură dată, de preferat tot de pe telefon, logat în GitHub:

1. github.com → poza de profil → **Settings** → jos, **Developer settings** → **Personal access tokens** → **Fine-grained tokens** → **Generate new token**.
2. Nume oricare; **Expiration** cum vrei (la expirare faci altul); **Repository access**: *Only select repositories* → `retete`.
3. **Permissions** → *Repository permissions* → **Contents**: *Read and write* (restul rămân „No access”). Generate token, copiază-l (începe cu `github_pat_`).
4. În carte: „filtre ▾” → **token** → lipește. Cartea îl verifică pe loc (acces la repo și drept de scriere) și îl ține doar în browserul telefonului; sub buton scrie dacă e salvat. Dacă lipsește sau e refuzat, sub „📷 poză” și „scrie în jurnal” apare un mesaj roșu cu motivul. Poza apare pe loc pe telefonul tău și în 1–2 minute pe celelalte, după ce GitHub Pages publică commit-ul.

## Scale

**Gust (1–10):** 5 = mâncabil, nu repet · 7 = bun, dar aș schimba ceva · 8 = l-aș face din nou exact așa · 10 = l-aș servi la oaspeți.

**Efort (1–5):** 1 = o oală, ≤ 15 min activ · 3 = două vase, ~30 min activ · 5 = 3+ vase sau > 2 h total.

## Starea rețetei

Calculată de `build.py` din ultima intrare în jurnal:

- fără jurnal → `test`
- ultima intrare cu `executie: greseala_mea` → `imbunatatire`, indiferent de notă; intrarea nu se numără la limita de încercări
- gust ≥ 8 și efort ≤ 3 → `carte`; gust ≥ 8 și efort ≥ 4 → `carte` + tag automat `ocazie`
- gust 6–7 → `imbunatatire`; după 3 încercări cu `executie: ok` fără gust ≥ 8 → `gunoi`
- gust ≤ 5 (cu `executie: ok`) → `gunoi`
- `status_manual` completat suprascrie orice

Cartea arată implicit doar `carte`; `imbunatatire` și `test` se pot afișa cu un comutator; `gunoi` nu apare.

## Cartea (`carte/index.html`)

Pe telefon: https://deradfromhell.github.io/retete/carte/ (GitHub Pages din acest repo; se actualizează la fiecare `git push`, în 1–2 minute). Un singur fișier, merge offline. Din carte nu se editează rețete; singurele scrieri sunt intrările de jurnal și pozele, care ajung ca fișiere în repo, prin GitHub, și de acolo se regenerează cartea (`.github/workflows/build.yml` rulează `build.py` la orice schimbare în `retete/`, CSV, șablon sau `build.py`; commit-ul robotului „carte regenerata” nu redeclanșează nimic). De pe calculator, înainte de `git push`, `git pull --rebase`, ca să iei commit-urile făcute din telefon și de robot. Lista: căutare, comutatoare de stare, filtre (sortare, categorie, tag) și carduri cu timp, kcal, cost, ultima notă și „din timp”. Detaliul: cifrele mari sub titlu, bară de salt (Ingrediente · Pași · Nutriție · Jurnal), ingrediente pe grupuri cu scalare de porții, pași pe etape care se bifează și pornesc cronometre, note pliate, nutriție per porție și per 100 g, tot jurnalul. Cât e deschisă o rețetă, ecranul telefonului rămâne aprins (unde browserul permite), iar „Aa” mărește textul. Cronometre: ⏱ din bară (presetări sau minute la alegere) sau atingerea unui timp din pas; oricâte în paralel, într-o bară jos, pe orice ecran; atingerea unuia îl oprește. „+ cumpărături” din rețetă deschide lista ingredientelor, debifezi ce ai deja și restul intră în listă, cu gramele însumate între rețete; în listă poți adăuga orice altceva („pâine”, „detergent”), ce bifezi coboară la „Cumpărate”, iar butonul 🛒 din antet apare doar când lista are ceva. „▶ Gătește pas cu pas” arată întâi planul (ce e din timp, etapele cu cronometrele lor, ingredientele de scos), apoi o etapă pe ecran, cu toți pașii ei bifabili, „Ai nevoie” și ce urmează. Un cronometru pornit dintr-un pas știe ce urmează: când sună, propune următorul timp din același pas („▶ apoi: 4 minute”) sau te duce la pasul următor al acelui fir („→ apoi, pasul 3”), oriunde ai fi, chiar în altă rețetă. Orice „N minute” din text devine cronometru, deci un pas se scrie cu timpii reali de așteptat și fără repetarea lor („în tot acest timp”, nu „în cele 16 minute”). Coșul, bifele lui și mărimea textului se țin doar în browserul telefonului; restul e efemer.

## Nutriție și cost

Per porție = (Σ g × valoare / 100) / porții, din gramaje crude. Per 100 g = total / `greutate_gatita_g` × 100 dacă greutatea gătită e completată (cântărește mâncarea gata), altfel pe suma ingredientelor crude, etichetat „crud”. Afișare cu „≈”: kcal rotunjit la 10, macro la 1 g, sare la 0,1 g (singura cu zecimală, pentru că 2 g și 2,5 g diferă); cost rotunjit la 0,5 lei.

Sarea (g/100 g, ca pe etichete) vine de pe etichetă sau, la rândurile USDA, din sodiu × 2,5. Reper: sub 6 g pe zi înseamnă sub ~2 g la o masă principală. Ingredientele mici au marjă de ±5%, de aceea nu afișăm precizie falsă. Ingredient fără `pret_per_kg` → cost „—”. Prețurile din seed sunt estimări (marcate „preț estimat 2026” în `nota`); se corectează de pe bonuri când e cazul.

`ingrediente.csv`: coloanele `id,nume,kcal,proteine,carbo,grasimi,fibre,sare,pret_per_kg,sursa,nota`, valori per 100 g crud. `sursa` e obligatorie: „eticheta <brand>” sau „USDA FDC <id>”. Fără sursă nu se adaugă rândul. Brandul stă doar în `sursa`; `nume` e generic („Sos de soia”), pentru că în carte contează produsul, nu marca. Ingredient necunoscut într-o rețetă = build-ul eșuează. Nutriția nu se ghicește niciodată.
