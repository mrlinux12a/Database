# -*- coding: utf-8 -*-
"""Cerca nel nomeV2 di un catalogo i pezzi di testo che si ripetono su molti articoli: sono candidati a diventare un attributo
(e quindi a sparire dal nome, dando il nomeV3). Li scrive in `attributo_candidato` con stato 'proposto'; li approva una persona.

  py -3.15 proponi_attributi.py --catalogo "Air Control SRL" [--min 5] [--parole]

Di default guarda i pezzi separati da virgola (nomeV1 "a virgole", come Air Control). Con --parole guarda invece le parole e
le coppie di parole dopo la prima (per i cataloghi i cui nomi non hanno virgole, come Aquatechnik).
"""
import argparse
import collections

import psycopg2.extras

from arricchisci import collega, CATALOGO_DEFAULT


VUOTE = {"a", "e", "di", "da", "in", "per", "con", "il", "la", "le", "del"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogo", default=CATALOGO_DEFAULT)
    ap.add_argument("--min", type=int, default=5, help="minimo di articoli in cui il testo deve comparire")
    ap.add_argument("--parole", action="store_true", help="parole e coppie di parole invece dei pezzi tra virgole")
    a = ap.parse_args()
    conn = collega()
    cur = conn.cursor()
    cur.execute("select cod_fornitore, nomev2 from materiale where catalogo = %s and nomev2 is not null", (a.catalogo,))
    conta, esempio = collections.Counter(), {}
    per_nome = collections.defaultdict(collections.Counter)         # testo -> {nome base: articoli}   (solo --parole)
    totale_nome = collections.Counter()                              # nome base -> articoli
    for cod, n2 in cur.fetchall():
        if a.parole:
            tutte = n2.lower().split()
            base, parole = tutte[0], tutte[1:]                       # la prima parola e' il nome base
            totale_nome[base] += 1
            segmenti = {p for p in parole if len(p) > 2 and not p.isdigit() and p not in VUOTE}
            segmenti |= {" ".join(parole[i:i + 2]) for i in range(len(parole) - 1)
                         if parole[i] not in VUOTE and parole[i + 1] not in VUOTE}
            for seg in segmenti:
                per_nome[seg][base] += 1
        else:
            segmenti = {s.strip().lower() for s in n2.split(",")[1:] if s.strip()}  # il primo pezzo e' il nome base
        for seg in segmenti:
            conta[seg] += 1
            esempio.setdefault(seg, cod)
    trovati = [(t, n) for t, n in conta.most_common() if n >= a.min]
    if a.parole:
        # Un candidato utile DISTINGUE articoli dello stesso nome base (compare in alcuni "Tee" e in altri no): se compare in
        # tutti gli articoli del nome base, o in uno solo, non serve a cercare. E una coppia che compare esattamente dove
        # compare una sua parola e' ridondante: resta la parola.
        def varia(t):
            return [(b, n) for b, n in per_nome[t].items() if n >= 2 and n < totale_nome[b]]
        trovati = [(t, n) for t, n in trovati if varia(t)]
        parole_tenute = {t: n for t, n in trovati if " " not in t}
        trovati = [(t, n) for t, n in trovati
                   if " " not in t or not any(conta[p] == n for p in t.split() if p in parole_tenute)]
        dove = {t: max(varia(t), key=lambda bn: bn[1]) for t, _ in trovati}
    if a.parole:                                  # toglie i vecchi candidati non piu' validi (solo quelli ancora 'proposto')
        cur.execute("delete from attributo_candidato where catalogo = %s and stato = 'proposto' and testo <> all(%s)",
                    (a.catalogo, [t for t, _ in trovati]))
        print("rimossi %d candidati vecchi non piu' validi" % cur.rowcount)
    if trovati:
        psycopg2.extras.execute_values(
            cur, """insert into attributo_candidato (catalogo, testo, esempio_codice, n) values %s
                    on conflict (catalogo, testo) do update set n = excluded.n, esempio_codice = excluded.esempio_codice""",
            [(a.catalogo, t, esempio[t], n) for t, n in trovati])
    conn.commit()
    print("%d candidati (testo in almeno %d articoli) scritti in attributo_candidato:" % (len(trovati), a.min))
    for t, n in trovati[:40]:
        extra = "  [varia dentro «%s»: %d su %d]" % (dove[t][0], dove[t][1], totale_nome[dove[t][0]]) if a.parole else ""
        print("  %5d  %s   (es. %s)%s" % (n, t, esempio[t], extra))


if __name__ == "__main__":
    main()
