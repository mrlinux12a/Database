# -*- coding: utf-8 -*-
"""Un modulo per catalogo: arricchimento/cataloghi/<nome>.py, dove <nome> e' il nome del file CSV (colonna `catalogo`
di materiale) in minuscolo, con i caratteri non alfanumerici sostituiti da "_"   ("Air Control SRL" -> air_control_srl).

Ogni modulo espone:
    analizza(cod_fornitore, descrizione) -> (nomev1, {chiave_attributo: {"valore", "num", "unita", "origine", "fonte"}})
e, se serve:
    prepara(righe)      # chiamata una volta prima del ciclo, con la lista [(cod_fornitore, descrizione), ...]
    VUOLE_RIGA = True   # allora analizza(cod, descrizione, riga) riceve anche `riga` = {"linea", "serie", "sigla", "marca", "um"}
                        # (le altre colonne del CSV: servono quando la descrizione da sola non basta, es. la gamma e' nella Linea)

Se il modulo del catalogo non esiste si usa `generico` (regole di base) e il programma lo dice.
Per un catalogo nuovo: copia `_modello.py` con il nome giusto e aggiungi le regole.
"""
import importlib
import re


def slug(catalogo):
    return re.sub(r"[^a-z0-9]+", "_", catalogo.lower()).strip("_")


COLONNE_RIGA = ("linea", "serie", "sigla", "marca", "um")        # colonne di `materiale` passate ai moduli che le vogliono


def analizza(modulo, cod, descr, riga):
    """Chiama modulo.analizza: con `riga` (colonne del CSV) solo se il modulo ha VUOLE_RIGA = True, cosi' i moduli vecchi
    (come Air Control) continuano a funzionare identici."""
    if getattr(modulo, "VUOLE_RIGA", False):
        return modulo.analizza(cod, descr, riga)
    return modulo.analizza(cod, descr)


def carica(catalogo):
    """-> (modulo, nome del modulo usato)"""
    nome = slug(catalogo)
    try:
        return importlib.import_module("%s.%s" % (__name__, nome)), nome
    except ModuleNotFoundError as e:
        if e.name != "%s.%s" % (__name__, nome):
            raise                      # un errore dentro il modulo, non un modulo mancante
        return importlib.import_module("%s.generico" % __name__), "generico"
