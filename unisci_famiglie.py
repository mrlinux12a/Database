# -*- coding: utf-8 -*-
"""Unisce le famiglie dei cataloghi che sono lo stesso tipo di prodotto (regole in arricchimento/famiglie_comuni.py).

  py -3.15 unisci_famiglie.py --prova                       cosa verrebbe unito, senza scrivere
  py -3.15 unisci_famiglie.py                               unisce (tutti i cataloghi presenti)
  py -3.15 unisci_famiglie.py --catalogo "Aquatechnik"      solo gli articoli di un catalogo
  py -3.15 unisci_famiglie.py --prova --dubbi               elenca anche gli articoli incerti / in piu' tipi

Cosa fa: per ogni articolo con nomeV2 che combacia con una regola mette `famiglia_id` della famiglia comune (la crea se serve,
con una nota); riscrive la tabella tipo_incerto (articoli messi nel tipo piu' vicino senza esserne sicuri, e articoli che stanno
ANCHE in un altro tipo); poi toglie le famiglie rimaste senza articoli e scrive nella nota della famiglia comune da quali
famiglie dei cataloghi e' nata. Gli articoli che non combaciano non cambiano. Si puo' ripetere: il secondo giro non cambia niente.
Va dopo  proponi_famiglie.py --assegna  (che crea le famiglie dai gruppi di nomeV2 uguale).
"""
import argparse
import collections
import re

from arricchisci import collega
from arricchimento.famiglie_comuni import TIPI, classifica

TABELLA = """CREATE TABLE IF NOT EXISTS tipo_incerto (
    codice      text    NOT NULL REFERENCES materiale(codice) ON DELETE CASCADE,
    famiglia_id integer NOT NULL REFERENCES famiglia(id) ON DELETE CASCADE,
    principale  boolean NOT NULL,
    PRIMARY KEY (codice, famiglia_id));
CREATE INDEX IF NOT EXISTS tipo_incerto_famiglia_idx ON tipo_incerto (famiglia_id);"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogo", help="un solo catalogo (default: tutti)")
    ap.add_argument("--prova", action="store_true", help="non scrive nel database")
    ap.add_argument("--dubbi", action="store_true", help="elenca gli articoli incerti o messi in piu' tipi")
    a = ap.parse_args()
    conn = collega()
    cur = conn.cursor()
    cur.execute("select m.codice, m.catalogo, m.nomev2, m.famiglia_id, f.nome, m.nomev1 from materiale m "
                "left join famiglia f on f.id = m.famiglia_id where m.nomev2 is not null"
                + (" and m.catalogo = %s" if a.catalogo else "") + " order by m.codice", [a.catalogo] if a.catalogo else [])
    righe = cur.fetchall()

    nuovo = {}                                           # codice -> nome famiglia comune
    prima = collections.defaultdict(collections.Counter)  # famiglia comune -> {(catalogo, famiglia di prima): articoli}
    dubbi = []                                           # (codice, tipo, principale)
    esempi = collections.defaultdict(collections.Counter)  # tipo -> {(nomeV2, nota): articoli} per --dubbi
    for codice, cat, v2, fam_id, fam_nome, v1 in righe:
        c = classifica(v2, v1)
        if not c:
            continue
        comune, incerto, anche = c
        if comune != fam_nome:
            nuovo[codice] = comune
        prima[comune][(cat, fam_nome)] += 1
        if incerto:
            dubbi.append((codice, comune, True))
            esempi[comune][(v2, "anche in " + ", ".join(anche) if anche else "piu' vicino")] += 1
        for altro in anche:
            dubbi.append((codice, altro, False))
            esempi[altro][(v2, "anche (principale: %s)" % comune)] += 1

    print("%d articoli con nomeV2 guardati, %d da spostare in una famiglia comune, %d incerti, %d messi anche in un altro tipo"
          % (len(righe), len(nuovo), sum(1 for d in dubbi if d[2]), sum(1 for d in dubbi if not d[2])))
    for nome in TIPI:
        n_cat = collections.Counter()
        vecchie = set()
        for (cat, fam), n in prima[nome].items():
            n_cat[cat] += n
            if fam and fam != nome:
                vecchie.add((cat, fam))
        n_dubbi = sum(esempi[nome].values())
        if n_cat or n_dubbi:
            print("  %-45s %s   (famiglie assorbite: %d%s)"
                  % (nome, ", ".join("%s %d" % (c, n) for c, n in sorted(n_cat.items())), len(vecchie),
                     ", in giallo: %d" % n_dubbi if n_dubbi else ""))
            if a.dubbi:
                for (v2, nota), n in sorted(esempi[nome].items()):
                    print("        ? %3d  %-60s %s" % (n, v2[:60], nota))
    if a.prova:
        return

    cur.execute(TABELLA)
    ids = {}
    for nome in TIPI:
        cur.execute("insert into famiglia (nome) values (%s) on conflict (nome) do update set nome = excluded.nome returning id", (nome,))
        ids[nome] = cur.fetchone()[0]
    for codice, nome in nuovo.items():
        cur.execute("update materiale set famiglia_id = %s where codice = %s", (ids[nome], codice))
    # tipi incerti / doppi: si rifanno da capo (per il catalogo scelto, o per tutti)
    cur.execute("delete from tipo_incerto" + (" where codice in (select codice from materiale where catalogo = %s)" if a.catalogo else ""),
                [a.catalogo] if a.catalogo else [])
    for codice, nome, principale in dubbi:
        cur.execute("insert into tipo_incerto (codice, famiglia_id, principale) values (%s, %s, %s) on conflict do nothing",
                    (codice, ids[nome], principale))
    # famiglie rimaste vuote (nessun articolo, nemmeno «anche»): via
    cur.execute("delete from famiglia f where not exists (select 1 from materiale m where m.famiglia_id = f.id) "
                "and not exists (select 1 from tipo_incerto t where t.famiglia_id = f.id)")
    print("famiglie vuote tolte:", cur.rowcount)
    for nome in TIPI:                                     # nota: da dove nasce (si somma a quello che c'era: i giri successivi non la perdono)
        cur.execute("select note from famiglia where id = %s", (ids[nome],))
        riga = cur.fetchone()
        if not riga:
            continue
        prec = re.search(r"Nata dall'unione di: (.*)\.$", riga[0] or "")
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
