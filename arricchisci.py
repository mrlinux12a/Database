# -*- coding: utf-8 -*-
"""Riempie nel database `nomev1`, `nomev2` e gli attributi degli articoli di UN catalogo.

  py -3.13 arricchisci.py                              -> catalogo "Air Control SRL", scrive nel database
  py -3.13 arricchisci.py --catalogo "Acme SRL"        -> un altro catalogo (colonna `catalogo` di materiale)
  py -3.13 arricchisci.py --catalogo "Acme SRL" --prova  -> calcola e mostra le statistiche, senza scrivere

Cosa fa
  * legge gli articoli di `materiale` di quel catalogo;
  * per ognuno chiama il modulo del catalogo (arricchimento/cataloghi/<nome>.py, oppure `generico`): nomev1 + attributi;
  * calcola nomev2 (nomev1 senza le informazioni che l'articolo ha gia' come attributo: arricchimento/v2.py);
  * riscrive le righe di `materiale_attributo` di quel catalogo (solo i valori trovati: niente NULL).
Si puo' rieseguire quando si vuole; va rieseguito dopo ogni import_catalogo.py (l'import cancella e ricrea le righe).
Connessione: PGHOST, PGUSER, PGPASSWORD, PGDATABASE (default localhost, postgres, nessuna password, db_serio_finale).
"""
import argparse
import collections
import os
import sys

import psycopg2
import psycopg2.extras

from arricchimento import attributi, cataloghi, comuni, v2

AQUI = os.path.dirname(os.path.abspath(__file__))
CATALOGO_DEFAULT = "Air Control SRL"


def collega():
    return psycopg2.connect(dbname=os.environ.get("PGDATABASE", os.environ.get("DB_NAME", "db_serio_finale")),
                            user=os.environ.get("PGUSER", os.environ.get("DB_USER", "postgres")),
                            host=os.environ.get("PGHOST", os.environ.get("DB_HOST", "localhost")),
                            password=os.environ.get("PGPASSWORD") or os.environ.get("DB_PASSWORD") or None)


def scrivi_dizionario(cur):
    """Riscrive la tabella `attributo` (elenco degli attributi) da arricchimento/attributi.py."""
    cur.executemany(
    """insert into attributo (chiave, etichetta, gruppo, nuovo, ordine, breve) values (%s,%s,%s,%s,%s,%s)
       on conflict (chiave) do update set etichetta = excluded.etichetta, gruppo = excluded.gruppo,
                                          nuovo = excluded.nuovo, ordine = excluded.ordine, breve = excluded.breve""",
    [(c, e, g, n, i, attributi.BREVE[c]) for i, (c, e, g, n) in enumerate(attributi.ATTRIBUTI, 1)])


def valido(chiave, v):
    """Un valore entra solo se ha chiave nota, testo non vuoto e origine ammessa."""
    return (chiave in attributi.CHIAVI and str(v.get("valore") or "").strip()
            and v.get("origine") in comuni.ORIGINI)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogo", default=CATALOGO_DEFAULT, help="nome del catalogo (colonna `catalogo`, = nome del CSV)")
    ap.add_argument("--prova", action="store_true", help="non scrive nel database")
    a = ap.parse_args()

    conn = collega()
    cur = conn.cursor()
    with open(os.path.join(AQUI, "schema.sql"), encoding="utf-8") as f:
        cur.execute(f.read())
    cur.execute("select codice, cod_fornitore, descrizione from materiale where catalogo = %s order by codice", (a.catalogo,))
    righe = cur.fetchall()
    if not righe:
        cur.execute("select catalogo, count(*) from materiale group by 1 order by 1")
        sys.exit("Nessun articolo per il catalogo %r. Cataloghi presenti: %s" % (a.catalogo, cur.fetchall()))
    modulo, nome_modulo = cataloghi.carica(a.catalogo)
    print("Catalogo %r: %d articoli, modulo %s" % (a.catalogo, len(righe), nome_modulo))
    if nome_modulo == "generico":
        print("  (nessun modulo specifico: uso le regole di base; per farne uno: copia arricchimento/cataloghi/_modello.py)")
    if hasattr(modulo, "prepara"):
        modulo.prepara([(r[1], r[2]) for r in righe])

    nomi, nomi2, attrs, errori, scartati = {}, {}, {}, 0, 0
    for codice, forn, descr in righe:
        try:
            nome, at = modulo.analizza(forn, descr)
        except Exception as e:                      # un articolo strano non deve fermare tutto
            errori += 1
            print("ERRORE", forn, repr(e), file=sys.stderr)
            continue
        buoni = {k: v for k, v in at.items() if valido(k, v)}
        scartati += len(at) - len(buoni)
        nomi[codice] = nome
        nomi2[codice] = v2.pulisci(nome, buoni)
        attrs[codice] = buoni

    conta = collections.Counter(k for at in attrs.values() for k in at)
    orig = collections.Counter((k, v["origine"]) for at in attrs.values() for k, v in at.items())
    print(f"{len(righe)} articoli, {len(nomi)} nomi, {sum(conta.values())} valori di attributo, "
          f"{errori} errori, {scartati} valori scartati (chiave/origine/testo non validi)")
    for chiave, etichetta, gruppo, nuovo in attributi.ATTRIBUTI:
        o = {k2: n for (k1, k2), n in orig.items() if k1 == chiave}
        print(f"  {chiave:<18} {conta.get(chiave, 0):5d}   {o if o else ''}")
    if a.prova:
        return 0

    cur.execute("delete from materiale_attributo where codice in (select codice from materiale where catalogo = %s)",
                (a.catalogo,))
    scrivi_dizionario(cur)
    psycopg2.extras.execute_values(
        cur, "update materiale m set nomev1 = v.n, nomev2 = v.n2 from (values %s) as v(c, n, n2) where m.codice = v.c",
        [(c, nomi[c], nomi2[c]) for c in nomi], page_size=1000)
    rows = [(codice, k, v["valore"], v.get("num"), v.get("unita"), v["origine"], v.get("fonte"))
            for codice, at in attrs.items() for k, v in at.items()]
    psycopg2.extras.execute_values(
        cur, """insert into materiale_attributo (codice, chiave, valore, valore_num, unita, origine, fonte) values %s""",
        rows, page_size=2000)
    conn.commit()
    print("scritto nel database:", len(nomi), "nomi,", len(rows), "attributi")
    return 0


if __name__ == "__main__":
    sys.exit(main())
