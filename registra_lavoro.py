# -*- coding: utf-8 -*-
"""Registra un lavoro di raggruppamento delle famiglie in lavori_raggruppamento.json.

Nella pagina web le famiglie (e le categorie) con almeno un lavoro mostrano in alto a destra una barretta per ogni lavoro:
VERDE = raggruppamento fatto (nuovo), AZZURRA = raggruppamento aggiornato o migliorato. Ogni volta che si lavora su una famiglia
si aggiunge una riga: va lanciato DOPO aver applicato le regole (unisci_famiglie.py).

  py -3.15 registra_lavoro.py --tipo nuovo --prefisso "Raccordo" --nota "Raccordi: 36 famiglie -> 10 tipi"
  py -3.15 registra_lavoro.py --tipo migliorato --famiglie "Valvola a sfera;Valvola di zona" --nota "..."

  --prefisso X     tutte le famiglie del database il cui nome comincia con X (solo quelle che hanno articoli)
  --famiglie "A;B" elenco esatto dei nomi
  --prova          mostra cosa scriverebbe senza scrivere
Il file si committa (la pagina web, anche sulla VPS, lo legge da li').
"""
import argparse
import datetime
import json
import os

from arricchisci import collega

FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lavori_raggruppamento.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tipo", choices=["nuovo", "migliorato"], required=True)
    ap.add_argument("--nota", required=True, help="una riga: cosa e' stato fatto")
    ap.add_argument("--prefisso")
    ap.add_argument("--famiglie")
    ap.add_argument("--data", default=datetime.date.today().isoformat())
    ap.add_argument("--prova", action="store_true")
    a = ap.parse_args()
    if bool(a.prefisso) == bool(a.famiglie):
        ap.error("serve uno solo tra --prefisso e --famiglie")

    cur = collega().cursor()
    cur.execute("select f.nome from famiglia f where exists (select 1 from materiale m where m.famiglia_id = f.id) order by 1")
    esistenti = [r[0] for r in cur.fetchall()]
    if a.prefisso:
        nomi = [n for n in esistenti if n.lower().startswith(a.prefisso.lower())]
    else:
        nomi = [n.strip() for n in a.famiglie.split(";") if n.strip()]
        mancanti = [n for n in nomi if n not in esistenti]
        if mancanti:
            raise SystemExit("Famiglie che non esistono (o senza articoli): " + "; ".join(mancanti))
    if not nomi:
        raise SystemExit("Nessuna famiglia trovata.")

    dati = json.load(open(FILE, encoding="utf-8")) if os.path.exists(FILE) else {"lavori": []}
    base = a.data + "-" + (a.prefisso or nomi[0]).lower().replace(" ", "-")[:30]
    ids = {l["id"] for l in dati["lavori"]}
    id_, n = base, 2
    while id_ in ids:
        id_, n = "%s-%d" % (base, n), n + 1
    voce = {"id": id_, "data": a.data, "tipo": a.tipo, "nota": a.nota, "famiglie": nomi}
    print(("[prova] " if a.prova else "") + "%s (%s): %d famiglie" % (id_, a.tipo, len(nomi)))
    print("  " + "; ".join(nomi[:12]) + ("; ..." if len(nomi) > 12 else ""))
    if not a.prova:
        dati["lavori"].append(voce)
        with open(FILE, "w", encoding="utf-8") as f:
            json.dump(dati, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print("scritto", FILE)


if __name__ == "__main__":
    main()
