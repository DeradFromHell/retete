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

**După gătit.** Scriu o singură propoziție: „piept-pui-orez: gust 7, efort 3, prea sărat, data viitoare jumătate sare”. Dacă am greșit eu, spun „greșeala mea: am ars ceapa”. Claude adaugă intrarea în jurnal cu `executie` corect, rulează build, commit `<slug> v1: gust 7 efort 3`. Dacă propoziția e completă, nu pune întrebări.

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

## Nutriție și cost

Per porție = (Σ g × valoare / 100) / porții, din gramaje crude. Per 100 g = total / `greutate_gatita_g` × 100 dacă greutatea gătită e completată (cântărește mâncarea gata), altfel pe suma ingredientelor crude, etichetat „crud”. Afișare cu „≈”: kcal rotunjit la 10, macro la 1 g, fără zecimale; cost rotunjit la 0,5 lei. Ingredientele mici au marjă de ±5%, de aceea nu afișăm precizie falsă. Ingredient fără `pret_per_kg` → cost „—”. Prețurile din seed sunt estimări (marcate „preț estimat 2026” în `nota`); se corectează de pe bonuri când e cazul.

`ingrediente.csv`: coloanele `id,nume,kcal,proteine,carbo,grasimi,fibre,pret_per_kg,sursa,nota`, valori per 100 g crud. `sursa` e obligatorie: „eticheta <brand>” sau „USDA FDC <id>”. Fără sursă nu se adaugă rândul. Ingredient necunoscut într-o rețetă = build-ul eșuează. Nutriția nu se ghicește niciodată.
