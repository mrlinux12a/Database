"""Legge le schede prodotto italiane (https://www.aircontrolclima.it/it/p/...) e le salva in aircontrolclima_it/pagine.json.

Fonte: sito ufficiale del produttore (Air Control Srl). Rispetta robots.txt (che non vieta /it/p/), pausa tra le richieste
(0,6 s) e User-Agent generico. Le pagine da leggere si ricavano dalla sitemap del sito.

Uso:  py -3.15 fonti/scrape_aircontrolclima.py
Per ogni scheda salva: titolo, serie, schemi di codice (campo "Codice"), categoria, testo della descrizione/dettagli tecnici
e i link ai documenti collegati (scheda commerciale, scheda tecnica, manuale, dimensionali) - i PDF NON vengono scaricati.
"""
import html
import json
import os
import re
import sys
import time

import requests

SITE = "https://www.aircontrolclima.it/"
UA = {"User-Agent": "Mozilla/5.0 (compatible; catalogo-research/1.0)"}
USCITA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aircontrolclima_it", "pagine.json")


def testo(frag):
    frag = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", "", frag)
    frag = re.sub(r"(?i)<br\s*/?>", "\n", frag)
    frag = re.sub(r"(?i)</(p|div|li|tr|h\d|ul|ol|table)>", "\n", frag)
    frag = re.sub(r"(?i)</t[dh]>", " | ", frag)
    frag = re.sub(r"<[^>]+>", "", frag)
    frag = html.unescape(frag).replace("\xa0", " ")
    righe = [re.sub(r"[ \t]+", " ", r).strip() for r in frag.split("\n")]
    out, vuote = [], 0
    for r in righe:
        if not r:
            vuote += 1
            if vuote > 1:
                continue
        else:
            vuote = 0
        out.append(r)
    return "\n".join(out).strip()


def analizza(h, url):
    d = {"url": url}
    m = re.search(r'(?is)<h1[^>]*class="article__heading[^"]*"[^>]*>(.*?)</h1>', h)
    d["titolo"] = testo(m.group(1)) if m else None
    m = re.search(r'(?is)<div class="project-designer__title[^"]*">(.*?)</div>', h)
    d["serie"] = testo(m.group(1)) if m else None
    d["breadcrumb"] = [testo(c) for c in re.findall(r'(?is)<span itemprop="name">(.*?)</span>', h)]
    meta = {}
    for t, v in re.findall(r'(?is)project-meta__item-title">(.*?)</div>\s*<div class="project-meta__item-text">(.*?)</div>', h):
        meta[testo(t).rstrip(":")] = testo(v)
    d["meta"] = meta
    i = h.find('class="article__main')
    j = h.find("</article>", i)
    corpo = h[i:j] if i >= 0 else ""
    d["docs"] = [{"testo": testo(t), "href": a}
                 for a, t in re.findall(r'(?is)<a href="([^"]*(?:qr\.php|download\.php|\.pdf)[^"]*)"[^>]*>(.*?)</a>', corpo)]
    d["testo"] = testo(re.sub(r'(?is)<h4 class="mb-3">Documenti</h4>.*', "", corpo))
    return d


def url_prodotti():
    """Indirizzi delle schede: quelli della sitemap + quelli linkati dalle pagine categoria (alcune schede nuove non sono in sitemap)."""
    sitemap = requests.get(SITE + "sitemap.xml", headers=UA, timeout=30).text
    urls = set(re.findall(r"<loc>([^<]*/it/p/[^<]*)</loc>", sitemap))
    cat = set(re.findall(r"<loc>([^<]*/it/c/[^<]*)</loc>", sitemap))
    home = requests.get(SITE + "it/prodotti.html", headers=UA, timeout=30).text
    cat |= {SITE + c for c in re.findall(r'href="(it/c/\d+/[^"]+)"', home)}
    for c in sorted(cat):
        h = requests.get(c, headers=UA, timeout=30).text
        urls |= {SITE + p for p in re.findall(r'href="(?:https://www\.aircontrolclima\.it/)?(it/p/\d+/[^"]+)"', h)}
        time.sleep(0.6)
    return sorted(urls, key=lambda u: int(re.search(r"/it/p/(\d+)/", u).group(1)))


def main():
    solo_nuovi = "--solo-nuovi" in sys.argv       # non rilegge le schede gia' presenti in pagine.json
    out = json.load(open(USCITA, encoding="utf-8")) if solo_nuovi and os.path.exists(USCITA) else {}
    urls = [u for u in url_prodotti() if re.search(r"/it/p/(\d+)/", u).group(1) not in out]
    print(len(urls), "schede da leggere")
    for n, u in enumerate(urls, 1):
        mid = re.search(r"/it/p/(\d+)/", u).group(1)
        r = requests.get(u, headers=UA, timeout=30)
        r.encoding = "utf-8"
        out[mid] = analizza(r.text, u)
        time.sleep(0.6)
        if n % 25 == 0:
            print(n, "/", len(urls), flush=True)
    os.makedirs(os.path.dirname(USCITA), exist_ok=True)
    with open(USCITA, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("salvato", USCITA, len(out), "schede")


if __name__ == "__main__":
    sys.exit(main())
