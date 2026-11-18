# -*- coding: utf-8 -*-
"""Prepara il progetto su un PC nuovo (lo lanciano installa.bat su Windows e installa.sh su Mac/Linux):
  1. crea `.env` da `.env.example` se manca (su Mac/Linux mette come PGUSER il nome utente del sistema);
  2. si collega a PostgreSQL;
  3. crea il database indicato in PGDATABASE se non esiste;
  4. applica schema.sql (tabelle).
Si puo' rilanciare quando si vuole: non cancella nulla.
"""
import getpass
import os
import re
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ENV, ENV_ESEMPIO = os.path.join(AQUI, ".env"), os.path.join(AQUI, ".env.example")


def main():
    print("Python %s" % sys.version.split()[0])
    if not os.path.isfile(ENV):
        shutil.copyfile(ENV_ESEMPIO, ENV)
        if sys.platform != "win32":      # su Mac/Linux l'utente di PostgreSQL e' di solito quello del sistema
            with open(ENV, encoding="utf-8") as f:
                t = f.read()
            t = re.sub(r"(?m)^PGUSER=.*$", "PGUSER=" + getpass.getuser(), t)
            with open(ENV, "w", encoding="utf-8") as f:
                f.write(t)
        print("Creato il file .env (aprilo per cambiare nome del database, utente e password).")
    else:
        print("Il file .env c'e' gia': non lo tocco.")

    import psycopg2
    from psycopg2 import sql
    import arricchimento  # noqa: F401  (legge .env)
    dbname = os.environ.get("PGDATABASE", "db_serio_finale")
    parametri = dict(user=os.environ.get("PGUSER", "postgres"), host=os.environ.get("PGHOST", "localhost"),
                     port=os.environ.get("PGPORT", "5432"), password=os.environ.get("PGPASSWORD") or None)
    try:
        c = psycopg2.connect(dbname="postgres", **parametri)
    except Exception as e:
        print("\nNON riesco a collegarmi a PostgreSQL come utente %r su %s:%s." % (
            parametri["user"], parametri["host"], parametri["port"]))
        print("Controlla che PostgreSQL sia installato e acceso, e che in .env PGUSER e PGPASSWORD siano giusti.")
        print("Dettaglio:", str(e).strip()[:300].encode("ascii", "replace").decode())
        return 1
    c.autocommit = True
    cur = c.cursor()
    cur.execute("select 1 from pg_database where datname = %s", (dbname,))
    if cur.fetchone():
        print("Database %r: esiste gia'." % dbname)
    else:
        cur.execute(sql.SQL("create database {}").format(sql.Identifier(dbname)))
        print("Database %r: creato." % dbname)
    c.close()

    c = psycopg2.connect(dbname=dbname, **parametri)
    with c, c.cursor() as cur, open(os.path.join(AQUI, "schema.sql"), encoding="utf-8") as f:
        cur.execute(f.read())
    c.close()
    print("Tabelle pronte.")
    print("\nTutto pronto. Prossimo passo: importa il catalogo (vedi CLAUDE.md, punto 1) oppure apri Claude Code qui.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
