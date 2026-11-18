"""Sito di consultazione di db_serio_finale: per ogni codice fornitore mostra nomeV1 e gli attributi trovati
(solo quelli con un valore: dove non c'e' niente, la riga non esiste).

Uso:  py -3.13 web/server.py [--porta 8001] [--apri] [--host 127.0.0.1]
Di default e' raggiungibile solo da questo PC. Connessione al database: PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE
(default: localhost, 5432, postgres, nessuna password, db_serio_finale).

Indirizzi
  /                 la pagina
  /api/articoli     ?q=parole &attr=chiave|__nessuno &origine=descrizione|codice|sito|web &ordine=codice|nome &pagina=N
  /api/attributi    elenco degli attributi con il numero di articoli che hanno un valore (e da quale origine)
"""
import argparse
import json
import os
import re
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import psycopg2
from psycopg2.pool import ThreadedConnectionPool

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(BASE))
import arricchimento  # noqa: E402,F401  (legge il file .env)
INDEX = os.path.join(BASE, "index.html")
PER_PAGINA = 50
ORIGINI = ("descrizione", "codice", "sito", "web")
NESSUNO = "__nessuno"              # filtro speciale: articoli senza nessun attributo
POOL = None


def con_cursore(funzione):
    conn = POOL.getconn()
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            return funzione(cur)
    finally:
        POOL.putconn(conn)


def cerca(q, pagina, attr, origine, ordine):
    """Articoli che contengono TUTTE le parole di `q` nel codice fornitore, nel nomeV1, nella descrizione o in un valore
    di attributo (senza badare alle maiuscole); opzionalmente solo quelli che hanno l'attributo `attr` (con quell'origine)."""
    where, params = [], []
    for parola in q.split()[:8]:
        like = "%" + re.sub(r"([\\%_])", r"\\\1", parola) + "%"      # % e _ scritti dall'utente valgono come lettere
        where.append("(m.cod_fornitore ILIKE %s OR m.nomev1 ILIKE %s OR m.nomev2 ILIKE %s OR m.descrizione ILIKE %s OR EXISTS "
                     "(SELECT 1 FROM materiale_attributo x WHERE x.codice = m.codice AND x.valore ILIKE %s))")
        params += [like] * 5
    if attr == NESSUNO:
        where.append("NOT EXISTS (SELECT 1 FROM materiale_attributo x WHERE x.codice = m.codice)")
    elif attr or origine:
        sub = "SELECT 1 FROM materiale_attributo x WHERE x.codice = m.codice"
        if attr:
            sub += " AND x.chiave = %s"
            params.append(attr)
        if origine:
            sub += " AND x.origine = %s"
            params.append(origine)
        where.append("EXISTS (" + sub + ")")
    cond = " AND ".join(where) or "TRUE"
    ordina = "lower(m.nomev1), m.codice" if ordine == "nome" else "lower(m.cod_fornitore), m.codice"

    def esegui(cur):
        cur.execute("SELECT count(*) FROM materiale m WHERE " + cond, params)
        totale = cur.fetchone()[0]
        pagine = max(1, -(-totale // PER_PAGINA))
        pag = min(max(1, pagina), pagine)
        cur.execute("SELECT m.codice, m.cod_fornitore, m.nomev1, m.descrizione, m.nomev2 FROM materiale m WHERE " + cond +
                    " ORDER BY " + ordina + " LIMIT %s OFFSET %s", params + [PER_PAGINA, (pag - 1) * PER_PAGINA])
        righe = cur.fetchall()
        attributi = {r[0]: [] for r in righe}
        if righe:
            cur.execute("SELECT x.codice, x.chiave, x.valore, x.origine, x.fonte "
                        "FROM materiale_attributo x JOIN attributo a ON a.chiave = x.chiave "
                        "WHERE x.codice = ANY(%s) ORDER BY a.ordine", (list(attributi),))
            for codice, chiave, valore, orig, fonte in cur.fetchall():
                attributi[codice].append([chiave, valore, orig, fonte])
        return {"totale": totale, "pagina": pag, "pagine": pagine,
                "righe": [{"cod": forn, "nome": nome, "nome2": nome2, "descr": descr, "attr": attributi[codice]}
                          for codice, forn, nome, descr, nome2 in righe]}

    return con_cursore(esegui)


def elenco_attributi():
    def esegui(cur):
        cur.execute("SELECT count(*) FROM materiale")
        totale = cur.fetchone()[0]
        cur.execute("SELECT count(DISTINCT codice) FROM materiale_attributo")
        con_attributi = cur.fetchone()[0]
        cur.execute("SELECT chiave, origine, count(*) FROM materiale_attributo GROUP BY chiave, origine")
        origini = {}
        for chiave, orig, n in cur.fetchall():
            origini.setdefault(chiave, {})[orig] = n
        cur.execute("SELECT a.chiave, a.etichetta, coalesce(a.breve, a.etichetta), a.gruppo, a.nuovo, "
                    "       (SELECT count(*) FROM materiale_attributo x WHERE x.chiave = a.chiave) "
                    "FROM attributo a ORDER BY a.ordine")
        attributi = [{"chiave": c, "etichetta": e, "breve": b, "gruppo": g, "nuovo": nuovo, "n": n,
                      "origini": origini.get(c, {})} for c, e, b, g, nuovo, n in cur.fetchall()]
        return {"totale": totale, "con_attributi": con_attributi, "senza": totale - con_attributi,
                "attributi": attributi}

    return con_cursore(esegui)


class Handler(BaseHTTPRequestHandler):
    def invia(self, stato, corpo, tipo):
        self.send_response(stato)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corpo)

    def json(self, dati):
        self.invia(200, json.dumps(dati, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self):
        url = urlparse(self.path)
        if url.path in ("/", "/index.html"):
            with open(INDEX, "rb") as f:
                self.invia(200, f.read(), "text/html; charset=utf-8")
        elif url.path in ("/api/articoli", "/api/attributi"):
            args = parse_qs(url.query)

            def arg(nome, default=""):
                return (args.get(nome) or [default])[0]

            try:
                if url.path == "/api/attributi":
                    self.json(elenco_attributi())
                else:
                    try:
                        pagina = int(arg("pagina", "1"))
                    except ValueError:
                        pagina = 1
                    origine = arg("origine")
                    ordine = arg("ordine", "codice")
                    self.json(cerca(arg("q"), pagina, arg("attr")[:60],
                                    origine if origine in ORIGINI else "",
                                    ordine if ordine in ("codice", "nome") else "codice"))
            except Exception as e:
                print("Errore database:", repr(e), file=sys.stderr)
                self.invia(500, b'{"errore": "database non raggiungibile"}', "application/json; charset=utf-8")
        else:
            self.invia(404, b"Pagina non trovata", "text/plain; charset=utf-8")

    def log_message(self, fmt, *args):       # niente riga di log per ogni richiesta
        pass


def main():
    global POOL
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--porta", type=int, default=8001)
    ap.add_argument("--apri", action="store_true", help="apre il browser")
    a = ap.parse_args()

    try:
        POOL = ThreadedConnectionPool(1, 8, dbname=os.environ.get("PGDATABASE", "db_serio_finale"),
                                      host=os.environ.get("PGHOST", "localhost"), user=os.environ.get("PGUSER", "postgres"))
        conn = POOL.getconn()
        with conn.cursor() as cur:
            cur.execute("SELECT count(*), count(nomev1) FROM materiale")
            n, n_nomi = cur.fetchone()
        conn.rollback()
        POOL.putconn(conn)
    except Exception as e:
        sys.exit("Non riesco a leggere il database (PostgreSQL acceso? import fatto con avvia_import.bat?): %r" % (e,))
    if n and not n_nomi:
        print("ATTENZIONE: gli articoli non hanno ancora nomeV1 e attributi: lancia arricchisci.py (o avvia_import.bat).")

    try:
        server = ThreadingHTTPServer((a.host, a.porta), Handler)
    except OSError:
        sys.exit("La porta %d e' gia' occupata: il sito e' probabilmente gia' acceso su http://localhost:%d" % (a.porta, a.porta))
    url = "http://localhost:%d" % a.porta
    print("Database %s: %d articoli. Sito su %s (CTRL+C per spegnerlo)"
          % (os.environ.get("PGDATABASE", "db_serio_finale"), n, url))
    if a.apri:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
