#!/usr/bin/env python3
"""Validează rețetele din retete/, calculează nutriția și generează carte/index.html. Reguli: README.md.
    python build.py --check   doar validare (raportează toate erorile odată)
    python build.py           validare + calcul + generare"""
import csv, io, json, math, re, sys
from datetime import date
from html import escape
from pathlib import Path

import yaml

RADACINA = Path(__file__).resolve().parent
DIR_RETETE = RADACINA / "retete"
FISIER_INGREDIENTE = RADACINA / "ingrediente.csv"
FISIER_SABLON = RADACINA / "sablon.html"
FISIER_CARTE = RADACINA / "carte" / "index.html"
MARCAJ_SABLON = "/*@RETETE@*/[]"
CATEGORII = ("mic-dejun", "pranz-cina", "garnitura", "desert", "sos")
STATUSURI = ("test", "imbunatatire", "carte", "gunoi")
NUTRIENTI = ("kcal", "proteine", "carbo", "grasimi", "fibre")
COLOANE_CSV = ["id", "nume", *NUTRIENTI, "pret_per_kg", "sursa", "nota"]
OBLIGATORII = ("titlu", "slug", "categorie", "sursa", "portii", "timp_activ_min", "timp_total_min", "versiune", "ingrediente")
RE_PAS = re.compile(r"^(\d+)[.)]\s+(.+)$")
RE_FRONTMATTER = re.compile(r"^---\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)(.*)$", re.S)


class Incarcator(yaml.SafeLoader):  # fără date implicite: „2026-13-40” rămâne text și îl verifică data_valida, cu mesaj clar
    yaml_implicit_resolvers = {c: [r for r in l if r[0] != "tag:yaml.org,2002:timestamp"]
                               for c, l in yaml.SafeLoader.yaml_implicit_resolvers.items()}

def este_numar(v, minim=None, maxim=None, intreg=False):
    """True dacă v e număr finit și rezonabil (nu bool, nu inf/nan, sub 1e9), de tipul cerut și în interval."""
    return (not isinstance(v, bool) and isinstance(v, int if intreg else (int, float)) and abs(v) < 1e9
            and (minim is None or v >= minim) and (maxim is None or v <= maxim))

def data_valida(v):
    """Obiect date sau None. Jurnalul folosește AAAA-LL-ZZ; YAML lasă valoarea text (vezi Incarcator)."""
    try:
        return date.fromisoformat(str(v))
    except ValueError:
        return None

def rotunjeste(x, pas=1):
    """Rotunjire „jumătate în sus” la multiplu de pas; aceleași operații ca rot() din sablon.html."""
    r = math.floor(x / pas + 0.5) * pas
    return int(r) if r == int(r) else r

def citeste_ingrediente(erori):
    """ingrediente.csv → {id: {nume, kcal, proteine, carbo, grasimi, fibre, pret_per_kg|None, sursa}}, None dacă nu se poate citi."""
    ingrediente = {}
    try:
        cititor = csv.DictReader(io.StringIO(FISIER_INGREDIENTE.read_text(encoding="utf-8-sig")))
        if cititor.fieldnames != COLOANE_CSV:
            raise ValueError(f"coloanele trebuie să fie exact: {','.join(COLOANE_CSV)}")
    except (OSError, ValueError) as ex:  # lipsă, non-UTF-8 sau antet greșit
        erori.append(f"ingrediente.csv: {'fișierul lipsește' if isinstance(ex, FileNotFoundError) else ex}")
        return None
    for rand in cititor:
        c = {col: (rand.get(col) or "").strip() for col in COLOANE_CSV}
        eroare = lambda mesaj: erori.append(f"ingrediente.csv rândul {cititor.line_num}: {mesaj}")  # noqa: E731
        if None in rand or None in rand.values():  # DictReader pune sub None câmpurile în plus sau lipsă
            eroare(f"rândul trebuie să aibă exact {len(COLOANE_CSV)} coloane (virgulă fără ghilimele în text?)")
        if not re.fullmatch(r"[a-z0-9_]+", c["id"]) or c["id"] in ingrediente:
            eroare(f"id invalid sau duplicat „{c['id']}” (doar a-z, 0-9 și _, unic)")
        if not c["nume"] or not c["sursa"]:
            eroare("lipsește numele sau sursa („eticheta <brand>” sau „USDA FDC <id>”)")
        ing = {"nume": c["nume"], "sursa": c["sursa"], "pret_per_kg": None}
        for col in NUTRIENTI + ("pret_per_kg",):
            if col == "pret_per_kg" and not c[col]:
                continue
            try:
                ing[col] = float(c[col].replace(",", "."))
                if not 0 <= ing[col] < 1e9:
                    raise ValueError
            except ValueError:
                eroare(f"„{col}” trebuie să fie un număr ≥ 0, nu „{c[col]}”")
                ing[col] = 0.0
        ingrediente[c["id"]] = ing
    return ingrediente

def citeste_reteta(cale, erori):
    """Returnează (meta, corp) sau (None, "") dacă frontmatter-ul nu se poate citi."""
    try:
        potrivire = RE_FRONTMATTER.match(cale.read_text(encoding="utf-8-sig"))
        if not potrivire:
            raise ValueError("lipsește frontmatter-ul YAML delimitat de „---”")
        chei = re.findall(r"^(\w+):", potrivire.group(1), re.M)  # PyYAML păstrează tacit ultima valoare a unei chei duplicate
        if len(chei) != len(set(chei)):
            raise ValueError(f"cheia „{next(c for c in chei if chei.count(c) > 1)}” apare de două ori în frontmatter")
        meta = yaml.load(potrivire.group(1), Incarcator)
        if not isinstance(meta, dict):
            raise ValueError("frontmatter-ul trebuie să fie o mapare cheie: valoare")
    except (OSError, ValueError, yaml.YAMLError) as ex:  # necitibil, non-UTF-8 (ValueError) sau YAML invalid
        erori.append(f"{cale.name}: {ex}")
        return None, ""
    return meta, potrivire.group(2)

def valideaza_reteta(meta, corp, cale, ingrediente, erori):
    """Verifică schema unei rețete; adaugă fiecare problemă în erori, nu se oprește la prima. True dacă e validă."""
    inainte = len(erori)
    eroare = lambda mesaj: erori.append(f"{cale.name}: {mesaj}")  # noqa: E731
    for camp in OBLIGATORII:
        if meta.get(camp) in (None, "", []):
            eroare(f"lipsește câmpul obligatoriu „{camp}”")
    slug, sursa, tags = meta.get("slug"), meta.get("sursa"), meta.get("tags") or []
    if not isinstance(meta.get("titlu", ""), str):
        eroare("titlu trebuie să fie text")
    if slug is not None and not (isinstance(slug, str) and re.fullmatch(r"[a-z0-9-]+", slug) and slug == cale.stem):
        eroare(f"slug „{slug}” trebuie să fie ASCII (a-z, 0-9, -) și identic cu numele fișierului")
    if meta.get("categorie") not in CATEGORII:
        eroare(f"categorie „{meta.get('categorie')}” nu e una din: {', '.join(CATEGORII)}")
    if sursa is not None and not (isinstance(sursa, str)
                                  and (sursa in ("claude", "propriu") or sursa.startswith(("http://", "https://")))):
        eroare("sursa trebuie să fie un URL, „claude” sau „propriu”")
    if not isinstance(tags, list) or not all(isinstance(t, str) and t.strip() for t in tags):
        eroare("tags trebuie să fie o listă de texte nevide")
    if not isinstance(meta.get("din_timp") or "", str):
        eroare("din_timp trebuie să fie text (ex. „marinare 4–6 h”)")
    for camp, minim in (("portii", 1), ("timp_activ_min", 0), ("timp_total_min", 0), ("versiune", 1), ("greutate_gatita_g", 1)):
        if meta.get(camp) is not None and not este_numar(meta[camp], minim, intreg=True):
            eroare(f"„{camp}” trebuie să fie un număr întreg ≥ {minim}")
    if (este_numar(meta.get("timp_activ_min")) and este_numar(meta.get("timp_total_min"))
            and meta["timp_total_min"] < meta["timp_activ_min"]):
        eroare("timp_total_min nu poate fi mai mic decât timp_activ_min")
    if meta.get("status_manual") not in (None, "") + STATUSURI:
        eroare(f"status_manual „{meta['status_manual']}” nu e unul din: {', '.join(STATUSURI)}")
    lista, jurnal = meta.get("ingrediente"), meta.get("jurnal") or []
    if not isinstance(lista, (list, type(None))) or not isinstance(jurnal, list):
        eroare("ingrediente și jurnal trebuie să fie liste")
    for i, ing in enumerate(lista if isinstance(lista, list) else [], start=1):
        if not isinstance(ing, dict) or not isinstance(ing.get("id"), str):
            eroare(f"ingredientul #{i} trebuie să aibă „id” (text) și „g”")
            continue
        if ingrediente is not None and ing["id"] not in ingrediente:
            eroare(f"ingredient necunoscut „{ing['id']}” — adaugă-l în ingrediente.csv, cu sursă")
        if not (este_numar(ing.get("g")) and ing["g"] > 0):
            eroare(f"ingredientul „{ing['id']}” trebuie să aibă g > 0")
    versiune_max = meta["versiune"] if este_numar(meta.get("versiune"), 1, intreg=True) else None
    for i, j in enumerate(jurnal if isinstance(jurnal, list) else [], start=1):
        if not isinstance(j, dict):
            eroare(f"jurnal #{i}: intrarea trebuie să aibă data, versiune, gust, efort, executie")
            continue
        if data_valida(j.get("data")) is None:
            eroare(f"jurnal #{i}: data lipsește sau nu e în formatul AAAA-LL-ZZ")
        for camp, minim, maxim in (("versiune", 1, versiune_max), ("gust", 1, 10), ("efort", 1, 5)):
            if not este_numar(j.get(camp), minim, maxim, intreg=True):
                eroare(f"jurnal #{i}: {camp} trebuie să fie un întreg între {minim} și {maxim or 'versiunea rețetei'}")
        if j.get("executie") not in ("ok", "greseala_mea"):
            eroare(f"jurnal #{i}: executie trebuie să fie „ok” sau „greseala_mea”")
    if not any(RE_PAS.match(linie.strip()) for linie in corp.splitlines()):
        eroare("corpul rețetei nu are niciun pas numerotat („1. …”)")
    return len(erori) == inainte

def calculeaza_status(meta):
    """Regulile din README aplicate pe ultima intrare din jurnal. Returnează (status, tag_ocazie)."""
    if meta.get("status_manual"):
        return meta["status_manual"], False
    if not (jurnal := meta.get("jurnal")):
        return "test", False
    ultima = jurnal[-1]
    if ultima["executie"] == "greseala_mea":
        return "imbunatatire", False
    if ultima["gust"] >= 8:
        return "carte", ultima["efort"] >= 4
    reusite = [j for j in jurnal if j["executie"] == "ok"]
    if ultima["gust"] <= 5 or (len(reusite) >= 3 and all(j["gust"] < 8 for j in reusite)):
        return "gunoi", False
    return "imbunatatire", False

def calculeaza_nutritie(meta, ingrediente):
    """Per porție, din gramaje crude: kcal la 10, macro la 1 g, cost la 0,5 lei (None dacă lipsește un preț)."""
    total = dict.fromkeys(NUTRIENTI, 0.0)
    cost, cost_complet = 0.0, True
    for ing in meta["ingrediente"]:
        valori = ingrediente[ing["id"]]
        for n in NUTRIENTI:
            total[n] += ing["g"] * valori[n] / 100
        cost_complet = cost_complet and valori["pret_per_kg"] is not None
        cost += ing["g"] / 1000 * (valori["pret_per_kg"] or 0)
    rezultat = {n: rotunjeste(total[n] / meta["portii"], 10 if n == "kcal" else 1) for n in NUTRIENTI}
    rezultat["cost"] = rotunjeste(cost / meta["portii"], 0.5) if cost_complet else None
    return rezultat

def corp_in_html(corp):
    """Pașii numerotați devin <ol> (cu numărul din fișier, ca etapele „## Titlu” să nu reia numerotarea), restul paragrafe."""
    html, pasi = [], []
    for linie in [l.strip() for l in corp.splitlines() if l.strip()] + [""]:  # rândurile goale nu rup lista
        if pas := RE_PAS.match(linie):
            pasi.append(f'<li value="{pas.group(1)}">{escape(pas.group(2))}</li>')
            continue
        if pasi:
            html.append(f"<ol>{''.join(pasi)}</ol>")
            pasi = []
        if titlu := re.match(r"#+\s+(.+)$", linie):
            html.append(f"<h3>{escape(titlu.group(1))}</h3>")
        elif linie:
            html.append(f"<p>{escape(linie)}</p>")
    return "".join(html)

def pregateste(meta, corp, ingrediente):
    """Structura unei rețete pentru JSON-ul din carte: stare, tag-uri, ingrediente cu valori/100 g, nutriție."""
    status, ocazie = calculeaza_status(meta)
    tags = list(dict.fromkeys(meta.get("tags") or []))
    if ocazie and "ocazie" not in tags:
        tags.append("ocazie")
    ultima = {**j[-1], "data": data_valida(j[-1]["data"]).strftime("%Y-%m-%d")} if (j := meta.get("jurnal")) else None
    return {
        "slug": meta["slug"], "titlu": meta["titlu"], "categorie": meta["categorie"], "tags": tags, "sursa": meta["sursa"],
        "status": status, "versiune": meta["versiune"], "portii": meta["portii"], "din_timp": meta.get("din_timp") or "",
        "timp_activ_min": meta["timp_activ_min"], "timp_total_min": meta["timp_total_min"], "greutate_gatita_g": meta.get("greutate_gatita_g"),
        "gust": ultima["gust"] if ultima else None, "efort": ultima["efort"] if ultima else None,
        "ingrediente": [{"id": i["id"], "nume": ingrediente[i["id"]]["nume"], "g": i["g"], "nota": str(i.get("nota") or ""),
                         "grup": str(i.get("grup") or ""), **{n: ingrediente[i["id"]][n] for n in NUTRIENTI + ("pret_per_kg",)}}
                        for i in meta["ingrediente"]],
        "nutritie": calculeaza_nutritie(meta, ingrediente),
        "pasi_html": corp_in_html(corp), "ultima": ultima,
    }

def main(argv):
    [flux.reconfigure(encoding="utf-8") for flux in (sys.stdout, sys.stderr)]
    if set(argv) - {"--check"}:
        print(__doc__)
        return 2
    erori, retete = [], []
    ingrediente = citeste_ingrediente(erori)  # None dacă CSV-ul nu se poate citi
    for cale in sorted(DIR_RETETE.glob("*.md")):
        meta, corp = citeste_reteta(cale, erori)
        if meta is not None and valideaza_reteta(meta, corp, cale, ingrediente, erori):
            retete.append((meta, corp))
    if erori:
        print(f"{len(erori)} erori, nimic generat:\n  - " + "\n  - ".join(erori))
        return 1
    print(f"OK: {len(retete)} rețete valide, {len(ingrediente)} ingrediente.")
    if "--check" in argv:
        return 0
    date_carte = [pregateste(meta, corp, ingrediente) for meta, corp in retete]
    print("".join(f"  {r['slug']:<32} {r['status']:<13} ≈{r['nutritie']['kcal']} kcal/porție\n" for r in date_carte), end="")
    vizibile = [r for r in date_carte if r["status"] != "gunoi"]
    sablon = FISIER_SABLON.read_text(encoding="utf-8") if FISIER_SABLON.is_file() else ""
    if MARCAJ_SABLON not in sablon:
        sys.exit(f"sablon.html: lipsește fișierul sau marcajul {MARCAJ_SABLON}")
    json_text = json.dumps(vizibile, ensure_ascii=False, default=str)
    json_text = json_text.replace("</", "<\\/").replace("<!--", "<\\!--")  # interzise literal într-un <script>; în JS „\/” = „/”
    FISIER_CARTE.parent.mkdir(exist_ok=True)
    FISIER_CARTE.write_text(sablon.replace(MARCAJ_SABLON, json_text), encoding="utf-8")
    print(f"Scris carte/index.html: {len(vizibile)} rețete afișabile, {len(date_carte) - len(vizibile)} la gunoi.")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
