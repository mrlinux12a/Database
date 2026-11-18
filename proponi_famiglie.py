# -*- coding: utf-8 -*-
"""Raggruppa gli articoli di un catalogo per nomeV2 identico: ogni gruppo e' una famiglia candidata.

  py -3.15 proponi_famiglie.py --catalogo "Air Control SRL" [--min 3]            elenca i gruppi
  py -3.15 proponi_famiglie.py --catalogo "Air Control SRL" --assegna            crea le famiglie e le assegna (solo agli articoli senza famiglia)

La famiglia vera la decide una persona: dopo --assegna si rinominano/uniscono con SQL o a mano
(es. update materiale set famiglia_id = <id buona> where famiglia_id = <id da unire>; delete from famiglia where id = <id da unire>).
"""
import argparse

from arricchisci import collega, CATALOGO_DEFAULT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogo", default=CATALOGO_DEFAULT)
    ap.add_argument("--min", type=int, default=3, help="minimo di articoli per proporre una famiglia")
    ap.add_argument("--assegna", action="store_true")
    a = ap.parse_args()
    conn = collega()
    cur = conn.cursor()
    cur.execute("""select nomev2, count(*) from materiale where catalogo = %s and nomev2 is not null
                   group by 1 having count(*) >= %s order by 2 desc, 1""", (a.catalogo, a.min))
    gruppi = cur.fetchall()
    cur.execute("select count(*) from materiale where catalogo = %s and nomev2 is not null", (a.catalogo,))
    totale = cur.fetchone()[0]
    print("%d gruppi con almeno %d articoli, %d articoli su %d" % (len(gruppi), a.min, sum(n for _, n in gruppi), totale))
    for nome, n in gruppi[:60]:
        print("  %5d  %s" % (n, nome))
    if a.assegna:
        for nome, _ in gruppi:
            cur.execute("insert into famiglia (nome) values (%s) on conflict (nome) do nothing", (nome,))
            cur.execute("""update materiale m set famiglia_id = f.id from famiglia f
                           where f.nome = %s and m.nomev2 = %s and m.catalogo = %s and m.famiglia_id is null""",
                        (nome, nome, a.catalogo))
        conn.commit()
        print("famiglie create/assegnate:", len(gruppi))


if __name__ == "__main__":
    main()
