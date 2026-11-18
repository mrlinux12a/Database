# -*- coding: utf-8 -*-
"""Unisce le famiglie dei cataloghi che sono lo stesso tipo di prodotto (regole in arricchimento/famiglie_comuni.py).

  py -3.15 unisci_famiglie.py --prova                       cosa verrebbe unito, senza scrivere
  py -3.15 unisci_famiglie.py                               unisce (tutti i cataloghi presenti)
  py -3.15 unisci_famiglie.py --catalogo "Aquatechnik"      solo gli articoli di un catalogo

Cosa fa: per ogni articolo con nomeV2 che combacia con una regola mette `famiglia_id` della famiglia comune (la crea se serve,
con una nota); poi toglie le famiglie rimaste senza articoli e scrive nella nota della famiglia comune da quali famiglie dei
cataloghi e' nata. Gli articoli che non combaciano non cambiano. Si puo' ripetere: il secondo giro non cambia niente.
Va dopo  proponi_famiglie.py --assegna  (che crea le famiglie dai gruppi di nomeV2 uguale).
"""
import argparse
import collections
import re

from arricchisci import collega
from arricchimento.famiglie_comuni import COMUNI, famiglia_comune


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogo", help="un solo catalogo (default: tutti)")
    ap.add_argument("--prova", action="store_true", help="non scrive nel database")
    a = ap.parse_args()
    conn = collega()
    cur = conn.cursor()
    cur.execute("select m.codice, m.catalogo, m.nomev2, m.famiglia_id, f.nome from materiale m "
                "left join famiglia f on f.id = m.famiglia_id where m.nomev2 is not null"
                + (" and m.catalogo = %s" if a.catalogo else "") + " order by m.codice", [a.catalogo] if a.catalogo else [])
    righe = cur.fetchall()

    nuovo = {}                                           # codice -> nome famiglia comune
    prima = collections.defaultdict(collections.Counter)  # famiglia comune -> {(catalogo, famiglia di prima): articoli}
    for codice, cat, v2, fam_id, fam_nome in righe:
        comune = famiglia_comune(v2)
        if comune and comune != fam_nome:
            nuovo[codice] = comune
        if comune:
            prima[comune][(cat, fam_nome)] += 1

    print("%d articoli con nomeV2 guardati, %d da spostare in una famiglia comune" % (len(righe), len(nuovo)))
    for nome, _ in COMUNI:
        n_cat = collections.Counter()
        vecchie = set()
        for (cat, fam), n in prima[nome].items():
            n_cat[cat] += n
            if fam and fam != nome:
                vecchie.add((cat, fam))
        if n_cat:
            print("  %-16s %s   (famiglie dei cataloghi assorbite: %d)"
                  % (nome, ", ".join("%s %d" % (c, n) for c, n in sorted(n_cat.items())), len(vecchie)))
    if a.prova or not nuovo:
        return

    ids = {}
    for nome, _ in COMUNI:
        cur.execute("insert into famiglia (nome) values (%s) on conflict (nome) do update set nome = excluded.nome returning id", (nome,))
        ids[nome] = cur.fetchone()[0]
    for codice, nome in nuovo.items():
        cur.execute("update materiale set famiglia_id = %s where codice = %s", (ids[nome], codice))
    # famiglie dei cataloghi rimaste vuote: via
    cur.execute("delete from famiglia f where not exists (select 1 from materiale m where m.famiglia_id = f.id)")
    print("famiglie vuote tolte:", cur.rowcount)
    for nome, _ in COMUNI:                                # nota: da dove nasce (si somma a quello che c'era: i giri successivi non la perdono)
        cur.execute("select note from famiglia where id = %s", (ids[nome],))
        prec = re.search(r"Nata dall'unione di: (.*)\.$", cur.fetchone()[0] or "")
        vecchie = sorted({f for (_c, f) in prima[nome] if f and f != nome} | set(prec.group(1).split("; ") if prec else []))
        cur.execute("select distinct catalogo from materiale where famiglia_id = %s order by 1", (ids[nome],))
        cat = [r[0] for r in cur.fetchall()]
        nota = ("Famiglia comune ai cataloghi (arricchimento/famiglie_comuni.py). Cataloghi: " + ", ".join(cat) + "."
                + (" Nata dall'unione di: " + "; ".join(vecchie) + "." if vecchie else ""))
        cur.execute("update famiglia set note = %s where id = %s", (nota, ids[nome]))
    conn.commit()
    print("fatto")


if __name__ == "__main__":
    main()
