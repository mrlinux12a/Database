# -*- coding: utf-8 -*-
"""Misura la ricerca della pagina «prima» (sottostringa, nessun alias) e «dopo» (alias, misure, plurali) con le frasi di
prove_ricerca.json. Non scrive nulla.

  py -3.15 prova_ricerca.py              tabella: per ogni frase, articoli trovati e quanti sono della famiglia attesa
  py -3.15 prova_ricerca.py --persi      mostra anche gli articoli trovati prima e non piu' dopo (non dovrebbero essercene)

Per ogni frase:  n = articoli trovati,  ok = quanti sono nelle famiglie attese,  trovata = ok > 0,
purezza = ok / n (se e' bassa, la frase trova la famiglia giusta ma anche molto altro).
Controlla anche che ogni nome in alias_famiglie.json sia una famiglia che esiste.
"""
import argparse
import json
import os
import sys

import psycopg2

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(QUI, "web"))
sys.path.insert(0, QUI)
os.environ.setdefault("PGDATABASE", "db_serio_finale")
import ricerca  # noqa: E402
import server  # noqa: E402


def trova(cur, q, attese):
    cond, params = server.condizioni(q, "", "", "", 0, ())
    cur.execute("SELECT m.codice, coalesce(f.nome, '') FROM materiale m LEFT JOIN famiglia f ON f.id = m.famiglia_id WHERE " + cond,
                params)
    righe = cur.fetchall()
    ok = sum(1 for _, f in righe if f in attese)
    return {c for c, _ in righe}, len(righe), ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--persi", action="store_true")
    a = ap.parse_args()
    cur = psycopg2.connect(dbname=os.environ["PGDATABASE"], user=os.environ.get("PGUSER", "postgres"),
                           host=os.environ.get("PGHOST", "localhost")).cursor()
    with open(os.path.join(QUI, "prove_ricerca.json"), encoding="utf-8") as f:
        prove = json.load(f)["prove"]
    with open(os.path.join(QUI, "alias_famiglie.json"), encoding="utf-8") as f:
        fam_alias = json.load(f)["famiglie"]
    cur.execute("SELECT nome FROM famiglia")
    esistenti = {r[0] for r in cur.fetchall()}
    for nome in fam_alias:
        if nome not in esistenti:
            print("ATTENZIONE: alias per una famiglia che non esiste:", nome)
    for p in prove:
        for nome in p["attese"]:
            if nome not in esistenti:
                print("ATTENZIONE: famiglia attesa che non esiste:", nome, "(frase:", p["q"] + ")")

    tot = {"prima": 0, "dopo": 0, "n": 0}
    print(f"{'frase':38} {'prima: n ok':>13} {'dopo: n ok':>13}  esito")
    for p in prove:
        ricerca.ATTIVA = False
        ins_prima, n0, ok0 = trova(cur, p["q"], p["attese"])
        ricerca.ATTIVA = True
        ins_dopo, n1, ok1 = trova(cur, p["q"], p["attese"])
        da_conf = p.get("stato") == "da_confermare"
        esito = ("migliora" if ok1 > ok0 and ok0 == 0 else "piu' articoli giusti" if ok1 > ok0 else
                 "uguale" if ok1 == ok0 else "PEGGIORA")
        if ok1 == 0:
            esito = "non trovata" + (" (alias da confermare)" if da_conf else "")
        persi = ins_prima - ins_dopo
        if persi:
            esito += f"  [{len(persi)} articoli persi]"
        print(f"{p['q'][:38]:38} {n0:6} {ok0:6} {n1:7} {ok1:5}  {esito}")
        if a.persi and persi:
            print("      persi:", sorted(persi)[:10])
        if not da_conf:
            tot["n"] += 1
            tot["prima"] += ok0 > 0
            tot["dopo"] += ok1 > 0
    print(f"\nFrasi (senza quelle con alias da confermare): {tot['n']}")
    print(f"  trovano la famiglia giusta PRIMA: {tot['prima']}   DOPO: {tot['dopo']}")


if __name__ == "__main__":
    main()
