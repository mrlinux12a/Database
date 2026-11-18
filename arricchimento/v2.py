# -*- coding: utf-8 -*-
"""nomeV2 = nomeV1 senza le informazioni che l'articolo ha gia' come attributo (dimensioni, Ø, attacchi, colore, tensione...).
Si toglie dal nome una informazione SOLO se l'attributo corrispondente esiste per quell'articolo."""
import re

N = r"\d+(?:[.,]\d+)?"
# (attributi che autorizzano la rimozione, espressione da togliere)
PARTE_OD = r'\d+(?:[.,]\d+)?(?:/\d+(?:[.,]\d+)?)?(?:"(?:[MF]/[MF]|[MF])?|[MF](?![\w"]))?'   # 63 · 4,2 · 25/3,5 · 1/2" · 2.1/2"M · 1/2"M/F · 23/1,5M
REGOLE = [
    ({"attacco", "n_derivazioni"}, r"\b\d+ attacch?[oi]\b(?:\s*Ø\d+(?:[/-]\d+)?(?![\d\"/.,]))?(?:\s+(?:posteriore|laterale|superiore|inferiore|frontale))?"),
    ({"n_derivazioni"}, r"\b\d+ stacch[io]\b(?:\s*Ø\d+)?"),
    ({"n_derivazioni"}, r"\b\d+(?:[-+]\d+)?\s*(?:uscite|attacchi|derivazioni|circuiti)\b"),
    ({"diametro", "attacco"}, r"\b\d+\s*x\s*Ø\d+"),
    # gruppo Ø intero: Ø63 · Ø63-75 · Ø14÷32 · Ø26x18x26 · Ø1/2"Mx16 · Ø25/3,5 (anche con " mm" dopo)
    ({"diametro", "attacco"}, r"Ø%s(?:[x÷-]%s)*(?:\s?mm\b)?" % (PARTE_OD, PARTE_OD)),
    ({"sdr"}, r"\bSDR\s?\d+(?:[.,]\d+)?"),
    ({"pn"}, r"\bPN\s?\d+(?:/\d+)?\b"),
    ({"lunghezza"}, r"\bbarra da \d+(?:[.,]\d+)? m\b"),
    ({"diametro", "attacco"}, r"Ø\d+(?:[/-]\d+)?"),
    ({"dimensioni", "altezza", "lunghezza", "spessore"}, r"\b%s\s*x\s*%s(?:\s*x\s*%s)?\s*mm\b" % (N, N, N)),
    ({"dimensioni", "altezza", "lunghezza", "spessore"}, r"\b%s\s*mm\b" % N),
    ({"comando"}, r"(?<!\w)comando(?!\w)(?=\s*(?:,|$))"),
    ({"feritoie"}, r"\b\d+ feritoi[ae]\b"),
    ({"colore"}, r"\b(?:bianc[oa]|ner[oa]|grigi[oa])\b(?:\s*RAL\s*\d+)?"),
    ({"colore"}, r"\b(?:giall[oa]|verde|blu|ross[oa]|azzurr[oa])\b"),
    ({"tensione"}, r"(?<!\d[-–÷])\b%s\s*V\b(?:\s*(?:AC/DC|AC|DC))?" % N),     # non il segnale "0-10 V"
    ({"dn"}, r"\bDN\s?\d+(?:\s*[÷/-]\s*(?:DN)?\s?\d+)?\b"),
    ({"pressione", "taratura", "campo_regolazione"}, r"\b%s(?:\s*÷\s*%s)?\s*(?:bar|mbar|kPa|m c\.a\.)(?!\w)" % (N, N)),
    ({"campo_regolazione"}, r"\b%s\s*÷\s*%s\s*°C\b" % (N, N)),
    ({"potenza"}, r"\b%s\s*(?:kW|W|VA)\b" % N),
    ({"frequenza"}, r"\b%s\s*Hz\b" % N),
    ({"portata"}, r"\b%s(?:\s*÷\s*%s)?\s*(?:l/min|l/h)(?!\w)" % (N, N)),
    ({"volume_acqua"}, r"\b%s\s*l\b(?![/'])" % N),
    ({"coibentazione"}, r"\b(?:con coibentazione|coibentat[oaie])\b"),
    ({"vie"}, r"\b\d(?:[/-]\d)?\s*vie\b"),
    ({"interasse"}, r"\binterasse\s+%s\s*mm\b" % N),
    ({"spessore"}, r"\bspessore\s+%s\s*mm\b" % N),
    ({"lunghezza"}, r"\blunghezza\s+%s\s*m?m\b" % N),
    ({"lunghezza_cavo"}, r"\bcavo\s+%s\s*m\b" % N),
    ({"maschio_femmina"}, r"\b(?:maschio|femmina)\s+(?:maschio|femmina)\b"),
    ({"coppia"}, r"\b%s\s*Nm\b" % N),
    ({"peso"}, r"\b%s\s*(?:kg|g)\b" % N),
    ({"temperatura", "taratura"}, r"\b%s\s*°C\b" % N),
    ({"portata"}, r"\b%s(?:\s*[–÷-]\s*%s)?\s*m³/h(?!\w)" % (N, N)),
    ({"confezione"}, r"\(?\s*confezione minima \d+ pz\s*\)?"),
    ({"confezione"}, r"\brotolo da \d+ m\b|\bal metro\b|\(\s*\d+ pz\s*\)"),
]
_REGOLE = [(k, re.compile(r, re.I)) for k, r in REGOLE]


def pulisci(nome, attrs):
    """attrs: {chiave: {"valore": ...}}  ->  nomeV2"""
    s = nome
    # il valore dell'attributo scritto cosi' com'e' nel nome
    for chiave in ("installazione", "compatibilita", "fluidi"):
        v = attrs.get(chiave, {}).get("valore")
        if v:
            s = re.sub(r"\bper\s+" + re.escape(v), "", s, flags=re.I)
    for chiave in ("finitura", "materiale", "comando", "tipo_base", "maschio_femmina", "tipo_raccordo", "installazione",
                   "confezione", "guarnizione", "scarico", "normativa", "fluidi"):
        v = attrs.get(chiave, {}).get("valore")
        if chiave == "tipo_base" and attrs.get(chiave, {}).get("origine") != "descrizione":
            continue                      # la gamma letta dalla scheda del sito e' un nome di prodotto: non si toglie dal nome
        if v:
            for pezzo in re.split(r",\s*", v):
                if len(pezzo) > 2:
                    prima = r"(?:\b(?:in|con|tenuta)\s+)?" if chiave in ("materiale", "guarnizione") else ""
                    s = re.sub(prima + r"(?<!\w)" + re.escape(pezzo) + r"(?!\w)", "", s, flags=re.I)
    for k, rx in _REGOLE:
        if k & attrs.keys():
            s = rx.sub("", s)
    s = re.sub(r"\b(?:in|di|con|e|da|a)\s+(?=(?:per|con|in|di|da)\b)", "", s, flags=re.I)   # preposizione rimasta sola ("in per")
    s = re.sub(r"\(\s*\)", "", s)
    s = re.sub(r"\s+([,;])", r"\1", s)
    s = re.sub(r"([,;])(\s*[,;])+", r"\1", s)
    s = re.sub(r"\s{2,}", " ", s)
    s = re.sub(r"^[\s,;+\-–]+|[\s,;+\-–]+$", "", s)
    s = re.sub(r"(?:\s+(?:con|senza|per|di|e|a|da|in|del))+$", "", s, flags=re.I)
    s = re.sub(r"[\s,;+\-–]+$", "", s)
    if not re.search(r"[^\W\d_]{3,}", s):          # non e' rimasto un nome: meglio tenere nomeV1
        return nome
    return s[:1].upper() + s[1:]
