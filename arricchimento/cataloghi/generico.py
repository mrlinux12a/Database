# -*- coding: utf-8 -*-
"""Regole di base, valide per qualunque catalogo: servono come punto di partenza.
Legge dalla descrizione le misure e i dati numerici piu' comuni; il nome e' la descrizione ripulita (maiuscole)."""
import re

from ..comuni import F, frase, it, numero

N = r"(\d+(?:[.,]\d+)?)"
REGOLE = [   # (attributo, espressione, funzione(match) -> (testo, num, unita))
    ("dimensioni", r"\b%s\s*[xX×]\s*%s(?:\s*[xX×]\s*%s)?\s*(mm|cm)\b" % (N, N, N),
     lambda m: (" x ".join(it(numero(g)) for g in m.groups()[:3] if g) + " " + m.group(4), None, None)),
    ("diametro", r"[Ø⌀]\s*%s\s*(mm)?" % N, lambda m: (it(numero(m.group(1))) + " mm", numero(m.group(1)), "mm")),
    ("dn", r"\bDN\s?(\d+)\b", lambda m: ("DN" + m.group(1), float(m.group(1)), "DN")),
    ("pn", r"\bPN\s?(\d+)\b", lambda m: ("PN" + m.group(1), float(m.group(1)), "PN")),
    ("tensione", r"\b%s\s*V\b" % N, lambda m: (it(numero(m.group(1))) + " V", numero(m.group(1)), "V")),
    ("potenza", r"\b%s\s*(kW|W)\b" % N, lambda m: (it(numero(m.group(1))) + " " + m.group(2), numero(m.group(1)), m.group(2))),
    ("pressione", r"\b%s\s*(bar|psi)\b" % N, lambda m: (it(numero(m.group(1))) + " " + m.group(2), numero(m.group(1)), m.group(2))),
    ("peso", r"\b%s\s*kg\b" % N, lambda m: (it(numero(m.group(1))) + " kg", numero(m.group(1)), "kg")),
    ("temperatura", r"%s\s*°\s*C\b" % N, lambda m: (it(numero(m.group(1))) + " °C", numero(m.group(1)), "°C")),
    ("portata", r"\b%s\s*(m³/h|m3/h|l/s|l/min)" % N,
     lambda m: (it(numero(m.group(1))) + " " + m.group(2).replace("m3", "m³"), numero(m.group(1)), m.group(2).replace("m3", "m³"))),
]
_REGOLE = [(k, re.compile(r, re.I), f) for k, r, f in REGOLE]


def analizza(cod, descr):
    at = {}
    for chiave, rx, f in _REGOLE:
        m = rx.search(descr)
        if m:
            testo, num, unita = f(m)
            at[chiave] = F(testo, "descrizione", num, unita)
    return frase(" ".join(descr.split())), at
