# -*- coding: utf-8 -*-
"""nomeV2 = nomeV1 senza le informazioni che l'articolo ha gia' come attributo (dimensioni, Ø, attacchi, colore, tensione...).
Si toglie dal nome una informazione SOLO se l'attributo corrispondente esiste per quell'articolo."""
import re

N = r"\d+(?:[.,]\d+)?"
# (attributi che autorizzano la rimozione, espressione da togliere)
REGOLE = [
    ({"attacco", "n_derivazioni"}, r"\b\d+ attacch?[oi]\b(?:\s*Ø\d+(?:[/-]\d+)?)?(?:\s+(?:posteriore|laterale|superiore|inferiore|frontale))?"),
    ({"n_derivazioni"}, r"\b\d+ stacch[io]\b(?:\s*Ø\d+)?"),
    ({"diametro", "attacco"}, r"\b\d+\s*x\s*Ø\d+"),
    ({"diametro", "attacco"}, r"Ø\d+(?:[/-]\d+)?"),
    ({"dimensioni", "altezza", "lunghezza", "spessore"}, r"\b%s\s*x\s*%s(?:\s*x\s*%s)?\s*mm\b" % (N, N, N)),
    ({"dimensioni", "altezza", "lunghezza", "spessore"}, r"\b%s\s*mm\b" % N),
    ({"comando"}, r"(?<!\w)comando(?!\w)(?=\s*(?:,|$))"),
    ({"feritoie"}, r"\b\d+ feritoi[ae]\b"),
    ({"colore"}, r"\b(?:bianc[oa]|ner[oa]|grigi[oa])\b(?:\s*RAL\s*\d+)?"),
    ({"tensione"}, r"\b%s\s*V\b(?:\s*(?:AC/DC|AC|DC))?" % N),
    ({"coppia"}, r"\b%s\s*Nm\b" % N),
    ({"peso"}, r"\b%s\s*(?:kg|g)\b" % N),
    ({"temperatura", "taratura"}, r"\b%s\s*°C\b" % N),
    ({"portata"}, r"\b%s(?:\s*[–-]\s*%s)?\s*m³/h\b" % (N, N)),
    ({"confezione"}, r"\(?\s*confezione minima \d+ pz\s*\)?"),
    ({"confezione"}, r"\brotolo da \d+ m\b|\bal metro\b|\(\s*\d+ pz\s*\)"),
]
_REGOLE = [(k, re.compile(r, re.I)) for k, r in REGOLE]


def pulisci(nome, attrs):
    """attrs: {chiave: {"valore": ...}}  ->  nomeV2"""
    s = nome
    # il valore dell'attributo scritto cosi' com'e' nel nome
    for chiave in ("installazione", "compatibilita"):
        v = attrs.get(chiave, {}).get("valore")
        if v:
            s = re.sub(r"\bper\s+" + re.escape(v), "", s, flags=re.I)
    for chiave in ("finitura", "materiale", "comando"):
        v = attrs.get(chiave, {}).get("valore")
        if v:
            for pezzo in re.split(r",\s*", v):
                if len(pezzo) > 2:
                    s = re.sub(r"(?<!\w)" + re.escape(pezzo) + r"(?!\w)", "", s, flags=re.I)
    for k, rx in _REGOLE:
        if k & attrs.keys():
            s = rx.sub("", s)
    s = re.sub(r"\(\s*\)", "", s)
    s = re.sub(r"\s+([,;])", r"\1", s)
    s = re.sub(r"([,;])(\s*[,;])+", r"\1", s)
    s = re.sub(r"\s{2,}", " ", s)
    s = re.sub(r"^[\s,;+\-–]+|[\s,;+\-–]+$", "", s)
    s = re.sub(r"(?:\s+(?:con|senza|per|di|e|a|da|in|del))+$", "", s, flags=re.I)
    s = re.sub(r"[\s,;+\-–]+$", "", s)
    if not re.search(r"[^\W\d_]{4,}", s):          # non e' rimasto un nome: meglio tenere nomeV1
        return nome
    return s[:1].upper() + s[1:]
