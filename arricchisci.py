# -*- coding: utf-8 -*-
"""Riempie nel database `nomev1` e gli attributi di ogni articolo.

  py -3.13 arricchisci.py            -> calcola e scrive nel database (tutto in una transazione)
  py -3.13 arricchisci.py --prova    -> calcola e mostra le statistiche, senza scrivere

Cosa fa
  * legge gli articoli di `materiale`;
  * per ognuno calcola nomev1 e gli attributi (arricchimento/parse.py: descrizione + codice + scheda del produttore);
  * aggiunge i valori trovati con le ricerche mirate sul web (arricchimento/web.py), se presenti;
  * riscrive l'elenco `attributo` e le righe di `materiale_attributo` (solo i valori trovati: niente NULL).
Si puo' rieseguire quando si vuole; va rieseguito dopo ogni import_catalogo.py (l'import cancella e ricrea le righe).
"""
import argparse
import collections
import os
import sys

import psycopg2
import psycopg2.extras

from arricchimento import attributi, parse, v2

try:
    from arricchimento import web
except ImportError:
    web = None

AQUI = os.path.dirname(os.path.abspath(__file__))
DB = dict(dbname=os.environ.get("DB_NAME", "db_serio_finale"), user=os.environ.get("DB_USER", "postgres"),
          host=os.environ.get("DB_HOST", "localhost"), password=os.environ.get("DB_PASSWORD") or None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prova", action="store_true", help="non scrive nel database")
    a = ap.parse_args()

    conn = psycopg2.connect(**DB)
    cur = conn.cursor()
    with open(os.path.join(AQUI, "schema.sql"), encoding="utf-8") as f:
        cur.execute(f.read())
    cur.execute("select codice, cod_fornitore, descrizione from materiale order by codice")
    righe = cur.fetchall()
    parse.registra_codici([r[1] for r in righe])

    nomi, attrs, errori = {}, {}, 0
    nomi2 = {}
    for codice, forn, descr in righe:
        try:
            nome, at = parse.analizza(forn, descr)
        except Exception as e:                      # un articolo strano non deve fermare tutto
            errori += 1
            print("ERRORE", forn, repr(e), file=sys.stderr)
            continue
        if web:
            nome, at = web.integra(forn, descr, nome, at)
        nomi[codice] = nome
        nomi2[codice] = v2.pulisci(nome, at)
        attrs[codice] = at

    conta = collections.Counter(k for at in attrs.values() for k in at)
    orig = collections.Counter((k, v["origine"]) for at in attrs.values() for k, v in at.items())
    print(f"{len(righe)} articoli, {len(nomi)} nomi, {sum(conta.values())} valori di attributo, {errori} errori")
    for chiave, etichetta, gruppo, nuovo in attributi.ATTRIBUTI:
        o = {k2: n for (k1, k2), n in orig.items() if k1 == chiave}
        print(f"  {chiave:<18} {conta.get(chiave, 0):5d}   {o if o else ''}")
    if a.prova:
        return 0

    chiavi_ok = set(attributi.CHIAVI)
    cur.execute("delete from materiale_attributo")
    cur.executemany(
        """insert into attributo (chiave, etichetta, gruppo, nuovo, ordine, breve) values (%s,%s,%s,%s,%s,%s)
           on conflict (chiave) do update set etichetta = excluded.etichetta, gruppo = excluded.gruppo,
                                              nuovo = excluded.nuovo, ordine = excluded.ordine, breve = excluded.breve""",
        [(c, e, g, n, i, attributi.BREVE[c]) for i, (c, e, g, n) in enumerate(attributi.ATTRIBUTI, 1)])
    psycopg2.extras.execute_values(
        cur, "update materiale m set nomev1 = v.n from (values %s) as v(c, n) where m.codice = v.c",
        list(nomi.items()), page_size=1000)
    psycopg2.extras.execute_values(
        cur, "update materiale m set nomev2 = v.n from (values %s) as v(c, n) where m.codice = v.c",
        list(nomi2.items()), page_size=1000)
    rows = [(codice, k, v["valore"], v.get("num"), v.get("unita"), v["origine"], v.get("fonte"))
            for codice, at in attrs.items() for k, v in at.items() if k in chiavi_ok]
    psycopg2.extras.execute_values(
        cur, """insert into materiale_attributo (codice, chiave, valore, valore_num, unita, origine, fonte) values %s""",
        rows, page_size=2000)
    conn.commit()
    print("scritto nel database:", len(nomi), "nomi,", len(rows), "attributi")
    return 0


if __name__ == "__main__":
    sys.exit(main())
