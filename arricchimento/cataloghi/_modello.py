# -*- coding: utf-8 -*-
"""MODELLO per un catalogo nuovo.  Copia questo file con il nome del catalogo (vedi __init__.py: "Acme SRL" -> acme_srl.py)
e riempilo.  Parti da `generico`, poi aggiungi le regole del catalogo: sigle, abbreviazioni, formato dei codici.

Regole che valgono sempre (dettagli in CLAUDE.md):
  * un valore entra SOLO se e' scritto nella descrizione / nel codice / in una fonte che hai letto; mai valori inventati;
  * ogni valore ha la sua `origine` (descrizione | codice | sito | web) e, per sito/web, la `fonte` (indirizzo della pagina);
  * dove non sai, non mettere niente (nessuna riga) e lascia il testo cosi' com'e' nel nome.
"""
from ..comuni import F, frase
from . import generico

ABBREVIAZIONI = [         # (testo come scritto nel catalogo in minuscolo, testo esteso)
    # ("c/", "con"), ("s/", "senza"),
]


def prepara(righe):
    """Facoltativa: chiamata una volta con [(cod_fornitore, descrizione), ...] (es. per imparare i prefissi dei codici)."""


def analizza(cod, descr):
    nome, at = generico.analizza(cod, descr)
    # --- regole specifiche del catalogo qui sotto -------------------------------------------------------------
    return nome, at
