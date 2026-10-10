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
| `inbox/` | rețete brute trimise din carte (text, link, poză), până le transformă Claude în `retete/<slug>.md` |

## Comenzi

```bash
python build.py --check   # validează toate rețetele și CSV-ul; raportează toate erorile odată
python build.py           # check + calcul + generează carte/index.html
```

Cerințe: Python 3 și PyYAML (`pip install pyyaml`). Nimic altceva. Pe Windows, dacă `python` deschide Microsoft Store, folosește `py build.py` (launcher-ul Python).

## Fluxul de lucru

**Rețetă găsită pe telefon.** În carte, butonul „+” de lângă titlu: lipești textul sau linkul rețetei (de pe net, de la alt AI, din cap) și, dacă vrei, o captură de ecran. Ajunge în repo, în `inbox/` (un `.md` și poza), cu același token ca jurnalul. Apoi îi spui lui Claude „convertește inboxul”: el face din fiecare rețetă completă, în schemă, și șterge fișierul din inbox. `build.py` nu citește `inbox/`.

**Rețetă nouă.** Claude propune 2–3 surse testate (sau o rețetă clasică, `sursa: claude`), eu aleg. Claude o scrie în schemă, convertește totul în grame cu `conversii.md` (cantitatea originală merge în `nota`), adaugă ingredientele lipsă în `ingrediente.csv` cu sursă, rulează `--check`, commit `reteta <slug> v1`.

**Note pe pași.** Creionul de lângă fiecare pas, în rețetă și când gătești, ține o notă („3 minute e prea mult”) doar pe telefon, până scrii în jurnal; atunci intră în intrare, la `pasi`. Data următoare, nota apare sub pas, „Data trecută: …”, cât timp versiunea rețetei e aceeași.

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
    pasi:                      # opțional: note pe pași, cu numărul pasului
      4: 16 minute au fost prea multe, 14 ajung
---
## Pregătire
1. Încinge uleiul în tigaie, ~1 min, până unduiește.
2. ...

## Note
Ce nu e sigur: timpi, sare, temperatura cuptorului.
```

După pași vine `## Păstrare și reîncălzire` (cât ține la frigider sau congelator și cum se reîncălzește, pe metode: air fryer, tigaie, microunde, cu temperatură, timp și semn că e gata), apoi `## Note`; cartea arată reîncălzirea deschis, cu buton în bara de salt, iar notele pliate. Titlurile `## …` dintre pași grupează pașii pe etape; numerotarea continuă (se folosește numărul scris în fișier). Pașii unei etape se fac în ordine. Ce se face în paralel merge în etapă separată, iar titlul spune când: „Orezul (pornește odată cu puiul)”. Ultima etapă se cheamă „Servire” și nu e propusă înainte de vreme. Timpii pentru altă zi, cum ar fi din congelat sau la reîncălzire, stau la „Păstrare și reîncălzire”, nu în pași, altfel devin cronometre. Cartea înțelege și aceste formulări: un total urmat de bucăți („35 de minute; întoarce-i după 15 minute, apoi încă 20”), „la fiecare N minute”, „la jumătate” și „în ultimele N minute” în titlul unei etape. În carte, pașii se bifează prin atingere, iar orice „8 minute” sau „30–60 de secunde” dintr-un pas pornește un cronometru cu sunet la final. Timpul total se afișează în ore și minute. Toate cantitățile în grame. Nume de fișiere și id-uri: ASCII, fără diacritice. Conținutul: română cu diacritice. `sursa` e un URL complet (cu `http://` sau `https://`), `claude` sau `propriu`.

## Poze

Poza unei rețete e fișierul `retete/poze/<slug>.jpg`; dacă există, cartea o arată pe card și în detaliu, altfel rămâne inițiala. Build-ul refuză pozele care nu corespund unei rețete.

Din telefon: în rețetă, „Poză” alege sau face o poză, o micșorează (~1200 px) și o trimite direct în repo, ca un commit, prin API-ul GitHub. Pentru asta (și pentru jurnal) cartea are nevoie de un token personal, pe care îl faci o singură dată, de preferat tot de pe telefon, logat în GitHub:

1. github.com → poza de profil → **Settings** → jos, **Developer settings** → **Personal access tokens** → **Fine-grained tokens** → **Generate new token**.
2. Nume oricare; **Expiration** cum vrei (la expirare faci altul); **Repository access**: *Only select repositories* → `retete`.
3. **Permissions** → *Repository permissions* → **Contents**: *Read and write* (restul rămân „No access”). Generate token, copiază-l (începe cu `github_pat_`).
4. În carte: jos, sub lista de rețete, **Pune token-ul** → lipește. Cartea îl verifică pe loc (acces la repo și drept de scriere) și îl ține doar în browserul telefonului; textul de lângă buton spune dacă e salvat. Dacă lipsește sau e refuzat, sub „Poză” și „Scrie în jurnal” apare un mesaj roșu cu motivul. Poza apare pe loc pe telefonul tău și în 1–2 minute pe celelalte, după ce GitHub Pages publică commit-ul.

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

Pe telefon: https://deradfromhell.github.io/retete/carte/ (GitHub Pages din acest repo; se actualizează la fiecare `git push`, în 1–2 minute). Un singur fișier, merge offline. Din carte nu se editează rețete; singurele scrieri sunt intrările de jurnal și pozele, care ajung ca fișiere în repo, prin GitHub, și de acolo se regenerează cartea (`.github/workflows/build.yml` rulează `build.py` la orice schimbare în `retete/`, CSV, șablon sau `build.py`; commit-ul robotului „carte regenerata” nu redeclanșează nimic). De pe calculator, înainte de `git push`, `git pull --rebase`, ca să iei commit-urile făcute din telefon și de robot.

**Aspectul.** Poze mari, fond alb, fonturile Bricolage Grotesque (titluri) și Figtree (text), de la Google Fonts; fără internet, cartea folosește fonturile salvate la prima deschidere sau pe cele ale telefonului. Până pui o poză, rețeta are un desen pe culoarea categoriei. Roșul e pentru foc și timp, negrul pentru acțiunea principală.

**Lista.** Căutare, filtre (stare, sortare, categorie, tag), carduri cu timp, kcal, gust și „din timp”; atingerea cardului deschide rețeta, butonul „Gătesc” de pe card o adaugă la gătit fără să o deschizi. Mai multe ingrediente despărțite prin virgulă („pui, orez, ardei”) înseamnă „ce am în casă”: apar rețetele care folosesc cel puțin unul, întâi cele cu cele mai multe, iar cardul spune care. Catalogul pe feluri (Pui, Porc, Vită, Pește, Ouă, Fără carne) se face singur, după carnea cu cele mai multe grame, și apare sub căutare doar când există cel puțin două feluri cu câte cel puțin două rețete.

**Frigiderul (opțional).** La finalul unei mese, cartea întreabă câte porții pun la frigider (implicit toate în afară de una). Pe prima pagină apare „În frigider”, cu porțiile și până când se mănâncă, după „Frigider: N zile” din „Păstrare și reîncălzire”, plus „Am mâncat una”. Din lista de cumpărături, „Gătește-le pe toate acum” pune toate rețetele din listă la aceeași masă, pentru meal prep.

**Rețeta.** Cifrele mari sub titlu, bară de salt (Ingrediente, Pași, Reîncălzire, Nutriție, Jurnal), ingrediente pe grupuri cu scalare de porții (lingurile și lingurițele se recalculează, în fracții: 1/2, 3/4), pași pe etape care se bifează și pornesc cronometre, păstrare și reîncălzire, note pliate, nutriție per porție și per 100 g, jurnalul cu formularul de intrare nouă (arată pe loc în ce stare ajunge rețeta). „Aa” mărește textul.

**Masa: una sau mai multe rețete gătite împreună.** „Gătește” pune rețeta la masă; din altă rețetă, „Gătește și asta, la aceeași masă” adaugă încă una. Planul arată ordinea în care pornești, ca să fie gata toate odată (cea mai lungă prima, cealaltă cu un cronometru „până pornești X”), ce poți face din timp (bifat, pașii aceia apar deja făcuți și planul se scurtează), porțiile și ce scoți pe blat. La gătit, fiecare rețetă are fila ei, cu culoarea ei, și o etapă pe ecran: pașii bifabili, „Ai nevoie” (ce ingrediente intră acum, cu gramajul) și ce urmează. Cât aștepți un cronometru, ecranul spune ce poți face între timp: etapa următoare a aceleiași rețete, dacă tot ce a rămas din etapa curentă are cronometrul pornit (orezul cât e puiul în air fryer), sau pasul următor din cealaltă rețetă. La o așteptare de 8 minute sau mai mult (cartofii fierb), propune și etapa următoare, ca opțiune („Dacă vrei, între timp”). Când sună, cronometrul propune următorul timp din același pas sau te duce la pasul următor („Apoi pasul 9”), chiar dacă ești în altă rețetă, și bifează singur pasul cu timpul. Alarma rămâne pe ecran până o atingi. Cât merge un cronometru lung, „amestecă la fiecare 10 minute” și „întoarce la jumătate” devin mementouri: două bipuri scurte și textul, cu galben, în bara de jos, fără să oprească cronometrul. O etapă „(în ultimele 25 de minute ale tocăniței)” e anunțată când cronometrul cel lung al rețetei mai are 25 de minute. „Revino la pasul 6” din text e un link către pasul 6.

**Un singur air fryer.** Dacă două rețete de la masă folosesc air fryer-ul, sau cuptorul la temperaturi diferite, planul întreabă dacă ai unul singur. Răspunsul se ține minte pe telefon. Dacă da, le faci pe rând: rețeta care intră prima în aparat îl ține până îi termină pașii de acolo. Cealaltă vede „Air fryer-ul e ocupat” și ce poți face între timp, iar când se eliberează, cartea anunță „Air fryer-ul e liber” cu pasul de reluat. Cartea știe ce pași folosesc aparatul din text: de la primul pas care îl pomenește („air fryer”, „coș”, „cuptor”) până la ultimul, și mai departe până când mâncarea iese („scoate … pe o grilă”, pe tocător, pe foc). „Când puiul intră în air fryer” e doar un moment, nu o folosire. Când termini o rețetă, „Continuă cu …” te duce la cealaltă; la final, butoane spre jurnalul fiecăreia. Orice „N minute” dintr-un pas devine cronometru; timpii alternativi („sau la cuptor 18 minute”, „ultimele 2 minute”, „în total 20 de minute”) apar ca atare, dar nu sunt propuși ca „apoi”.

**Cronometre.** Din bara de sus (presetări sau minute la alegere) sau atingând un timp din pas; oricâte în paralel, în bara neagră de jos, pe orice ecran, fiecare cu un cerc care se umple pe măsură ce trece timpul. Sună și vibrează la final și trimit o notificare dacă ai dat voie. Ecranul rămâne aprins cât gătești (unde browserul permite). Cu telefonul blocat, browserul poate întârzia sunetul: pe iPhone, notificările merg doar dacă pui cartea pe ecranul principal (Safari, Partajare, „Adaugă pe ecranul principal”); pe Android, din Chrome, „Instalează aplicația”. Instalată, cartea se deschide și fără internet (`carte/sw.js` păstrează ultima versiune).

**Cumpărături.** „Cumpărături” din rețetă deschide ingredientele; debifezi ce ai deja și restul intră în listă, cu gramele însumate între rețete și cu un punct colorat pentru fiecare rețetă. Poți adăuga orice altceva („pâine”, „detergent”); ce bifezi coboară la „Cumpărate”. Butonul coșului din antet apare doar când lista are ceva.

Masa în curs, cronometrele (cu ora la care sună), coșul și mărimea textului se țin în browserul telefonului, deci supraviețuiesc unei reîncărcări a paginii.

**Simulare.** `carte/index.html?viteza=60` face cronometrele de 60 de ori mai rapide (un minut trece într-o secundă), ca să încerci o masă întreagă în câteva minute. Doar pentru test.

`carte/sw.js`, `carte/manifest.webmanifest` și `carte/icon.svg` sunt fișiere statice, scrise de mână, nu generate.

## Nutriție și cost

Per porție = (Σ g × valoare / 100) / porții, din gramaje crude. Per 100 g = total / `greutate_gatita_g` × 100 dacă greutatea gătită e completată (cântărește mâncarea gata), altfel pe suma ingredientelor crude, etichetat „crud”. Afișare cu „≈”: kcal rotunjit la 10, macro la 1 g, sare la 0,1 g (singura cu zecimală, pentru că 2 g și 2,5 g diferă); cost rotunjit la 0,5 lei.

Sarea (g/100 g, ca pe etichete) vine de pe etichetă sau, la rândurile USDA, din sodiu × 2,5. Reper: sub 6 g pe zi înseamnă sub ~2 g la o masă principală. Ingredientele mici au marjă de ±5%, de aceea nu afișăm precizie falsă. Ingredient fără `pret_per_kg` → cost „—”. Prețurile din seed sunt estimări (marcate „preț estimat 2026” în `nota`); se corectează de pe bonuri când e cazul.

`ingrediente.csv`: coloanele `id,nume,kcal,proteine,carbo,grasimi,fibre,sare,pret_per_kg,sursa,nota`, valori per 100 g crud. `sursa` e obligatorie: „eticheta <brand>” sau „USDA FDC <id>”. Fără sursă nu se adaugă rândul. Brandul stă doar în `sursa`; `nume` e generic („Sos de soia”), pentru că în carte contează produsul, nu marca. Ingredient necunoscut într-o rețetă = build-ul eșuează. Nutriția nu se ghicește niciodată.
