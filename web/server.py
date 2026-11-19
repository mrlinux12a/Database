"""Sito di consultazione di db_serio_finale: per ogni codice fornitore mostra nomeV1 e gli attributi trovati
(solo quelli con un valore: dove non c'e' niente, la riga non esiste).

Uso:  py -3.15 web/server.py [--porta 8001] [--apri] [--host 127.0.0.1]
Di default e' raggiungibile solo da questo PC. Connessione al database: PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE
(default: localhost, 5432, postgres, nessuna password, db_serio_finale).

Su un server (VPS) le impostazioni stanno nel file .env (vedi .env.example e README, "Pagina web su una VPS"):
  WEB_HOST=0.0.0.0     ascolta su tutte le interfacce (default 127.0.0.1 = solo questo computer)
  WEB_PORTA=8001
  WEB_UTENTE / WEB_PASSWORD   accesso con nome e password (autenticazione HTTP Basic). Se il sito ascolta fuori da
                              127.0.0.1 la password e' OBBLIGATORIA: senza, il server non parte.
La pagina e' in sola lettura (solo GET) e non mostra prezzi. /salute risponde "ok" senza password (per i controlli).

Indirizzi
  /                 la pagina
  /api/cataloghi    i cataloghi presenti, ognuno con i suoi numeri (articoli, attributi, famiglie, fonti)
  /api/articoli     ?catalogo=Nome &q=parole &attr=chiave|__nessuno &origine=descrizione|codice|sito|web &famiglia=id
                    &ordine=codice|nome &pagina=N
                    &f=chiave::valore   (ripetibile: l'articolo deve avere tutti quei valori di attributo)
  /api/faccette     stessi filtri di /api/articoli + &chiave=attributo: gli attributi che hanno piu' di un valore tra gli articoli
                    filtrati e, per `chiave`, i suoi valori con il numero di articoli
  /api/attributi    ?catalogo=Nome   elenco degli attributi con il numero di articoli che hanno un valore (e da quale origine)
  /api/info         ?catalogo=Nome   informazioni utili: famiglie, attributi candidati, fonti consultate, articoli senza attributi
  /api/famiglie     ?catalogo=Nome   le famiglie (per le schede della pagina): articoli, cataloghi, attributi che servono a filtrare
  /api/candidati    ?catalogo=Nome   tutti gli attributi candidati, con il nome dell'articolo di esempio
  /foto/<file>      le foto degli articoli (cartella `foto` del progetto o CARTELLA_FOTO; vedi indice_foto)

Filtri comuni: famiglia=-1 = articoli senza famiglia; f=chiave::valore ripetuto con la STESSA chiave = uno qualsiasi di quei valori
(con chiavi diverse: tutti). /api/faccette con &tutte=1 restituisce i valori di tutti gli attributi in una volta.
/api/articoli accetta anche ordine=a:<chiave> (&verso=desc) per ordinare secondo un attributo (prima il numero, poi il testo).
"""
import argparse
import base64
import hmac
import json
import os
import re
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, unquote, urlparse

import psycopg2
from psycopg2.pool import ThreadedConnectionPool

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(BASE))
import arricchimento  # noqa: E402,F401  (legge il file .env)
INDEX = os.path.join(BASE, "index.html")

# ---- foto degli articoli ---------------------------------------------------------------------------------------------
# Cartella delle foto: CARTELLA_FOTO nel .env, altrimenti la cartella `foto` del progetto. Una foto si collega a un
# articolo dal NOME DEL FILE = codice fornitore (o codice interno), con eventuale suffisso dopo "_" per averne piu' di una:
#   foto/652514.jpg   foto/652514_2.jpg   foto/652514_retro.png
# Si puo' usare una sottocartella per catalogo (foto/Aquatechnik/652514.jpg): vale solo per quel catalogo, e vince sulla
# cartella principale se lo stesso codice c'e' in tutte e due. Le foto si vedono da /foto/<percorso>.
CARTELLA_FOTO = os.path.abspath(os.environ.get("CARTELLA_FOTO") or os.path.join(os.path.dirname(BASE), "foto"))
TIPI_FOTO = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp", ".gif": "image/gif",
             ".avif": "image/avif"}
_FOTO = {"quando": 0.0, "indice": {}, "dubbie": set(), "insiemi": {}, "qual": {}}


# Foto scaricate dal sito del produttore (scarica_foto.py): foto/<Catalogo>/_file/<nome>.jpg + foto/<Catalogo>/mappa.json
# {codice fornitore: {"file": "_file/<nome>.jpg", "affidabilita": "alta|media|solo serie", ...}}. La cartella _file non
# si indicizza per nome: le foto si collegano ai codici solo tramite la mappa (una foto per molti codici, senza copie).
SOGLIA_LATO = 600          # foto con il lato corto sotto questi pixel = qualita' bassa
SOGLIA_BYTE = 25_000       # o file piu' piccolo di cosi'
_DIM = {}                  # {percorso: (mtime, larghezza, altezza)}


def dimensioni(percorso):
    """(larghezza, altezza) di un jpg/png/webp/gif leggendo solo l'intestazione; None se non riconosciuta."""
    try:
        mt = os.path.getmtime(percorso)
        if percorso in _DIM and _DIM[percorso][0] == mt:
            return _DIM[percorso][1:]
        with open(percorso, "rb") as f:
            testa = f.read(32)
            dim = None
            if testa[:8] == b"\x89PNG\r\n\x1a\n":
                dim = (int.from_bytes(testa[16:20], "big"), int.from_bytes(testa[20:24], "big"))
            elif testa[:3] == b"GIF":
                dim = (int.from_bytes(testa[6:8], "little"), int.from_bytes(testa[8:10], "little"))
            elif testa[:4] == b"RIFF" and testa[8:12] == b"WEBP":
                if testa[12:16] == b"VP8X":
                    dim = (1 + int.from_bytes(testa[24:27], "little"), 1 + int.from_bytes(testa[27:30], "little"))
                elif testa[12:16] == b"VP8 ":
                    dim = (int.from_bytes(testa[26:28], "little") & 0x3FFF, int.from_bytes(testa[28:30], "little") & 0x3FFF)
            elif testa[:2] == b"\xff\xd8":
                f.seek(2)
                while True:
                    b = f.read(1)
                    while b and b != b"\xff":
                        b = f.read(1)
                    while b == b"\xff":
                        b = f.read(1)
                    if not b:
                        break
                    lung = int.from_bytes(f.read(2), "big")
                    if b[0] in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                        s = f.read(5)
                        dim = (int.from_bytes(s[3:5], "big"), int.from_bytes(s[1:3], "big"))
                        break
                    f.seek(lung - 2, 1)
        _DIM[percorso] = (mt,) + (dim or (0, 0))
        return dim
    except OSError:
        return None


def qualita_file(rel):
    """'bassa' se la foto e' piccola (lato corto < SOGLIA_LATO px o file < SOGLIA_BYTE), altrimenti 'ok'."""
    q = _FOTO["qual"].get(rel)
    if q is None:                                         # una volta per file e per ogni rilettura dell'indice
        p = os.path.join(CARTELLA_FOTO, rel)
        dim = dimensioni(p)
        try:
            piccolo = os.path.getsize(p) < SOGLIA_BYTE
        except OSError:
            piccolo = False
        q = _FOTO["qual"][rel] = "bassa" if (dim and min(dim) < SOGLIA_LATO) or piccolo else "ok"
    return q


def indice_foto():
    """{(sottocartella in minuscolo o "", nome base in minuscolo): [percorsi relativi]}, riletto al massimo ogni 15 s.
    In _FOTO["dubbie"] i (catalogo, codice) la cui foto viene da un abbinamento non sicuro (mappa.json: media / solo serie)."""
    adesso = time.time()
    if adesso - _FOTO["quando"] < 15:
        return _FOTO["indice"]
    indice, dubbie = {}, set()
    if os.path.isdir(CARTELLA_FOTO):
        for radice, cartelle, file in os.walk(CARTELLA_FOTO):
            cartelle[:] = sorted(c for c in cartelle if not c.startswith((".", "_")))
            rel_dir = os.path.relpath(radice, CARTELLA_FOTO)
            prima = "" if rel_dir == "." else rel_dir.replace("\\", "/").split("/")[0].lower()
            for nome in sorted(file):
                base, est = os.path.splitext(nome)
                if est.lower() not in TIPI_FOTO or nome.startswith("."):
                    continue
                rel = nome if rel_dir == "." else rel_dir.replace("\\", "/") + "/" + nome
                base = base.lower()
                indice.setdefault((prima, base), []).append(rel)
                if "_" in base:                                  # 652514_2 -> anche sotto 652514
                    indice.setdefault((prima, base.split("_", 1)[0]), []).append(rel)
            if "mappa.json" in file and rel_dir != "." and "/" not in rel_dir.replace("\\", "/"):
                try:                                             # foto scaricate dal produttore: dopo quelle messe a mano
                    with open(os.path.join(radice, "mappa.json"), encoding="utf-8") as f:
                        mappa = json.load(f)
                except (OSError, ValueError):
                    mappa = {}
                for cod, v in mappa.items():
                    chiave = (prima, cod.strip().lower())
                    rel = rel_dir.replace("\\", "/") + "/" + v["file"]
                    if chiave in indice or not os.path.exists(os.path.join(CARTELLA_FOTO, rel)):
                        continue                                 # c'e' gia' una foto messa a mano per questo codice
                    indice[chiave] = [rel]
                    if v.get("affidabilita", "alta") != "alta":
                        dubbie.add(chiave)
    _FOTO.update(quando=adesso, indice=indice, dubbie=dubbie, insiemi={})
    return indice


def stato_foto(catalogo, *codici):
    """'senza' | 'bassa' (tutte le foto sono piccole) | 'dubbia' (abbinamento non sicuro) | 'ok' per un articolo."""
    foto = foto_di(catalogo, *codici)
    if not foto:
        return "senza"
    if all(qualita_file(unquote(f[len("/foto/"):])) == "bassa" for f in foto):
        return "bassa"
    cat = (catalogo or "").lower()
    if any((cat, str(c).strip().lower()) in _FOTO["dubbie"] for c in codici if c):
        return "dubbia"
    return "ok"


def insiemi_foto(catalogo):
    """{'con': codici (minuscoli) che hanno foto, 'bassa': ..., 'dubbia': ...} per un catalogo (o tutti se vuoto)."""
    indice = indice_foto()
    if catalogo in _FOTO["insiemi"]:
        return _FOTO["insiemi"][catalogo]
    cat = (catalogo or "").lower()
    ins = {"con": set(), "bassa": set(), "dubbia": set()}
    for (cartella, cod), rels in indice.items():
        if catalogo and cartella not in (cat, ""):
            continue
        ins["con"].add(cod)
        if all(qualita_file(r) == "bassa" for r in rels):
            ins["bassa"].add(cod)
        elif (cartella, cod) in _FOTO["dubbie"]:
            ins["dubbia"].add(cod)
    _FOTO["insiemi"][catalogo] = ins
    return ins


def miniatura(percorso, rel, larghezza):
    """Percorso della miniatura (JPEG, lato lungo = larghezza) o None se Pillow non c'e' o l'immagine non si legge."""
    try:
        from PIL import Image
    except ImportError:
        return None
    nome = re.sub(r"[^A-Za-z0-9._-]+", "_", rel) + ".jpg"
    dest = os.path.join(CARTELLA_FOTO, "_miniature", str(larghezza), nome)
    try:
        if os.path.exists(dest) and os.path.getmtime(dest) >= os.path.getmtime(percorso):
            return dest
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with Image.open(percorso) as im:
            im = im.convert("RGB")
            im.thumbnail((larghezza, larghezza))
            tmp = dest + ".%d.tmp" % threading.get_ident()
            im.save(tmp, "JPEG", quality=82, optimize=True)
            os.replace(tmp, dest)
        return dest
    except Exception:
        return None


def nome_cartella_foto():
    """Come chiamare la cartella delle foto nella pagina: relativa al progetto se e' dentro, altrimenti il percorso."""
    progetto = os.path.dirname(BASE)
    if os.path.dirname(CARTELLA_FOTO) == progetto:
        return os.path.basename(CARTELLA_FOTO)
    return CARTELLA_FOTO


def foto_di(catalogo, *codici):
    """Indirizzi delle foto di un articolo: prima quelle della sottocartella del catalogo, altrimenti quelle della cartella
    principale. Il file col nome esatto viene prima delle varianti (_2, _retro...)."""
    indice = indice_foto()
    if not indice:
        return []
    for cartella in ((catalogo or "").lower(), ""):
        trovate = []
        for cod in codici:
            if cod:
                for rel in indice.get((cartella, str(cod).strip().lower()), []):
                    if rel not in trovate:
                        trovate.append(rel)
        if trovate:
            esatte = [r for r in trovate if "_" not in os.path.splitext(os.path.basename(r))[0]]
            return ["/foto/" + quote(r) for r in esatte + [r for r in trovate if r not in esatte]][:12]
    return []
PER_PAGINA = 50
ORIGINI = ("descrizione", "codice", "sito", "web")
NESSUNO = "__nessuno"              # filtro speciale: articoli senza nessun attributo
POOL = None
CREDENZIALI = None                 # b"utente:password" se l'accesso e' protetto


def con_cursore(funzione):
    conn = POOL.getconn()
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            return funzione(cur)
    finally:
        POOL.putconn(conn)


_RICHIESTA = threading.local()     # parametri della richiesta in corso che non passano da tutte le funzioni (filtro foto)


def condizioni(q, attr, origine, catalogo="", famiglia=0, filtri=(), escludi="", foto=None):
    """Condizione SQL (su `materiale m`) e parametri per i filtri della pagina. `filtri` = [(chiave, valore), ...]: per ogni
    chiave l'articolo deve avere UNO dei valori scelti, e deve soddisfare TUTTE le chiavi (le faccette). `escludi` = chiave
    di cui non applicare il filtro (serve a contare le alternative di un attributo gia' filtrato). famiglia=-1 = senza famiglia."""
    where, params = [], []
    if catalogo:
        where.append("m.catalogo = %s")
        params.append(catalogo)
    filtro_foto = getattr(_RICHIESTA, "foto", "") if foto is None else foto        # senza | bassa | dubbia | con (vedi do_GET)
    if filtro_foto in ("senza", "bassa", "dubbia", "con"):
        ins = insiemi_foto(catalogo)
        if filtro_foto == "senza":
            where.append("NOT (lower(m.cod_fornitore) = ANY(%s) OR m.codice = ANY(%s))")
            elenco = ins["con"]
        else:
            where.append("(lower(m.cod_fornitore) = ANY(%s) OR m.codice = ANY(%s))")
            elenco = ins["con" if filtro_foto == "con" else filtro_foto]
        params += [list(elenco), list(elenco)]
    if famiglia == -1:
        where.append("m.famiglia_id IS NULL")
    elif famiglia:
        where.append("m.famiglia_id = %s")
        params.append(famiglia)
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
    per_chiave = {}
    for chiave, valore in filtri:
        if chiave != escludi:
            per_chiave.setdefault(chiave, []).append(valore)
    for chiave, valori in per_chiave.items():
        where.append("EXISTS (SELECT 1 FROM materiale_attributo x WHERE x.codice = m.codice AND x.chiave = %s "
                     "AND x.valore = ANY(%s))")
        params += [chiave, valori]
    return " AND ".join(where) or "TRUE", params


def cerca(q, pagina, attr, origine, ordine, catalogo="", famiglia=0, filtri=(), verso="asc"):
    """Articoli che contengono TUTTE le parole di `q` nel codice fornitore, nel nomeV1, nella descrizione o in un valore
    di attributo (senza badare alle maiuscole); opzionalmente solo quelli che hanno l'attributo `attr` (con quell'origine)
    e quelli che hanno certi valori di attributo (`filtri`). ordine = codice | nome | a:<chiave attributo>."""
    cond, params = condizioni(q, attr, origine, catalogo, famiglia, filtri)
    desc = " DESC" if verso == "desc" else ""
    p_ordine = []
    if ordine.startswith("a:"):
        sub = "(SELECT x.%s FROM materiale_attributo x WHERE x.codice = m.codice AND x.chiave = %%s)"
        ordina = (sub % "valore_num") + desc + " NULLS LAST, lower(" + (sub % "valore") + ")" + desc + " NULLS LAST, m.codice"
        p_ordine = [ordine[2:], ordine[2:]]
    elif ordine == "nome":
        ordina = "lower(m.nomev1)" + desc + ", m.codice"
    else:
        ordina = "lower(m.cod_fornitore)" + desc + ", m.codice"

    def esegui(cur):
        cur.execute("SELECT count(*) FROM materiale m WHERE " + cond, params)
        totale = cur.fetchone()[0]
        pagine = max(1, -(-totale // PER_PAGINA))
        pag = min(max(1, pagina), pagine)
        cur.execute("SELECT m.codice, m.cod_fornitore, m.nomev1, m.descrizione, m.nomev2, m.catalogo, f.nome "
                    "FROM materiale m LEFT JOIN famiglia f ON f.id = m.famiglia_id WHERE " + cond +
                    " ORDER BY " + ordina + " LIMIT %s OFFSET %s",
                    params + p_ordine + [PER_PAGINA, (pag - 1) * PER_PAGINA])
        righe = cur.fetchall()
        attributi = {r[0]: [] for r in righe}
        if righe:
            cur.execute("SELECT x.codice, x.chiave, x.valore, x.origine, x.fonte "
                        "FROM materiale_attributo x JOIN attributo a ON a.chiave = x.chiave "
                        "WHERE x.codice = ANY(%s) ORDER BY a.ordine", (list(attributi),))
            for codice, chiave, valore, orig, fonte in cur.fetchall():
                attributi[codice].append([chiave, valore, orig, fonte])
        # quanti articoli dello stesso insieme (famiglia, ricerca, filtri) hanno / non hanno foto, senza il filtro foto
        cond_f, params_f = condizioni(q, attr, origine, catalogo, famiglia, filtri, foto="")
        cur.execute("SELECT lower(m.cod_fornitore), m.codice FROM materiale m WHERE " + cond_f, params_f)
        ins = insiemi_foto(catalogo)
        n_foto = {"tutte": 0, "con": 0, "senza": 0, "bassa": 0, "dubbia": 0}
        for forn, codice in cur.fetchall():
            n_foto["tutte"] += 1
            if forn in ins["con"] or codice in ins["con"]:
                n_foto["con"] += 1
                for k in ("bassa", "dubbia"):
                    if forn in ins[k] or codice in ins[k]:
                        n_foto[k] += 1
            else:
                n_foto["senza"] += 1
        return {"totale": totale, "pagina": pag, "pagine": pagine, "per_pagina": PER_PAGINA, "cartella_foto": nome_cartella_foto(),
                "n_foto": n_foto,
                "righe": [{"codice": codice, "cod": forn, "nome": nome, "nome2": nome2, "descr": descr,
                           "attr": attributi[codice], "catalogo": cat, "famiglia": fam,
                           "foto": foto_di(cat, forn, codice), "foto_stato": stato_foto(cat, forn, codice)}
                          for codice, forn, nome, descr, nome2, cat, fam in righe]}

    return con_cursore(esegui)


def riepilogo_foto():
    """Per catalogo: articoli, con foto buona, da verificare (abbinamento dubbio), qualita' bassa, senza foto."""
    def esegui(cur):
        cur.execute("SELECT catalogo, codice, cod_fornitore FROM materiale")
        out = {}
        for cat, codice, forn in cur.fetchall():
            r = out.setdefault(cat, {"catalogo": cat, "totale": 0, "ok": 0, "dubbia": 0, "bassa": 0, "senza": 0})
            ins = insiemi_foto(cat)
            f = (forn or "").lower()
            r["totale"] += 1
            if f not in ins["con"] and codice not in ins["con"]:
                r["senza"] += 1
            elif f in ins["bassa"] or codice in ins["bassa"]:
                r["bassa"] += 1
            elif f in ins["dubbia"] or codice in ins["dubbia"]:
                r["dubbia"] += 1
            else:
                r["ok"] += 1
        return sorted(out.values(), key=lambda r: r["catalogo"])
    return {"cataloghi": con_cursore(esegui), "soglia_lato": SOGLIA_LATO, "soglia_kb": SOGLIA_BYTE // 1000}


MAX_VALORI = 60                  # valori mostrati per attributo nelle faccette


def faccette(q, attr, origine, catalogo="", famiglia=0, filtri=(), chiave=""):
    """Per l'insieme di articoli che passa i filtri: gli attributi che HANNO PIU' DI UN VALORE (quelli che servono a restringere:
    un attributo con un solo valore non distingue niente) e, se `chiave` e' data, i valori di quell'attributo con il numero di
    articoli. E' il modo di arrivare all'articolo: prima la famiglia, poi un attributo dopo l'altro."""
    cond, params = condizioni(q, attr, origine, catalogo, famiglia, filtri)

    def esegui(cur):
        cur.execute("SELECT x.chiave, count(DISTINCT x.valore), count(*) FROM materiale m "
                    "JOIN materiale_attributo x ON x.codice = m.codice JOIN attributo a ON a.chiave = x.chiave "
                    "WHERE " + cond + " GROUP BY x.chiave, a.ordine HAVING count(DISTINCT x.valore) > 1 ORDER BY a.ordine", params)
        chiavi = [{"chiave": c, "valori": nv, "articoli": n} for c, nv, n in cur.fetchall()]
        valori = []
        if chiave:
            cur.execute("SELECT x.valore, count(*) FROM materiale m JOIN materiale_attributo x ON x.codice = m.codice "
                        "WHERE " + cond + " AND x.chiave = %s GROUP BY x.valore ORDER BY count(*) DESC, x.valore LIMIT %s",
                        params + [chiave, MAX_VALORI])
            valori = [{"valore": v, "n": n} for v, n in cur.fetchall()]
        return {"chiavi": chiavi, "chiave": chiave, "valori": valori}

    return con_cursore(esegui)


MAX_VALORI_TUTTE = 80              # valori per attributo quando si chiedono tutte le faccette insieme


def faccette_tutte(q, attr, origine, catalogo="", famiglia=0, filtri=()):
    """Tutti gli attributi utili a restringere, ciascuno con i suoi valori e il numero di articoli. Per un attributo gia'
    filtrato i numeri sono calcolati SENZA il suo filtro, cosi' si vedono (e si possono aggiungere) le alternative."""
    filtrate = list(dict.fromkeys(k for k, _ in filtri))

    def esegui(cur):
        cur.execute("SELECT chiave FROM attributo ORDER BY ordine")
        ordine = {c: i for i, (c,) in enumerate(cur.fetchall())}
        cond, params = condizioni(q, attr, origine, catalogo, famiglia, filtri)
        cur.execute("SELECT count(*) FROM materiale m WHERE " + cond, params)
        totale = cur.fetchone()[0]
        cur.execute("SELECT x.chiave, x.valore, min(x.valore_num), count(*) FROM materiale m "
                    "JOIN materiale_attributo x ON x.codice = m.codice WHERE " + cond + " GROUP BY 1, 2", params)
        gruppi = {}
        for chiave, valore, num, n in cur.fetchall():
            if chiave not in filtrate:
                gruppi.setdefault(chiave, []).append((valore, num, n))
        for chiave in filtrate:
            cond_k, params_k = condizioni(q, attr, origine, catalogo, famiglia, filtri, escludi=chiave)
            cur.execute("SELECT x.valore, min(x.valore_num), count(*) FROM materiale m "
                        "JOIN materiale_attributo x ON x.codice = m.codice WHERE " + cond_k + " AND x.chiave = %s "
                        "GROUP BY 1", params_k + [chiave])
            gruppi[chiave] = cur.fetchall()
        attributi, costanti = [], []
        for chiave, valori in gruppi.items():
            if len(valori) < 2 and chiave not in filtrate:      # un solo valore non distingue niente: e' una
                costanti.append({"chiave": chiave, "valore": valori[0][0], "n": valori[0][2]})  # caratteristica comune
                continue
            valori.sort(key=lambda v: (-v[2], v[0]))
            attributi.append({"chiave": chiave, "n_valori": len(valori), "articoli": sum(v[2] for v in valori),
                              "filtrato": chiave in filtrate,
                              "valori": [{"valore": v, "num": float(num) if num is not None else None, "n": n}
                                         for v, num, n in valori[:MAX_VALORI_TUTTE]]})
        attributi.sort(key=lambda a: ordine.get(a["chiave"], 999))
        costanti.sort(key=lambda a: ordine.get(a["chiave"], 999))
        return {"totale": totale, "attributi": attributi, "costanti": costanti}

    return con_cursore(esegui)


def elenco_famiglie(catalogo=""):
    """Le famiglie per le schede della pagina: articoli (nel catalogo scelto o in tutti), cataloghi in cui c'e', e gli
    attributi che distinguono i suoi articoli (piu' di un valore), dal piu' diffuso."""
    filtro = " AND m.catalogo = %s" if catalogo else ""
    p = [catalogo] if catalogo else []

    def esegui(cur):
        cur.execute("SELECT f.id, f.nome, m.catalogo, count(*) FROM materiale m JOIN famiglia f ON f.id = m.famiglia_id "
                    "GROUP BY f.id, f.nome, m.catalogo")
        fam = {}
        for i, nome, cat, n in cur.fetchall():
            fam.setdefault(i, {"id": i, "nome": nome, "cataloghi": {}})["cataloghi"][cat] = n
        cur.execute("SELECT m.famiglia_id, x.chiave, count(DISTINCT x.valore), count(*) FROM materiale m "
                    "JOIN materiale_attributo x ON x.codice = m.codice JOIN attributo a ON a.chiave = x.chiave "
                    "WHERE m.famiglia_id IS NOT NULL" + filtro + " GROUP BY 1, 2 HAVING count(DISTINCT x.valore) > 1 "
                    "ORDER BY 1, 4 DESC", p)
        chiavi = {}
        for i, chiave, nv, n in cur.fetchall():
            chiavi.setdefault(i, []).append({"chiave": chiave, "valori": nv, "articoli": n})
        famiglie = []
        for f in fam.values():
            n = f["cataloghi"].get(catalogo, 0) if catalogo else sum(f["cataloghi"].values())
            if n:
                famiglie.append(dict(f, n=n, comune=len(f["cataloghi"]) > 1, attributi=chiavi.get(f["id"], [])))
        famiglie.sort(key=lambda f: (-f["n"], f["nome"].lower()))
        cur.execute("SELECT count(*) FROM materiale m WHERE m.famiglia_id IS NULL" + filtro, p)
        senza = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM materiale m WHERE TRUE" + filtro, p)
        totale = cur.fetchone()[0]
        return {"catalogo": catalogo, "totale": totale, "senza_famiglia": senza, "famiglie": famiglie}

    return con_cursore(esegui)


def elenco_candidati(catalogo=""):
    """Tutti gli attributi candidati (testo ripetuto nel nomeV2), con il nome dell'articolo di esempio."""
    def esegui(cur):
        cur.execute("SELECT c.id, c.catalogo, c.testo, c.n, c.stato, c.esempio_codice, c.note, e.nomev1, e.nomev2 "
                    "FROM attributo_candidato c LEFT JOIN LATERAL (SELECT m.nomev1, m.nomev2 FROM materiale m "
                    "WHERE m.catalogo = c.catalogo AND (m.cod_fornitore = c.esempio_codice OR m.codice = c.esempio_codice) "
                    "LIMIT 1) e ON TRUE" + (" WHERE c.catalogo = %s" if catalogo else "") +
                    " ORDER BY c.n DESC, c.testo", [catalogo] if catalogo else [])
        return {"candidati": [{"id": i, "catalogo": cat, "testo": t, "n": n, "stato": s, "esempio": es, "note": note,
                               "esempio_nome": n1, "esempio_nome2": n2}
                              for i, cat, t, n, s, es, note, n1, n2 in cur.fetchall()]}

    return con_cursore(esegui)


def elenco_attributi(catalogo=""):
    """Attributi con il numero di articoli che hanno un valore: di tutto il database o di un solo catalogo."""
    filtro_m = " WHERE catalogo = %s" if catalogo else ""
    filtro_x = " AND x.codice IN (SELECT codice FROM materiale WHERE catalogo = %s)" if catalogo else ""
    p = [catalogo] if catalogo else []

    def esegui(cur):
        cur.execute("SELECT count(*) FROM materiale" + filtro_m, p)
        totale = cur.fetchone()[0]
        cur.execute("SELECT count(DISTINCT x.codice) FROM materiale_attributo x WHERE TRUE" + filtro_x, p)
        con_attributi = cur.fetchone()[0]
        cur.execute("SELECT x.chiave, x.origine, count(*) FROM materiale_attributo x WHERE TRUE" + filtro_x +
                    " GROUP BY x.chiave, x.origine", p)
        origini = {}
        for chiave, orig, n in cur.fetchall():
            origini.setdefault(chiave, {})[orig] = n
        cur.execute("SELECT a.chiave, a.etichetta, coalesce(a.breve, a.etichetta), a.gruppo, a.nuovo "
                    "FROM attributo a ORDER BY a.ordine")
        attributi = [{"chiave": c, "etichetta": e, "breve": b, "gruppo": g, "nuovo": nuovo,
                      "n": sum(origini.get(c, {}).values()), "origini": origini.get(c, {})}
                     for c, e, b, g, nuovo in cur.fetchall()]
        return {"totale": totale, "con_attributi": con_attributi, "senza": totale - con_attributi,
                "attributi": attributi}

    return con_cursore(esegui)


def elenco_cataloghi():
    """Un blocco di numeri per catalogo: serve alla scelta del catalogo e al riepilogo in cima alla pagina."""
    def esegui(cur):
        cur.execute("SELECT catalogo, count(*), count(nomev1), count(famiglia_id), count(DISTINCT famiglia_id) "
                    "FROM materiale GROUP BY catalogo ORDER BY catalogo")
        cataloghi = {c: {"nome": c, "articoli": n, "con_nome": nn, "con_famiglia": nf, "famiglie": fam,
                         "con_attributi": 0, "valori": 0, "origini": {}, "candidati": 0}
                     for c, n, nn, nf, fam in cur.fetchall()}
        cur.execute("SELECT m.catalogo, x.origine, count(*) FROM materiale_attributo x "
                    "JOIN materiale m ON m.codice = x.codice GROUP BY 1, 2")
        for c, orig, n in cur.fetchall():
            cataloghi[c]["origini"][orig] = n
            cataloghi[c]["valori"] += n
        cur.execute("SELECT m.catalogo, count(DISTINCT x.codice) FROM materiale_attributo x "
                    "JOIN materiale m ON m.codice = x.codice GROUP BY 1")
        for c, n in cur.fetchall():
            cataloghi[c]["con_attributi"] = n
        cur.execute("SELECT catalogo, count(*) FROM attributo_candidato WHERE stato = 'proposto' GROUP BY 1")
        for c, n in cur.fetchall():
            if c in cataloghi:
                cataloghi[c]["candidati"] = n
        # famiglie in comune: con articoli di almeno due cataloghi (per catalogo: quante delle sue famiglie lo sono)
        cur.execute("SELECT m.catalogo, count(DISTINCT m.famiglia_id) FROM materiale m WHERE m.famiglia_id IN "
                    "(SELECT famiglia_id FROM materiale WHERE famiglia_id IS NOT NULL GROUP BY 1 "
                    "HAVING count(DISTINCT catalogo) > 1) GROUP BY 1")
        for c in cataloghi.values():
            c["comuni"] = 0
        for c, n in cur.fetchall():
            cataloghi[c]["comuni"] = n
        cur.execute("SELECT count(*) FROM (SELECT 1 FROM materiale WHERE famiglia_id IS NOT NULL GROUP BY famiglia_id "
                    "HAVING count(DISTINCT catalogo) > 1) x")
        return {"cataloghi": list(cataloghi.values()), "comuni": cur.fetchone()[0]}

    return con_cursore(esegui)


def info_catalogo(catalogo):
    """Informazioni utili per chi controlla un catalogo: famiglie, candidati, pagine consultate, articoli senza attributi."""
    filtro = " AND m.catalogo = %s" if catalogo else ""
    p = [catalogo] if catalogo else []

    def esegui(cur):
        # le famiglie sono condivise tra cataloghi: per ognuna i numeri di OGNI catalogo, cosi' si vede quali sono in comune
        cur.execute("SELECT f.id, f.nome, m.catalogo, count(*) FROM materiale m JOIN famiglia f ON f.id = m.famiglia_id "
                    "GROUP BY f.id, f.nome, m.catalogo")
        per_famiglia = {}
        for i, nome, cat, c in cur.fetchall():
            per_famiglia.setdefault(i, {"id": i, "nome": nome, "cataloghi": {}})["cataloghi"][cat] = c
        famiglie = []
        for f in per_famiglia.values():
            n = f["cataloghi"].get(catalogo, 0) if catalogo else sum(f["cataloghi"].values())
            if n:
                famiglie.append({"id": f["id"], "nome": f["nome"], "n": n, "cataloghi": f["cataloghi"],
                                 "comune": len(f["cataloghi"]) > 1})
        famiglie.sort(key=lambda f: (-f["n"], f["nome"].lower()))
        famiglie = famiglie[:400]
        cur.execute("SELECT testo, n, stato, esempio_codice, catalogo FROM attributo_candidato"
                    + (" WHERE catalogo = %s" if catalogo else "") + " ORDER BY n DESC, testo LIMIT 100", p)
        candidati = [{"testo": t, "n": n, "stato": s, "esempio": e, "catalogo": c} for t, n, s, e, c in cur.fetchall()]
        cur.execute("SELECT x.fonte, x.origine, count(*), count(DISTINCT x.chiave) FROM materiale_attributo x "
                    "JOIN materiale m ON m.codice = x.codice WHERE x.fonte IS NOT NULL" + filtro +
                    " GROUP BY 1, 2 ORDER BY 3 DESC", p)
        fonti = [{"url": u, "origine": o, "valori": n, "attributi": na} for u, o, n, na in cur.fetchall()]
        cur.execute("SELECT count(*) FROM materiale m WHERE m.famiglia_id IS NULL" + filtro, p)
        senza_famiglia = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM materiale m WHERE NOT EXISTS "
                    "(SELECT 1 FROM materiale_attributo x WHERE x.codice = m.codice)" + filtro, p)
        senza_attributi = cur.fetchone()[0]
        return {"catalogo": catalogo, "famiglie": famiglie, "candidati": candidati, "fonti": fonti,
                "senza_famiglia": senza_famiglia, "senza_attributi": senza_attributi}

    return con_cursore(esegui)


class Handler(BaseHTTPRequestHandler):
    def invia(self, stato, corpo, tipo):
        self.send_response(stato)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corpo)

    def invia_foto(self, rel, larghezza=0):
        """Un file della cartella delle foto (solo immagini, solo dentro quella cartella). Con `larghezza` (?w=480) una
        miniatura JPEG (serve Pillow; se manca si invia l'originale), salvata in foto/_miniature per le richieste dopo."""
        percorso = os.path.realpath(os.path.join(CARTELLA_FOTO, rel))
        tipo = TIPI_FOTO.get(os.path.splitext(percorso)[1].lower())
        if (not tipo or "\0" in rel or not percorso.startswith(os.path.realpath(CARTELLA_FOTO) + os.sep)
                or not os.path.isfile(percorso)):
            self.invia(404, b"Foto non trovata", "text/plain; charset=utf-8")
            return
        if larghezza:
            mini = miniatura(percorso, rel, larghezza)
            if mini:
                percorso, tipo = mini, "image/jpeg"
        with open(percorso, "rb") as f:
            corpo = f.read()
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "private, max-age=86400")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(corpo)

    def json(self, dati):
        self.invia(200, json.dumps(dati, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def autorizzato(self):
        if CREDENZIALI is None:
            return True
        intest = self.headers.get("Authorization", "")
        if intest.startswith("Basic "):
            try:
                dato = base64.b64decode(intest[6:].strip(), validate=True)
            except ValueError:
                dato = b""
            if hmac.compare_digest(dato, CREDENZIALI):
                return True
        corpo = "Accesso riservato".encode("utf-8")
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Catalogo materiali", charset="UTF-8"')
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)
        return False

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/salute":                       # controllo di funzionamento (systemd, monitor): niente dati
            self.invia(200, b"ok", "text/plain; charset=utf-8")
            return
        if not self.autorizzato():
            return
        if url.path in ("/", "/index.html"):
            with open(INDEX, "rb") as f:
                self.invia(200, f.read(), "text/html; charset=utf-8")
        elif url.path.startswith("/foto/"):
            try:
                w = int((parse_qs(url.query).get("w") or ["0"])[0])
            except ValueError:
                w = 0
            self.invia_foto(unquote(url.path[len("/foto/"):]), w if 100 <= w <= 1200 else 0)
        elif url.path in ("/api/articoli", "/api/attributi", "/api/cataloghi", "/api/info", "/api/faccette",
                          "/api/famiglie", "/api/candidati", "/api/foto"):
            args = parse_qs(url.query)
            _RICHIESTA.foto = (args.get("foto") or [""])[0]

            def arg(nome, default=""):
                return (args.get(nome) or [default])[0]

            filtri = [tuple(f.split("::", 1)) for f in args.get("f", [])[:40] if "::" in f]    # f=chiave::valore, ripetibile

            try:
                if url.path == "/api/attributi":
                    self.json(elenco_attributi(arg("catalogo")[:120]))
                elif url.path == "/api/foto":
                    self.json(riepilogo_foto())
                elif url.path == "/api/cataloghi":
                    self.json(elenco_cataloghi())
                elif url.path == "/api/info":
                    self.json(info_catalogo(arg("catalogo")[:120]))
                elif url.path == "/api/famiglie":
                    self.json(elenco_famiglie(arg("catalogo")[:120]))
                elif url.path == "/api/candidati":
                    self.json(elenco_candidati(arg("catalogo")[:120]))
                else:
                    try:
                        pagina = int(arg("pagina", "1"))
                    except ValueError:
                        pagina = 1
                    origine = arg("origine")
                    ordine = arg("ordine", "codice")
                    try:
                        famiglia = int(arg("famiglia", "0"))
                    except ValueError:
                        famiglia = 0
                    origine = origine if origine in ORIGINI else ""
                    if url.path == "/api/faccette" and arg("tutte") == "1":
                        self.json(faccette_tutte(arg("q"), arg("attr")[:60], origine, arg("catalogo")[:120], famiglia,
                                                 filtri))
                    elif url.path == "/api/faccette":
                        self.json(faccette(arg("q"), arg("attr")[:60], origine, arg("catalogo")[:120], famiglia, filtri,
                                           arg("chiave")[:60]))
                    else:
                        valido = ordine in ("codice", "nome") or re.fullmatch(r"a:[a-z0-9_]{1,40}", ordine)
                        self.json(cerca(arg("q"), pagina, arg("attr")[:60], origine, ordine if valido else "codice",
                                        arg("catalogo")[:120], famiglia, filtri, arg("verso")))
            except Exception as e:
                print("Errore database:", repr(e), file=sys.stderr)
                self.invia(500, b'{"errore": "database non raggiungibile"}', "application/json; charset=utf-8")
        else:
            self.invia(404, b"Pagina non trovata", "text/plain; charset=utf-8")

    def log_message(self, fmt, *args):       # niente riga di log per ogni richiesta
        pass


def main():
    global POOL, CREDENZIALI
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default=os.environ.get("WEB_HOST", "127.0.0.1"),
                    help="0.0.0.0 = raggiungibile da altri computer (serve WEB_PASSWORD)")
    ap.add_argument("--porta", type=int, default=int(os.environ.get("WEB_PORTA", "8001")))
    ap.add_argument("--apri", action="store_true", help="apre il browser")
    a = ap.parse_args()

    utente, password = os.environ.get("WEB_UTENTE", "flash"), os.environ.get("WEB_PASSWORD", "")
    if password:
        CREDENZIALI = ("%s:%s" % (utente, password)).encode("utf-8")
    elif a.host not in ("127.0.0.1", "localhost", "::1"):
        sys.exit("Il sito ascolterebbe su %s, cioe' sarebbe raggiungibile da altri computer, ma manca WEB_PASSWORD.\n"
                 "Metti WEB_UTENTE e WEB_PASSWORD nel file .env (vedi .env.example) e riavvia." % a.host)

    try:
        POOL = ThreadedConnectionPool(1, 8, dbname=os.environ.get("PGDATABASE", "db_serio_finale"),
                                      host=os.environ.get("PGHOST", "localhost"), port=os.environ.get("PGPORT", "5432"),
                                      user=os.environ.get("PGUSER", "postgres"),
                                      password=os.environ.get("PGPASSWORD") or None)
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
    dove = url if a.host in ("127.0.0.1", "localhost", "::1") else "http://<indirizzo-del-server>:%d (ascolta su %s)" % (
        a.porta, a.host)
    print("Database %s: %d articoli. Sito su %s%s (CTRL+C per spegnerlo)"
          % (os.environ.get("PGDATABASE", "db_serio_finale"), n, dove,
             ", accesso con utente %r e password" % utente if CREDENZIALI else ""), flush=True)
    if a.apri:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
