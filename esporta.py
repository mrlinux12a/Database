# -*- coding: utf-8 -*-
"""Esporta il risultato del lavoro su UN catalogo in un file (JSON, anche .gz) da consegnare a chi tiene il database principale.
Dentro ci sono SOLO: codice, nomeV1, nomeV2, famiglia, attributi (con origine e fonte), attributi candidati.
Niente prezzi, sconti o altri dati commerciali.

  py -3.13 esporta.py --catalogo "Acme SRL" [--out esportazioni/acme_srl.json.gz]
"""
import argparse
import datetime
import gzip
import json
import os

from arricchimento import cataloghi
from arricchisci import collega, CATALOGO_DEFAULT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogo", default=CATALOGO_DEFAULT)
    ap.add_argument("--out")
    a = ap.parse_args()
    out = a.out or os.path.join("esportazioni", cataloghi.slug(a.catalogo) + ".json.gz")
    conn = collega()
    cur = conn.cursor()
    cur.execute("""select m.codice, m.cod_fornitore, m.nomev1, m.nomev2, f.nome from materiale m
                   left join famiglia f on f.id = m.famiglia_id where m.catalogo = %s order by m.codice""", (a.catalogo,))
    articoli = {r[0]: {"codice": r[0], "cod_fornitore": r[1], "nomev1": r[2], "nomev2": r[3], "famiglia": r[4], "attributi": []}
                for r in cur.fetchall()}
    cur.execute("""select x.codice, x.chiave, x.valore, x.valore_num, x.unita, x.origine, x.fonte
                   from materiale_attributo x join materiale m on m.codice = x.codice where m.catalogo = %s
                   order by x.codice, x.chiave""", (a.catalogo,))
    for codice, chiave, valore, num, unita, origine, fonte in cur.fetchall():
        articoli[codice]["attributi"].append([chiave, valore, float(num) if num is not None else None, unita, origine, fonte])
    cur.execute("select testo, esempio_codice, n, stato, note from attributo_candidato where catalogo = %s order by n desc",
                (a.catalogo,))
    candidati = [list(r) for r in cur.fetchall()]
    dati = {"versione": 1, "catalogo": a.catalogo, "creato": datetime.datetime.now().isoformat(timespec="seconds"),
            "articoli": list(articoli.values()), "attributi_candidato": candidati}
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    apri = gzip.open if out.endswith(".gz") else open
    with apri(out, "wt", encoding="utf-8") as f:
        json.dump(dati, f, ensure_ascii=False)
    n_att = sum(len(x["attributi"]) for x in articoli.values())
    print("Esportato %r: %d articoli, %d attributi, %d candidati -> %s" % (a.catalogo, len(articoli), n_att, len(candidati), out))


if __name__ == "__main__":
    main()
