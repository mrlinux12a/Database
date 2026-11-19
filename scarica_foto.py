"""Scarica le foto elencate in un CSV (colonne codice_produttore, url_foto, ...) in foto/<Catalogo>/_file/ e scrive
foto/<Catalogo>/mappa.json = {codice: {"file":..., "url":..., "pagina":..., "affidabilita":...}}.

Uso: py -3.15 scarica_foto.py "C:\\...\\foto_articoli_aircontrol.csv" "Air Control SRL"

Regole del progetto: una richiesta alla volta, pausa 0,5 s, User-Agent generico, niente tentativi di aggirare un 403
(i file che rispondono 403 restano da scaricare a mano: vengono scritti in <catalogo>/da_scaricare.txt).
Una foto gia' scaricata non viene riscaricata."""
import csv, json, os, sys, time, urllib.request, urllib.error, urllib.parse

csv_path, catalogo = sys.argv[1], sys.argv[2]
RADICE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "foto", catalogo)
FILES = os.path.join(RADICE, "_file")
os.makedirs(FILES, exist_ok=True)

righe = list(csv.DictReader(open(csv_path, encoding="utf-8-sig"), delimiter=";"))
urls = sorted({r["url_foto"] for r in righe if r["url_foto"]})
nome_file = {}
for u in urls:
    nome_file[u] = os.path.basename(urllib.parse.urlparse(u).path)
assert len(set(nome_file.values())) == len(nome_file), "nomi file duplicati"

ko = []
for i, u in enumerate(urls, 1):
    dest = os.path.join(FILES, nome_file[u])
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        continue
    rich = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (compatible; db-serio-foto)"})
    try:
        dati = urllib.request.urlopen(rich, timeout=30).read()
        if dati[:3] != b"\xff\xd8\xff" and dati[:4] != b"\x89PNG" and dati[:4] != b"RIFF":
            raise ValueError("non e' un'immagine")
        open(dest, "wb").write(dati)
    except Exception as e:
        ko.append((u, str(e)))
    if i % 25 == 0:
        print(i, "/", len(urls), "errori", len(ko), flush=True)
    time.sleep(0.5)

mappa = {}
for r in righe:
    f = nome_file.get(r["url_foto"])
    if f and os.path.exists(os.path.join(FILES, f)):
        mappa[r["codice_produttore"].strip()] = {"file": "_file/" + f, "url": r["url_foto"], "pagina": r["pagina_prodotto"],
                                                 "affidabilita": r.get("affidabilita_abbinamento") or "alta"}
json.dump(mappa, open(os.path.join(RADICE, "mappa.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
with open(os.path.join(RADICE, "da_scaricare.txt"), "w", encoding="utf-8") as f:
    for u, e in ko:
        f.write(u + "\n")
print("scaricate", len(urls) - len(ko), "su", len(urls), "- codici collegati", len(mappa), "- errori", len(ko))
for u, e in ko[:5]:
    print(" ", u, e)
