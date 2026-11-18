# -*- coding: utf-8 -*-
"""Controllo di regressione: ricalcola nomeV1, nomeV2 e attributi con il codice di adesso e li confronta con quelli salvati
nel database, SENZA scrivere niente. Si usa PRIMA e DOPO ogni modifica ai file condivisi (arricchimento/v2.py, comuni.py,
parse.py, generico.py, arricchisci.py) per sapere se i cataloghi gia' consegnati cambierebbero.

  py -3.15 controlla_regressione.py                       tutti i cataloghi presenti nel database
  py -3.15 controlla_regressione.py --catalogo "Air Control SRL" [--mostra 20]

Uscita 0 = nessuna differenza; 1 = almeno una differenza (le prime `--mostra` sono stampate).
"""
import argparse
import sys

from arricchisci import collega, cataloghi, v2, attributi, comuni


def controlla(cur, catalogo, mostra):
    cur.execute("select codice, cod_fornitore, descrizione, nomev1, nomev2, " + ", ".join(cataloghi.COLONNE_RIGA) +
                " from materiale where catalogo = %s order by codice", (catalogo,))
    righe = cur.fetchall()
    cur.execute("select x.codice, x.chiave, x.valore from materiale_attributo x join materiale m on m.codice = x.codice "
                "where m.catalogo = %s", (catalogo,))
    salvati = {}
    for codice, chiave, valore in cur.fetchall():
        salvati.setdefault(codice, {})[chiave] = valore
    modulo, nome_modulo = cataloghi.carica(catalogo)
    if hasattr(modulo, "prepara"):
        modulo.prepara([(r[1], r[2]) for r in righe])
    diff_nomi = diff_v2 = diff_attr = 0
    stampate = 0
    for codice, forn, descr, v1db, v2db, *colonne in righe:
        nome, at = cataloghi.analizza(modulo, forn, descr, dict(zip(cataloghi.COLONNE_RIGA, colonne)))
        n2 = v2.pulisci(nome, at)
        nuovi = {k: v["valore"] for k, v in at.items() if attributi.CHIAVI.count(k) and str(v.get("valore") or "").strip()
                 and v.get("origine") in comuni.ORIGINI}
        c1, c2, c3 = nome != v1db, n2 != v2db, nuovi != salvati.get(codice, {})
        diff_nomi += c1
        diff_v2 += c2
        diff_attr += c3
        if (c1 or c2 or c3) and stampate < mostra:
            stampate += 1
            print("  %s" % forn)
            if c1:
                print("     nomeV1  DB : %s\n             NEW: %s" % (v1db, nome))
            if c2:
                print("     nomeV2  DB : %s\n             NEW: %s" % (v2db, n2))
            if c3:
                vecchi = salvati.get(codice, {})
                for k in sorted(set(vecchi) | set(nuovi)):
                    if vecchi.get(k) != nuovi.get(k):
                        print("     attr %-12s DB: %r  NEW: %r" % (k, vecchi.get(k), nuovi.get(k)))
    print("%-24s modulo %-18s %5d articoli: nomeV1 diversi %d, nomeV2 diversi %d, attributi diversi %d"
          % (catalogo, nome_modulo, len(righe), diff_nomi, diff_v2, diff_attr))
    return diff_nomi + diff_v2 + diff_attr


def main():
    sys.stdout.reconfigure(errors="replace")
    ap = argparse.ArgumentParser(description="Confronta i risultati salvati con quelli ricalcolati dal codice attuale")
    ap.add_argument("--catalogo", help="un solo catalogo (default: tutti)")
    ap.add_argument("--mostra", type=int, default=10, help="quante differenze stampare per catalogo")
    a = ap.parse_args()
    conn = collega()
    cur = conn.cursor()
    if a.catalogo:
        nomi = [a.catalogo]
    else:
        cur.execute("select distinct catalogo from materiale order by 1")
        nomi = [r[0] for r in cur.fetchall()]
    totale = sum(controlla(cur, n, a.mostra) for n in nomi)
    print("Nessuna differenza." if not totale else "Ci sono differenze: controlla che siano volute prima di rilanciare arricchisci.py.")
    sys.exit(1 if totale else 0)


if __name__ == "__main__":
    main()
