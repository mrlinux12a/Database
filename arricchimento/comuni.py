# -*- coding: utf-8 -*-
"""Piccoli attrezzi comuni a tutti i moduli di catalogo."""
import re

ORIGINI = ("descrizione", "codice", "sito", "web")      # da dove arriva un valore (vedi README)


def F(valore, origine="descrizione", num=None, unita=None, fonte=None):
    """Un valore di attributo nel formato atteso da arricchisci.py."""
    return {"valore": str(valore).strip(), "num": num, "unita": unita, "origine": origine, "fonte": fonte}


def numero(testo):
    """'1.250,5' / '12,5' / '12.5' -> float"""
    t = testo.strip()
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    return float(t)


def it(x):
    """float -> testo all'italiana senza zeri inutili (12.5 -> '12,5', 150.0 -> '150')"""
    return ("%g" % x).replace(".", ",")


def frase(testo):
    """Descrizione da maiuscolo/Title Case a frase: prima lettera maiuscola, sigle e modelli (lettere+cifre) in maiuscolo."""
    parole = []
    for w in testo.split():
        if re.search(r"\d", w) and re.search(r"[A-Za-z]", w):
            parole.append(w.upper())
        elif w.isupper() and 2 <= len(w) <= 4 and not testo.isupper():
            parole.append(w)                                 # sigla scritta in maiuscolo dentro un testo misto
        else:
            parole.append(w.lower())
    s = " ".join(parole)
    return s[:1].upper() + s[1:]
