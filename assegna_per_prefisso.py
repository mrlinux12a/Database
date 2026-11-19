# -*- coding: utf-8 -*-
"""Mette in una famiglia gli articoli rimasti SENZA famiglia il cui nomeV2 comincia (a parola intera) con il nome di una
famiglia gia' usata nello STESSO catalogo: "Comando elettrotermico con microinterruttore" -> famiglia "Comando elettrotermico",
"Plenum bocchetta PSF, L400, aperto" -> "Plenum". Il resto del nome e' una variante (attributo candidato), non un altro
prodotto. Se piu' famiglie vanno bene vince quella con il nome piu' lungo.

  py -3.15 assegna_per_prefisso.py --prova        elenca cosa farebbe
  py -3.15 assegna_per_prefisso.py                assegna
  py -3.15 assegna_per_prefisso.py --catalogo "Caleffi"

Va dopo  proponi_famiglie.py --assegna  e  unisci_famiglie.py  (anche dopo averli rifatti: e' ripetibile).
ESCLUSI (controllati a mano il 2026-11-18): articoli che cominciano come una famiglia ma sono un altro prodotto.
"""
import argparse
import collections
import re

from arricchisci import collega

# (catalogo, codice fornitore): perche' no
ESCLUSI = {
    ("Caleffi", "140002"): "Tee sdoppiatore per prese di pressione: non e' un raccordo a T (vedi famiglie_comuni)",
    ("Caleffi", "545300"): "Tee Dirtmag per lavaggio impianti: componente, non raccordo",
    ("Caleffi", "359001"): "Raccordo a tee: sarebbe un Tee, non la famiglia generica Raccordo",
    ("Caleffi", "151000"): "Termostato attuatore: non si sa se e' un termostato o un attuatore",
    ("Caleffi", "545900"): "Filtro defangatore magnetico: la famiglia Filtro e' di filtri per gas",
    ("Caleffi", "579000"): "Filtro defangatore Dirtmagclean: la famiglia Filtro e' di filtri per gas",
    ("Caleffi", "579001"): "Filtro defangatore Dirtmagclean: la famiglia Filtro e' di filtri per gas",
    ("Caleffi", "577105"): "Filtro ispezionabile Filterstop (acqua): la famiglia Filtro e' di filtri per gas",
    ("Caleffi", "577106"): "Filtro ispezionabile Filterstop (acqua): la famiglia Filtro e' di filtri per gas",
    ("Caleffi", "F49474/BL"): "Filtro pulizia: non si capisce che prodotto e'",
    ("Caleffi", "F49474/GR"): "Filtro mantenimento: non si capisce che prodotto e'",
    ("Caleffi", "559003"): "Pozzetto con inserto magnetico: non e' un pozzetto portasonda come gli altri",
}


def norm(s):
    s = s.lower()
    s = re.sub(r"[\"'’`]", " ", s)
    s = re.sub(r"(?<!\w)[-–+,;:./()]+(?!\w)", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogo", help="un solo catalogo (default: tutti)")
    ap.add_argument("--prova", action="store_true", help="non scrive nel database")
    a = ap.parse_args()
    conn = collega()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT m.catalogo, f.id, f.nome FROM materiale m JOIN famiglia f ON f.id = m.famiglia_id")
    famiglie = collections.defaultdict(dict)                 # catalogo -> nome normalizzato -> (id, nome)
    for cat, i, nome in cur.fetchall():
        famiglie[cat][norm(nome)] = (i, nome)
    cur.execute("SELECT codice, catalogo, cod_fornitore, nomev2 FROM materiale WHERE famiglia_id IS NULL AND nomev2 IS NOT NULL"
                + (" AND catalogo = %s" if a.catalogo else "") + " ORDER BY catalogo, nomev2", [a.catalogo] if a.catalogo else [])
    da_fare, esclusi = [], 0
    for codice, cat, cod, v2 in cur.fetchall():
        n = norm(v2)
        cand = [k for k in famiglie.get(cat, {}) if n.startswith(k + " ")]
        if not cand:
            continue
        if (cat, cod) in ESCLUSI:
            esclusi += 1
            continue
        i, nome = famiglie[cat][max(cand, key=len)]
        da_fare.append((codice, cat, cod, v2, i, nome))
    per_cat = collections.Counter(x[1] for x in da_fare)
    print("%d articoli senza famiglia da mettere in una famiglia del loro catalogo (%s), %d esclusi a mano"
          % (len(da_fare), ", ".join("%s %d" % kv for kv in sorted(per_cat.items())), esclusi))
    per_fam = collections.Counter((x[1], x[5]) for x in da_fare)
    for (cat, nome), k in sorted(per_fam.items(), key=lambda x: (-x[1], x[0])):
        print("  %4d  %-16s -> %s" % (k, cat, nome))
    if a.prova or not da_fare:
        return
    cur.executemany("UPDATE materiale SET famiglia_id = %s WHERE codice = %s AND famiglia_id IS NULL",
                    [(i, codice) for codice, _, _, _, i, _ in da_fare])
    conn.commit()
    print("fatto")


if __name__ == "__main__":
    main()
