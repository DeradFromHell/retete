# Idei (backlog)

Aici se parchează ideile. Nu se construiește nimic până nu există 10 rețete cu cel puțin o intrare în jurnal.

- scor „merită” = gust ponderat cu efort, calculat doar la afișare, pentru sortare; nu se stochează, nu influențează statusul
- câte o poză per intrare în jurnal (acum e una per rețetă, `retete/poze/<slug>.jpg`)
- la masă, cu un singur air fryer: cartea să aleagă singură ordinea (întâi rețeta care mai are mult de lucru după aparat)

## Consiliul din 2026-11-11 (bucătar, designer UX, inginer, strateg de produs)

Verdict: îngheț pe funcții noi până la 10 jurnale; excepții doar pentru pierderi de date și textul rețetelor. Întâi se gătesc cele două v2 (șnițel, pui cu miere). Făcut atunci: trecerea de text prin rețete (pregătire, ture, siguranță) și un commit de cod (ciornă de jurnal, token păstrat la 403, lista arată toate stările).

Rețete noi, câte două, după ce sunt gătite cele două v2; timpii scriși în minute, nu în ore:
- orezul cu legume în tigaie (cel pe care îl faci deja), cartofi la air fryer
- salată de castraveți, paste cu carne tocată și roșii

La dezgheț, în ordinea asta:
- teste în repo pentru citirea timpilor din pași (azi „1 oră și 30 de minute” ar da un cronometru de 30 de minute, iar „1 oră” niciunul); înaintea oricărei schimbări la cronometre
- pe alarmă, „Încă 2 minute”, care devine singur notă pe pas
- la gătit, mai mult loc pentru textul pasului și „Începe” lipit jos (dacă la gătit chiar încurcă)
- câmp `ture` în rețetă, în locul celor două timpuri scrise în pas
- eticheta cronometrului „Pasul 4 · 35 de minute”; foaie pentru token în loc de prompt(); stare salvată cu versiune

Respinse: publicare fără commit-ul robotului, mutarea calculului de nutriție din build.py.
