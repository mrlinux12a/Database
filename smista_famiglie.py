# -*- coding: utf-8 -*-
"""Smistamento delle famiglie di un catalogo NUOVO in tre gruppi, prima di scrivere (non scrive niente nel database).

  py -3.15 smista_famiglie.py --catalogo "Watts"                  elenco per gruppi
  py -3.15 smista_famiglie.py --catalogo "Watts" --file x.tsv     anche in un file (gruppo, articoli, nomeV2, destinazione, nota)

Per ogni nomeV2 del catalogo (gli articoli con lo stesso nomeV2 vanno insieme):
  A  TIPO ESISTENTE: una regola di arricchimento/famiglie_comuni.py lo mette in un tipo che c'e' gia' con articoli di altri
     cataloghi (sicuro; «giallo» se la regola e' INCERTO, «anche» se ANCHE). Si scrive con unisci_famiglie.py.
  A? PROPOSTA PER PREFISSO: il nomeV2 comincia (a parola intera) con il nome di una famiglia di un ALTRO catalogo. Da
     confermare a mano (falsi amici: Bocchetta/Bocchettone, Filtro gas/acqua, Collare…): se va bene si aggiunge una regola.
  B  FAMIGLIA ESISTENTE, TIPO NUOVO: la prima parola e' quella di una famiglia/categoria che c'e' gia' (Valvola, Gruppo,
     Termometro…) ma nessun tipo combacia: si crea un tipo abbastanza specifico («Valvola di sovrapressione») con una regola
     in famiglie_comuni.py, da unire poi con gli altri tipi della categoria.
  C  FAMIGLIA NUOVA: niente di simile negli altri cataloghi: proponi_famiglie.py --assegna come sempre, poi i tipi.
Una regola gia' scritta per questo catalogo che crea un tipo che non esiste negli altri cataloghi conta come B o C
(«tipo nuovo da regola»), non come A.
Ordine di lavoro: smista_famiglie.py -> regole in famiglie_comuni.py -> segna_nuove.py --inizio -> proponi_famiglie.py
--assegna -> unisci_famiglie.py -> assegna_per_prefisso.py -> segna_nuove.py (segnetto rosso sulle famiglie nuove).
"""
import argparse
import collections
import re

from arricchisci import collega
from arricchimento.famiglie_comuni import classifica


def norm(s):
    s = s.lower()
    s = re.sub(r"[\"'’`]", " ", s)
    s = re.sub(r"(?<!\w)[-–+,;:./()]+(?!\w)", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def prima_parola(s):
    return norm(s).split(" ")[0] if s.strip() else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogo", required=True)
    ap.add_argument("--file", help="scrive anche un file TSV")
    a = ap.parse_args()
    cur = collega().cursor()
    # famiglie degli ALTRI cataloghi (con almeno un articolo che non e' di questo catalogo)
    cur.execute("SELECT f.nome, count(*) FROM famiglia f JOIN materiale m ON m.famiglia_id = f.id "
                "WHERE m.catalogo <> %s GROUP BY 1", (a.catalogo,))
    altre = dict(cur.fetchall())
    per_norm = {norm(n): n for n in altre}
    parole = collections.Counter(prima_parola(n) for n in altre)
    cur.execute("SELECT nomev2, min(nomev1), count(*) FROM materiale WHERE catalogo = %s AND nomev2 IS NOT NULL "
                "GROUP BY 1 ORDER BY 1", (a.catalogo,))
    gruppi = collections.defaultdict(list)          # gruppo -> [(n, nomeV2, destinazione, nota)]
    for v2, v1, n in cur.fetchall():
        c = classifica(v2, v1)
        if c and c[0] in altre:
            comune, incerto, anche = c
            nota = ("anche in " + ", ".join(anche)) if anche else ("giallo: il piu' vicino" if incerto else "")
            gruppi["A"].append((n, v2, comune, nota))
            continue
        k = norm(v2)
        cand = [p for p in per_norm if k == p or k.startswith(p + " ")]
        if c:                                         # regola gia' scritta, ma il tipo non c'e' negli altri cataloghi
            dest, nota = c[0], "tipo nuovo da regola"
            gruppi["B" if prima_parola(c[0]) in parole else "C"].append((n, v2, dest, nota))
        elif cand:
            p = max(cand, key=len)
            gruppi["A?"].append((n, v2, per_norm[p], "per prefisso: da confermare"))
        elif prima_parola(v2) in parole:
            w = prima_parola(v2)
            gruppi["B"].append((n, v2, w.capitalize() + " …", "%d famiglie «%s» negli altri cataloghi" % (parole[w], w)))
        else:
            gruppi["C"].append((n, v2, "", ""))
    titoli = {"A": "A  tipo esistente (regola)", "A?": "A? proposta per prefisso (da confermare)",
              "B": "B  famiglia esistente, tipo nuovo", "C": "C  famiglia nuova"}
    tot = sum(n for g in gruppi.values() for n, *_ in g)
    print("%s: %d articoli, %d nomeV2" % (a.catalogo, tot, sum(len(g) for g in gruppi.values())))
    righe = []
    for g in ("A", "A?", "B", "C"):
        lista = sorted(gruppi[g], key=lambda x: (x[2], -x[0], x[1]))
        print("\n%s: %d articoli, %d nomeV2" % (titoli[g], sum(x[0] for x in lista), len(lista)))
        for n, v2, dest, nota in lista:
            print("  %4d  %-62s -> %-38s %s" % (n, v2[:62], dest[:38], nota))
            righe.append("\t".join([g, str(n), v2, dest, nota]))
    if a.file:
        with open(a.file, "w", encoding="utf-8") as f:
            f.write("gruppo\tarticoli\tnomev2\tdestinazione\tnota\n" + "\n".join(righe) + "\n")
        print("\nscritto", a.file)


if __name__ == "__main__":
    main()
