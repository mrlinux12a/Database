# -*- coding: utf-8 -*-
"""Importa nel database il file prodotto da esporta.py (lavoro di un'altra persona su un catalogo).
Gli articoli devono GIA' esistere in `materiale` (stesso CSV importato con import_catalogo.py): si aggiornano nomeV1, nomeV2,
famiglia e attributi; non si crea ne' si cancella nessun articolo.

  py -3.13 importa_risultati.py esportazioni/acme_srl.json.gz [--prova] [--ignora-mancanti]
"""
import argparse
import gzip
import json
import os
import sys

import psycopg2.extras

from arricchimento import attributi, comuni
from arricchisci import collega, scrivi_dizionario

AQUI = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--prova", action="store_true", help="controlla soltanto, non scrive")
    ap.add_argument("--ignora-mancanti", action="store_true", help="salta gli articoli che non sono nel database")
    a = ap.parse_args()
    apri = gzip.open if a.file.endswith(".gz") else open
    with apri(a.file, "rt", encoding="utf-8") as f:
        d = json.load(f)
    if d.get("versione") != 1:
        sys.exit("Formato del file non riconosciuto (versione %r)" % d.get("versione"))
    conn = collega()
    cur = conn.cursor()
    with open(os.path.join(AQUI, "schema.sql"), encoding="utf-8") as f:
        cur.execute(f.read())
    cur.execute("select codice, cod_fornitore from materiale where catalogo = %s", (d["catalogo"],))
    nel_db = dict(cur.fetchall())

    ok, mancanti, diversi, righe_attr, errori = [], [], [], [], []
    for art in d["articoli"]:
        c = art["codice"]
        if c not in nel_db:
            mancanti.append(c)
        elif nel_db[c] != art["cod_fornitore"]:
            diversi.append(c)
        else:
            ok.append(art)
            for k, valore, num, unita, orig, fonte in art["attributi"]:
                if k not in attributi.CHIAVI or not str(valore).strip() or orig not in comuni.ORIGINI:
                    errori.append((c, k, orig))
                else:
                    righe_attr.append((c, k, valore, num, unita, orig, fonte))
    print("File: catalogo %r, %d articoli (creato %s)" % (d["catalogo"], len(d["articoli"]), d.get("creato")))
    print("  nel database: %d | mancanti: %d | codice fornitore diverso: %d | attributi non validi: %d"
          % (len(ok), len(mancanti), len(diversi), len(errori)))
    if diversi or errori or (mancanti and not a.ignora_mancanti):
        for nome, lista in (("mancanti", mancanti), ("codice fornitore diverso", diversi), ("non validi", errori)):
            if lista:
                print("  %s (primi 10): %s" % (nome, lista[:10]))
        sys.exit("Niente importato: correggere il file o il database (per saltare i mancanti: --ignora-mancanti).")
    if a.prova:
        print("Prova riuscita: nessuna modifica fatta.")
        return 0

    scrivi_dizionario(cur)
    codici = [art["codice"] for art in ok]
    cur.execute("delete from materiale_attributo where codice = any(%s)", (codici,))
    psycopg2.extras.execute_values(
        cur, "update materiale m set nomev1 = v.n1, nomev2 = v.n2 from (values %s) as v(c, n1, n2) where m.codice = v.c",
        [(x["codice"], x["nomev1"], x["nomev2"]) for x in ok], page_size=1000)
    for nome in sorted({x["famiglia"] for x in ok if x.get("famiglia")}):
        cur.execute("insert into famiglia (nome) values (%s) on conflict (nome) do nothing", (nome,))
    con_famiglia = [(x["codice"], x["famiglia"]) for x in ok if x.get("famiglia")]
    if con_famiglia:
        psycopg2.extras.execute_values(
            cur, """update materiale m set famiglia_id = f.id from famiglia f, (values %s) as v(c, fam)
                    where m.codice = v.c and f.nome = v.fam""", con_famiglia, page_size=1000)
    if righe_attr:
        psycopg2.extras.execute_values(
            cur, "insert into materiale_attributo (codice, chiave, valore, valore_num, unita, origine, fonte) values %s",
            righe_attr, page_size=2000)
    if d.get("attributi_candidato"):
        psycopg2.extras.execute_values(
            cur, """insert into attributo_candidato (catalogo, testo, esempio_codice, n, stato, note) values %s
                    on conflict (catalogo, testo) do update set n = excluded.n, esempio_codice = excluded.esempio_codice""",
            [(d["catalogo"], *c) for c in d["attributi_candidato"]])
    conn.commit()
    print("Importati %d articoli e %d attributi." % (len(ok), len(righe_attr)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
