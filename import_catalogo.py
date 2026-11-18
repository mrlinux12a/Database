"""Importa in db_serio_finale gli articoli di un catalogo CSV, tenendo solo le linee con "Si'" nell'Excel.

Excel (Flash_Delivery_Linee_per_Brand.xlsx): un blocco per brand (riga col nome del brand, poi una riga per ogni linea)
con la colonna "Tenere?":  Si' = la linea entra · No = resta fuori · cella vuota = resta fuori.
CSV: un file per fornitore, ";" come separatore, UTF-8, sempre le stesse 15 colonne. Le "serie" dell'Excel sono le
righe della colonna "Linea" del CSV (es. "001 Distribuzione Aeraulica": il numero davanti viene ignorato nel confronto);
la colonna "Serie" del CSV di Air Control e' vuota.

Ogni lancio rifa' da zero le righe di QUEL catalogo (cancella e reinserisce in un'unica transazione): si puo' rilanciare
dopo aver cambiato l'Excel senza creare doppioni, e gli altri cataloghi gia' nel database non vengono toccati.

Uso:  py -3.13 import_catalogo.py [--csv FILE] [--brand NOME_NELL_EXCEL] [--excel FILE] [--prova]
      --prova  mostra cosa entrerebbe, senza toccare il database
Connessione: PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE (default: localhost, 5432, postgres, nessuna password,
db_serio_finale).
"""
import argparse
import collections
import csv
import os
import re
import shutil
import sys
import tempfile
from decimal import Decimal

import openpyxl
import psycopg2
from psycopg2.extras import execute_values

BASE = os.path.dirname(os.path.abspath(__file__))
ORIGINE = r"C:\Users\SAMSUNG\lavoro\app2\db"
EXCEL_DEFAULT = os.path.join(ORIGINE, "Flash_Delivery_Linee_per_Brand.xlsx")
CSV_DEFAULT = os.path.join(ORIGINE, "cataloghi", "Air Control SRL.csv")
BRAND_DEFAULT = "AIR CONTROL"          # intestazione del blocco nell'Excel

COLONNE_CSV = ["Codice", "Descrizione", "Sigla", "Marca", "Cod. Fornitore", "Linea", "Serie", "U.M.", "Listino",
               "Sc1", "Sc2", "Sc3", "Sc4", "Netto", "Vecchio Codice"]
COLONNE_DB = ["codice", "descrizione", "sigla", "marca", "cod_fornitore", "linea", "serie", "um", "listino",
              "sc1", "sc2", "sc3", "sc4", "netto", "vecchio_codice", "catalogo"]
NUMERICHE = {"Listino", "Sc1", "Sc2", "Sc3", "Sc4", "Netto"}
NUMERO = re.compile(r"^-?\d+(?:,\d+)?$")       # "172,30000", "44,00": virgola decimale, nessun separatore di migliaia


class ErroreImport(Exception):
    pass


def norm(s):
    return re.sub(r"\s+", " ", str(s if s is not None else "").strip().lower())


def senza_numero(linea):
    """'001 Distribuzione Aeraulica' -> 'Distribuzione Aeraulica'"""
    return re.sub(r"^\d+\s*", "", (linea or "").strip()).strip()


def tenere(valore):
    """True = Si', False = No, None = vuota o non capita (la linea resta fuori)"""
    v = norm(valore)
    if v.startswith("s"):          # "Si", "Sì", "si ", "S"
        return True
    if v.startswith("n"):          # "No", "no", "NO"
        return False
    return None


def apri_excel(percorso):
    try:
        return openpyxl.load_workbook(percorso, data_only=True)
    except PermissionError:        # file aperto in Excel e bloccato: si lavora su una copia
        copia = os.path.join(tempfile.mkdtemp(), "linee.xlsx")
        shutil.copyfile(percorso, copia)
        return openpyxl.load_workbook(copia, data_only=True)


def linee_excel(percorso, brand):
    """{nome_linea_normalizzato: {nome, n, tenere, raw, nota}} del blocco `brand` dell'Excel"""
    ws = apri_excel(percorso).active
    blocchi, corrente, nuovo = {}, None, True
    for a, b, c, d in ws.iter_rows(min_row=5, max_col=4, values_only=True):
        if a is None:              # riga vuota: il blocco successivo e' un altro brand
            nuovo = True
            continue
        if nuovo:
            corrente = norm(a)
            blocchi[corrente] = {"brand": str(a).strip(), "linee": {}}
            nuovo = False
            continue
        blocchi[corrente]["linee"][norm(a)] = {"nome": str(a).strip(), "n": b, "tenere": tenere(c), "raw": c, "nota": d}
    if norm(brand) not in blocchi:
        raise ErroreImport("Il brand %r non c'e' nell'Excel. Brand presenti: %s"
                           % (brand, ", ".join(b["brand"] for b in blocchi.values())))
    return blocchi[norm(brand)]["linee"]


def leggi_csv(percorso):
    with open(percorso, encoding="utf-8-sig", newline="") as f:
        lettore = csv.reader(f, delimiter=";", quotechar='"')
        intestazione = next(lettore)
        if intestazione != COLONNE_CSV:
            raise ErroreImport("Colonne del CSV diverse dal previsto.\n  trovate:   %s\n  previste:  %s"
                               % (intestazione, COLONNE_CSV))
        righe = []
        for n, r in enumerate(lettore, start=2):
            if len(r) != len(COLONNE_CSV):
                raise ErroreImport("Riga %d del CSV con %d colonne invece di %d" % (n, len(r), len(COLONNE_CSV)))
            righe.append(dict(zip(COLONNE_CSV, r)))
    return righe


def numero(valore, campo, codice):
    v = valore.strip()
    if not v:
        return None
    if not NUMERO.match(v):
        raise ErroreImport("%s non numerico per l'articolo %s: %r" % (campo, codice, valore))
    return Decimal(v.replace(",", "."))


def riga_db(r, catalogo):
    """Una riga del CSV -> tupla nell'ordine di COLONNE_DB. Testi invariati; celle vuote (o solo spazi) -> NULL."""
    valori = []
    for col in COLONNE_CSV:
        if col in NUMERICHE:
            valori.append(numero(r[col], col, r["Codice"]))
        else:
            valori.append(r[col].strip() or None)
    valori.append(catalogo)
    return tuple(valori)


def rapporto(righe, linee):
    """Stampa il confronto Excel / CSV per linea e restituisce (righe_da_tenere, avvisi)"""
    per_linea = collections.Counter(senza_numero(r["Linea"]) for r in righe)
    chiavi = {norm(k): k for k in per_linea}
    avvisi = []
    print("\n%-42s %6s %6s   %s" % ("Linea", "CSV", "Excel", "Tenere?"))
    print("-" * 78)
    for k, l in linee.items():
        n_csv = per_linea[chiavi[k]] if k in chiavi else 0
        esito = {True: "SI  -> entra", False: "No  -> fuori", None: "(vuota/non capita) -> fuori"}[l["tenere"]]
        print("%-42s %6d %6s   %s" % (l["nome"][:42], n_csv, l["n"], esito))
        if l["n"] is not None and n_csv != l["n"]:
            avvisi.append("%s: il CSV ha %d articoli, l'Excel ne dice %s" % (l["nome"], n_csv, l["n"]))
        if l["tenere"] is None and l["raw"] is not None:
            avvisi.append("%s: valore %r in 'Tenere?' non capito, la linea resta fuori" % (l["nome"], l["raw"]))
        if l["nota"]:
            avvisi.append("%s: nota nell'Excel: %s" % (l["nome"], l["nota"]))
    for k, nome in chiavi.items():
        if k not in linee:
            avvisi.append("Linea %r (%d articoli) presente nel CSV ma non nell'Excel: resta fuori" % (nome, per_linea[nome]))
    tenute = [r for r in righe if linee.get(norm(senza_numero(r["Linea"])), {}).get("tenere") is True]
    return tenute, avvisi


def connetti():
    try:
        return psycopg2.connect(dbname=os.environ.get("PGDATABASE", "db_serio_finale"),
                                host=os.environ.get("PGHOST", "localhost"),
                                user=os.environ.get("PGUSER", "postgres"))
    except Exception as e:         # (il testo dell'errore di Windows puo' avere accenti illeggibili)
        raise ErroreImport("Non riesco a collegarmi a PostgreSQL (database %s): verifica che sia acceso e che il "
                           "database esista. Dettaglio: %r" % (os.environ.get("PGDATABASE", "db_serio_finale"), e))


def main():
    sys.stdout.reconfigure(errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--csv", default=CSV_DEFAULT)
    ap.add_argument("--excel", default=EXCEL_DEFAULT)
    ap.add_argument("--brand", default=BRAND_DEFAULT)
    ap.add_argument("--prova", action="store_true")
    a = ap.parse_args()
    catalogo = os.path.splitext(os.path.basename(a.csv))[0]

    righe = leggi_csv(a.csv)
    linee = linee_excel(a.excel, a.brand)
    print("CSV:   %s (%d articoli)\nExcel: %s (brand %s)" % (a.csv, len(righe), a.excel, a.brand))
    tenute, avvisi = rapporto(righe, linee)

    codici = collections.Counter(r["Codice"] for r in righe)
    doppi = [c for c, n in codici.items() if n > 1]
    if doppi:
        raise ErroreImport("Codici articolo ripetuti nel CSV (es. %s): importo annullato" % ", ".join(doppi[:5]))
    valori = [riga_db(r, catalogo) for r in tenute]      # controlla anche i numeri prima di toccare il database

    print("\nDa inserire: %d articoli su %d (restano fuori %d)" % (len(valori), len(righe), len(righe) - len(valori)))
    for av in avvisi:
        print("  AVVISO:", av)
    if a.prova:
        print("\n--prova: database non toccato.")
        return

    schema = open(os.path.join(BASE, "schema.sql"), encoding="utf-8").read()
    conn = connetti()
    try:
        with conn:                                       # una sola transazione: o entra tutto o niente
            with conn.cursor() as cur:
                cur.execute(schema)
                cur.execute("DELETE FROM materiale WHERE catalogo = %s", (catalogo,))
                execute_values(cur, "INSERT INTO materiale (%s) VALUES %%s" % ", ".join(COLONNE_DB), valori, page_size=1000)
        with conn.cursor() as cur:
            cur.execute("SELECT linea, count(*) FROM materiale WHERE catalogo = %s GROUP BY 1 ORDER BY 1", (catalogo,))
            nel_db = cur.fetchall()
            cur.execute("SELECT count(*) FROM materiale")
            totale = cur.fetchone()[0]
    finally:
        conn.close()
    print("\nNel database (catalogo %r):" % catalogo)
    for linea, n in nel_db:
        print("  %-42s %6d" % (linea, n))
    print("Totale articoli in tabella materiale: %d" % totale)
    if sum(n for _, n in nel_db) != len(valori):
        raise ErroreImport("Il numero di righe nel database non corrisponde a quelle inserite!")
    print("\nFatto.")


if __name__ == "__main__":
    try:
        main()
    except ErroreImport as e:
        print("\nERRORE:", e)
        sys.exit(1)
