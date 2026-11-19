"""Foto Aquatechnik: aquatechnik.it ha una foto per FAMIGLIA di tubo (pagine https://www.aquatechnik.it/prodotto/...),
non per codice e non per la raccorderia (solo foto di categoria, che non si usano). Qui si collega la foto della
pagina del tubo ai codici del catalogo che sono quel tubo (dal nomeV1). Affidabilita' "media": e' la foto di famiglia,
non dell'articolo. Scrive foto/Aquatechnik/mappa.json (+ _file/). Pausa 0,5 s tra le richieste, User-Agent generico.
Fonte immagini: pagina https://www.aquatechnik.it/sistemi-in-polipropilene/ (letta il 2026-11-19)."""
import json, os, re, time, urllib.request
import psycopg2

BASE = "https://cdn.aquatechnik.it/wp-content/uploads/"
# (espressione sul nomeV1, immagine, pagina del prodotto)
FAMIGLIE = [
    (r"tubo faser fiber-t\b(?!.*fires)", "2020/01/FUSIO-TECHNIK-faser-FIBER-T-SDR-74.jpg", "faser-fiber-t-sdr-74"),
    (r"tubo faser fiber-cond", "2020/01/FUSIO-TECHNIK-faser-FIBER-COND-SDR-11.jpg", "faser-fiber-cond-sdr-11"),
    (r"tubo faser fiber-light", "2020/01/FUSIO-TECHNIK-faser-FIBER-LIGHT-SDR-176.jpg", "faser-fiber-light-sdr-176"),
    (r"(tubo faser uvres|faser uvres tubo)", "2020/01/FUSIO-TECHNIK-UVRES-SDR-74-e-11-1.jpg", "faser-uvres-sdr-74-e-11"),
    (r"^(fusio-technik )?tubo faser fires", "2020/01/FUSIO-TECHNIK-FIRES-SDR-74-e-11.jpg", "faser-fires-sdr-74-e-11"),
    (r"tubo rain-water", "2019/11/FUSIO-TECHNIK-RAINWATER-SDR-11.jpg", "rainwater-sdr-11"),
    (r"tubo pp-r sdr 6\b", "2019/11/FUSIO-TECHNIK-SDR-6.jpg", "fusio-technik-sdr-6"),
]

RADICE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "foto", "Aquatechnik")
os.makedirs(os.path.join(RADICE, "_file"), exist_ok=True)
cur = psycopg2.connect(dbname=os.environ.get("PGDATABASE", "db_serio_finale"), user=os.environ.get("PGUSER", "postgres"),
                       host=os.environ.get("PGHOST", "localhost")).cursor()
cur.execute("select cod_fornitore, nomev1 from materiale where catalogo='Aquatechnik'")
mappa, scaricate = {}, set()
for cod, nome in cur.fetchall():
    for regex, img, pagina in FAMIGLIE:
        if re.search(regex, nome.lower()):
            nomefile = os.path.basename(img)
            dest = os.path.join(RADICE, "_file", nomefile)
            if nomefile not in scaricate:
                if not os.path.exists(dest):
                    rich = urllib.request.Request(BASE + img, headers={"User-Agent": "Mozilla/5.0 (compatible; db-serio-foto)"})
                    open(dest, "wb").write(urllib.request.urlopen(rich, timeout=30).read())
                    time.sleep(0.5)
                scaricate.add(nomefile)
            mappa[cod] = {"file": "_file/" + nomefile, "url": BASE + img, "pagina": "https://www.aquatechnik.it/prodotto/" + pagina + "/",
                          "affidabilita": "media"}
            break
json.dump(mappa, open(os.path.join(RADICE, "mappa.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("codici con foto:", len(mappa), "- foto:", len(scaricate))
