# -*- coding: utf-8 -*-
"""Catalogo "Air Control SRL": regole di lettura delle descrizioni (parse.py), schede del sito del produttore (sito.py)
e dati di terzi trovati sul web (web.py).  E' il catalogo di riferimento: guardalo per vedere come si fa."""
from .. import parse, web


def prepara(righe):
    parse.registra_codici([cod for cod, _ in righe])


def analizza(cod, descr):
    nome, at = parse.analizza(cod, descr)
    return web.integra(cod, descr, nome, at)
