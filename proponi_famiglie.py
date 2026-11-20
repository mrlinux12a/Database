# -*- coding: utf-8 -*-
"""Raggruppa gli articoli di un catalogo per nomeV2 identico: ogni gruppo e' una famiglia candidata.

  py -3.15 proponi_famiglie.py --catalogo "Air Control SRL" [--min 3]            elenca i gruppi
  py -3.15 proponi_famiglie.py --catalogo "Air Control SRL" --assegna            crea le famiglie e le assegna (solo agli articoli senza famiglia)
  py -3.15 proponi_famiglie.py --catalogo "Air Control SRL" --prefisso [--salva]
  py -3.15 proponi_famiglie.py --approva "Attuatore" [--catalogo "Air Control SRL"]
        ULTIMO PASSO (dopo unisci_famiglie.py e assegna_per_prefisso.py): gli articoli rimasti SENZA famiglia che hanno un
        nomeV2 unico (il modello o una variante resta nel nome: «Attuatore LF24-SR», «Attuatore SM24A, on-off/3 punti») si
        raggruppano per le PRIME PAROLE del nomeV2 (fino al primo numero, Ø o sigla in maiuscolo), se almeno --min articoli
        le hanno in comune. Prima una parola sola («Bicchieratrice»: a batteria e manuale sono varianti, non famiglie), ma non
        se la parola e' generica (Kit, Ricambio, Coppia, Gruppo...) o e' gia' una categoria (prima parola di 2+ famiglie:
        Valvola, Raccordo, Cassetta...): allora due parole («Comando master», «Cassetta d'ispezione»). Un nome che e' gia'
        una famiglia di un ALTRO catalogo («Attuatore», «Dima») non si assegna: e' segnato «da confermare» (falsi amici: la
        dima per curvatubi non e' la dima per satelliti); se va bene si scrive una regola in famiglie_comuni.py.
        Con --salva i gruppi NON diventano famiglie: si scrivono come PROPOSTE nella tabella famiglia_proposta (si rifanno da
        capo per il catalogo) e gli articoli restano «Senza famiglia». La pagina web le mostra nella sezione «Famiglie da
        approvare» (niente barretta rossa: il rosso e' solo per famiglie e tipi nuovi non ancora raggruppati). Una persona le
        approva con --approva "Nome" (crea la famiglia, o usa quella che c'e' gia' con quel nome, e ci mette gli articoli
        della proposta; con --catalogo solo quelli di quel catalogo). Le proposte non vanno nell'esportazione: dopo
        importa_risultati.py si rilancia --prefisso --salva.

La famiglia vera la decide una persona: dopo --assegna si rinominano/uniscono con SQL o a mano
(es. update materiale set famiglia_id = <id buona> where famiglia_id = <id da unire>; delete from famiglia where id = <id da unire>).
"""
import argparse
import collections
import re

from arricchisci import collega, CATALOGO_DEFAULT

GENERICHE = {"kit", "ricambio", "ricambi", "coppia", "gruppo", "set", "modulo", "confezione", "corpo", "serie", "comando",
             "dispositivo", "elemento", "accessorio", "accessori", "nuovo", "nuova", "mini", "doppio", "doppia",
             "fires"}                                     # Fires = linea di Aquatechnik, non un tipo di prodotto
VUOTE = {"di", "per", "con", "a", "da", "in", "e", "del", "della", "dei", "su", "ad", "senza", "+", "-", "–", "/"}
TABELLA = """CREATE TABLE IF NOT EXISTS famiglia_proposta (
    codice text NOT NULL PRIMARY KEY REFERENCES materiale(codice) ON DELETE CASCADE,
    nome   text NOT NULL,           -- nome della famiglia proposta (l'articolo resta senza famiglia finche' non si approva)
    nota   text,                    -- perche' e' da confermare (es. stesso nome di una famiglia di un altro catalogo)
    data   date NOT NULL DEFAULT current_date);
CREATE INDEX IF NOT EXISTS famiglia_proposta_nome_idx ON famiglia_proposta (nome);"""


def norm(s):
    s = s.lower()
    s = re.sub(r"[\"'’`]", " ", s)
    s = re.sub(r"(?<!\w)[-–+,;:./()]+(?!\w)", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def parole(v2):
    """Le parole iniziali del nomeV2 (testo originale) fino al primo numero, Ø, sigla in maiuscolo o segno."""
    out = []
    for t in re.findall(r"[^\s,;:()]+", v2):
        if re.search(r"\d|Ø", t) or (len(t) >= 2 and t.isupper() and out) or not re.search(r"[^\W\d_]", t):
            break
        out.append(t)
    return out


def chiave(ps, k):
    """Le prime k parole che contano (una preposizione si porta dietro la parola dopo: «Placca di copertura»)."""
    out, n = [], 0
    for i, t in enumerate(ps):
        out.append(t)
        if t.lower() not in VUOTE:
            n += 1
        if n == k:
            return out if i + 1 == len(out) else None
    return None


def per_prefisso(cur, catalogo, minimo):
    """-> (gruppi da assegnare [(nome, [codici], esempi)], gruppi da confermare [(nome, [codici], esempi, motivo)])"""
    from assegna_per_prefisso import ESCLUSI
    cur.execute("SELECT f.nome, array_agg(DISTINCT m.catalogo) FROM famiglia f JOIN materiale m ON m.famiglia_id = f.id GROUP BY 1")
    famiglie = {norm(n): (n, set(c)) for n, c in cur.fetchall()}
    categorie = collections.Counter(k.split(" ")[0] for k in famiglie)
    cur.execute("SELECT codice, cod_fornitore, nomev2 FROM materiale WHERE catalogo = %s AND famiglia_id IS NULL "
                "AND nomev2 IS NOT NULL ORDER BY nomev2", (catalogo,))
    righe = [(c, v2, parole(v2)) for c, cod, v2 in cur.fetchall() if (catalogo, cod) not in ESCLUSI]
    presi, buoni, dubbi = set(), [], []
    for k in (1, 2):
        gruppi = collections.defaultdict(list)
        for codice, v2, ps in righe:
            if codice in presi or not ps:
                continue
            ch = chiave(ps, k)
            if not ch:
                continue
            parole_ch = [t.lower() for t in ch]
            if parole_ch[0] in GENERICHE or (k == 1 and categorie[norm(parole_ch[0])] >= 2):
                continue
            if k == 2 and any(t in GENERICHE for t in parole_ch[1:]):
                continue
            gruppi[" ".join(parole_ch)].append((codice, v2, ch))
        for _k, membri in sorted(gruppi.items()):
            if len(membri) < minimo:
                continue
            nome = " ".join(membri[0][2])
            nome = nome[:1].upper() + nome[1:]
            codici = [m[0] for m in membri]
            esempi = sorted({m[1] for m in membri})[:3]
            presi.update(codici)
            gia = famiglie.get(norm(nome))
            if gia and catalogo not in gia[1]:
                dubbi.append((gia[0], codici, esempi, "e' gia' una famiglia di " + ", ".join(sorted(gia[1]))))
            elif gia:
                dubbi.append((gia[0], codici, esempi, "famiglia del catalogo: vedi assegna_per_prefisso.py (ESCLUSI?)"))
            else:
                buoni.append((nome, codici, esempi))
    return buoni, dubbi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogo")
    ap.add_argument("--min", type=int, default=3, help="minimo di articoli per proporre una famiglia")
    ap.add_argument("--assegna", action="store_true")
    ap.add_argument("--prefisso", action="store_true", help="raggruppa per prime parole gli articoli rimasti senza famiglia")
    ap.add_argument("--salva", action="store_true", help="con --prefisso: scrive i gruppi come famiglie DA APPROVARE")
    ap.add_argument("--approva", metavar="NOME", help="una famiglia da approvare diventa una famiglia vera")
    a = ap.parse_args()
    conn = collega()
    cur = conn.cursor()
    if a.approva:
        cur.execute("SELECT to_regclass('famiglia_proposta') IS NOT NULL")
        if not cur.fetchone()[0]:
            raise SystemExit("Nessuna famiglia da approvare (manca la tabella famiglia_proposta).")
        cur.execute("SELECT p.codice FROM famiglia_proposta p JOIN materiale m ON m.codice = p.codice WHERE p.nome = %s "
                    "AND m.famiglia_id IS NULL" + (" AND m.catalogo = %s" if a.catalogo else ""),
                    [a.approva] + ([a.catalogo] if a.catalogo else []))
        codici = [r[0] for r in cur.fetchall()]
        if not codici:
            raise SystemExit("Nessun articolo senza famiglia nella proposta «%s»%s." % (a.approva, " di " + a.catalogo if a.catalogo else ""))
        cur.execute("insert into famiglia (nome) values (%s) on conflict (nome) do update set nome = excluded.nome returning id",
                    (a.approva,))
        fid = cur.fetchone()[0]
        cur.execute("update materiale set famiglia_id = %s where codice = any(%s) and famiglia_id is null", (fid, codici))
        cur.execute("delete from famiglia_proposta where codice = any(%s)", (codici,))
        conn.commit()
        print("approvata «%s»: %d articoli nella famiglia" % (a.approva, len(codici)))
        return
    a.catalogo = a.catalogo or CATALOGO_DEFAULT
    if a.prefisso:
        buoni, dubbi = per_prefisso(cur, a.catalogo, a.min)
        cur.execute("SELECT count(*) FROM materiale WHERE catalogo = %s AND famiglia_id IS NULL AND nomev2 IS NOT NULL",
                    (a.catalogo,))
        print("%s: %d articoli senza famiglia; per prime parole: %d famiglie nuove (%d articoli), %d gruppi da confermare "
              "(%d articoli)" % (a.catalogo, cur.fetchone()[0], len(buoni), sum(len(b[1]) for b in buoni), len(dubbi),
                                 sum(len(d[1]) for d in dubbi)))
        for nome, codici, esempi in sorted(buoni, key=lambda x: -len(x[1])):
            print("  %4d  %-30s %s" % (len(codici), nome[:30], " | ".join(e[:38] for e in esempi)))
        for nome, codici, esempi, motivo in dubbi:
            print("  %4d  %-30s DA CONFERMARE: %s  (%s)" % (len(codici), nome[:30], motivo, " | ".join(e[:38] for e in esempi)))
        if a.assegna:
            raise SystemExit("Con --prefisso si usa --salva: i gruppi diventano famiglie DA APPROVARE, non famiglie.")
        if a.salva:
            cur.execute(TABELLA)
            cur.execute("DELETE FROM famiglia_proposta WHERE codice IN (SELECT codice FROM materiale WHERE catalogo = %s)",
                        (a.catalogo,))
            for nome, codici, *resto in buoni + dubbi:
                nota = resto[1] if len(resto) > 1 else None
                cur.executemany("INSERT INTO famiglia_proposta (codice, nome, nota) VALUES (%s, %s, %s)",
                                [(c, nome, nota) for c in codici])
            conn.commit()
            print("famiglie da approvare salvate: %d (gli articoli restano senza famiglia)" % (len(buoni) + len(dubbi)))
        return
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
