# -*- coding: utf-8 -*-
"""Segnetto ROSSO «nuovo» sulle famiglie e sui tipi nati lavorando un catalogo (file famiglie_nuove.json, da committare).

  py -3.15 segna_nuove.py --catalogo "Watts" --inizio     PRIMA di creare le famiglie del catalogo: fotografa le famiglie che ci sono
  py -3.15 segna_nuove.py --catalogo "Watts"              DOPO (proponi/unisci/assegna): segna come nuove quelle che prima non c'erano
  py -3.15 segna_nuove.py --conferma "Manometro;Sonda"    una persona le ha approvate: via il segnetto
  py -3.15 segna_nuove.py --conferma-catalogo "Watts"     via tutti i segnetti di quel catalogo
  --prova                                                 mostra senza scrivere

Nuova = famiglia con almeno un articolo del catalogo (anche solo «anche» in tipo_incerto) il cui nome non c'era nella
fotografia e che NON ha ancora avuto un tentativo di raggruppamento (dal 2026-11-20: i tipi di famiglie_comuni.py e le famiglie
con un lavoro in lavori_raggruppamento.json non prendono il rosso; le famiglie da approvare non sono famiglie). «tipo» se la sua prima parola e' quella di una famiglia che c'era gia' (Valvola di sovrapressione: la famiglia
Valvola c'era, il tipo no); «famiglia» se e' nuova anche la prima parola (Manometro). Nella pagina web: barretta rossa sulla
scheda della famiglia e della sua categoria, e la voce «nuovo» nella legenda. Il segnetto resta finche' non si conferma.
Si va per NOME (non per id): rifare le famiglie (azzera, proponi, unisci) non toglie e non sposta i segnetti.
"""
import argparse
import datetime
import json
import os
import re

from arricchisci import collega
from arricchimento.famiglie_comuni import TIPI

FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "famiglie_nuove.json")
FILE_LAVORI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lavori_raggruppamento.json")


def prima_parola(nome):
    return re.split(r"[\s/,]+", nome.strip().lower())[0]


def leggi():
    if os.path.exists(FILE):
        with open(FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"cataloghi": {}}


def scrivi(dati):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(dati, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("scritto", FILE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogo")
    ap.add_argument("--inizio", action="store_true")
    ap.add_argument("--conferma", help='nomi separati da ";"')
    ap.add_argument("--conferma-catalogo")
    ap.add_argument("--data", default=datetime.date.today().isoformat())
    ap.add_argument("--prova", action="store_true")
    a = ap.parse_args()
    dati = leggi()
    cat = dati.setdefault("cataloghi", {})

    if a.conferma or a.conferma_catalogo:
        nomi = {n.strip() for n in (a.conferma or "").split(";") if n.strip()}
        tolti = []
        for c, voce in cat.items():
            for n in list(voce.get("nuove", {})):
                if n in nomi or c == a.conferma_catalogo:
                    tolti.append((c, n))
                    if not a.prova:
                        del voce["nuove"][n]
        print("segnetti tolti: %d  %s" % (len(tolti), "; ".join("%s (%s)" % (n, c) for c, n in tolti)))
        if not a.prova:
            scrivi(dati)
        return
    if not a.catalogo:
        ap.error("serve --catalogo (oppure --conferma / --conferma-catalogo)")

    cur = collega().cursor()
    cur.execute("SELECT DISTINCT f.nome FROM famiglia f WHERE EXISTS (SELECT 1 FROM materiale m WHERE m.famiglia_id = f.id)")
    esistenti = sorted(r[0] for r in cur.fetchall())
    if a.inizio:
        cur.execute("SELECT count(*) FROM materiale WHERE catalogo = %s AND famiglia_id IS NOT NULL", (a.catalogo,))
        gia = cur.fetchone()[0]
        if gia:
            print("attenzione: %d articoli di %s hanno gia' una famiglia; le famiglie solo di %s contano come «c'erano»"
                  % (gia, a.catalogo, a.catalogo))
        print("fotografia: %d famiglie" % len(esistenti))
        if not a.prova:
            cat[a.catalogo] = {"data": a.data, "nuove": cat.get(a.catalogo, {}).get("nuove", {}), "prima": esistenti}
            scrivi(dati)
        return

    voce = cat.get(a.catalogo)
    if not voce or "prima" not in voce:
        raise SystemExit("Manca la fotografia: lancia prima  segna_nuove.py --catalogo \"%s\" --inizio  (prima di creare le "
                         "famiglie del catalogo)." % a.catalogo)
    prima = set(voce["prima"])
    parole_prima = {prima_parola(n) for n in prima}
    tipo_incerto = "LEFT JOIN tipo_incerto t ON t.codice = m.codice"
    cur.execute("SELECT to_regclass('tipo_incerto') IS NOT NULL")
    if not cur.fetchone()[0]:
        tipo_incerto = "LEFT JOIN (SELECT NULL::text codice, NULL::int famiglia_id) t ON false"
    cur.execute("SELECT DISTINCT f.nome FROM materiale m " + tipo_incerto +
                " JOIN famiglia f ON f.id = m.famiglia_id OR f.id = t.famiglia_id WHERE m.catalogo = %s", (a.catalogo,))
    del_catalogo = sorted(r[0] for r in cur.fetchall())
    # il rosso e' solo per famiglie/tipi nuovi che non hanno ancora avuto un tentativo di raggruppamento: niente rosso ai tipi
    # di famiglie_comuni.py (nati da una regola di unione) ne' alle famiglie con un lavoro in lavori_raggruppamento.json
    raggruppate = set(TIPI)
    try:
        with open(FILE_LAVORI, encoding="utf-8") as f:
            raggruppate |= {n for l in json.load(f).get("lavori", []) for n in l.get("famiglie", [])}
    except (OSError, ValueError):
        pass
    nuove = {}
    for n in del_catalogo:
        if n in prima or n in raggruppate:
            continue
        w = prima_parola(n)
        nuove[n] = {"tipo": "tipo" if w in parole_prima else "famiglia", "categoria": w if w in parole_prima else None}
    vecchie = voce.get("nuove", {})
    for n in list(vecchie):                     # segnetti di prima su famiglie che non esistono piu' (rinominate/unite): via
        if n not in nuove and n not in esistenti:
            print("  (tolto: %s non esiste piu')" % n)
    voce["nuove"] = {n: dict(vecchie.get(n, {}), **info, data=vecchie.get(n, {}).get("data", a.data)) for n, info in nuove.items()}
    print("%s: %d famiglie con articoli del catalogo, %d nuove (%d tipi in famiglie che c'erano, %d famiglie nuove)"
          % (a.catalogo, len(del_catalogo), len(nuove), sum(1 for x in nuove.values() if x["tipo"] == "tipo"),
             sum(1 for x in nuove.values() if x["tipo"] == "famiglia")))
    for n, info in sorted(nuove.items(), key=lambda x: (x[1]["tipo"], x[0])):
        print("  %-8s %s" % (info["tipo"], n))
    if not a.prova:
        scrivi(dati)


if __name__ == "__main__":
    main()
