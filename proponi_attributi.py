# -*- coding: utf-8 -*-
"""Cerca nel nomeV2 di un catalogo i pezzi di testo che si ripetono su molti articoli: sono candidati a diventare un attributo
(e quindi a sparire dal nome, dando il nomeV3). Li scrive in `attributo_candidato` con stato 'proposto'; li approva una persona.

  py -3.13 proponi_attributi.py --catalogo "Air Control SRL" [--min 5]
"""
import argparse
import collections

import psycopg2.extras

from arricchisci import collega, CATALOGO_DEFAULT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogo", default=CATALOGO_DEFAULT)
    ap.add_argument("--min", type=int, default=5, help="minimo di articoli in cui il testo deve comparire")
    a = ap.parse_args()
    conn = collega()
    cur = conn.cursor()
    cur.execute("select cod_fornitore, nomev2 from materiale where catalogo = %s and nomev2 is not null", (a.catalogo,))
    conta, esempio = collections.Counter(), {}
    for cod, n2 in cur.fetchall():
        for seg in {s.strip().lower() for s in n2.split(",")[1:] if s.strip()}:    # il primo pezzo e' il nome base
            conta[seg] += 1
            esempio.setdefault(seg, cod)
    trovati = [(t, n) for t, n in conta.most_common() if n >= a.min]
    if trovati:
        psycopg2.extras.execute_values(
            cur, """insert into attributo_candidato (catalogo, testo, esempio_codice, n) values %s
                    on conflict (catalogo, testo) do update set n = excluded.n, esempio_codice = excluded.esempio_codice""",
            [(a.catalogo, t, esempio[t], n) for t, n in trovati])
    conn.commit()
    print("%d candidati (testo in almeno %d articoli) scritti in attributo_candidato:" % (len(trovati), a.min))
    for t, n in trovati[:40]:
        print("  %5d  %s   (es. %s)" % (n, t, esempio[t]))


if __name__ == "__main__":
    main()
