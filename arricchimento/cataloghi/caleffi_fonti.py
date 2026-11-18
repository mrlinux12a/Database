# -*- coding: utf-8 -*-
"""Dati di FAMIGLIA presi dalle pagine HTML del produttore (caleffi.com, versione internazionale en-int: la versione italiana
it-it rispondeva "502 Bad Gateway" il 2026-11-18) per il catalogo "Caleffi".

Regole seguite:
  * un fatto vale per un codice solo se la pagina letta elenca quel codice (tabella "Drawings and specifications") e il testo
    di capitolato di ogni codice ripete lo stesso dato (verificato): per questo ogni gruppo ha l'elenco/schema dei codici;
  * ogni pagina e' stata letta DUE volte (prima citazione letterale di "Technical data" / "Product Description", poi conferma
    si'/no con la frase esatta e l'elenco dei codici): solo i fatti confermati entrano;
  * origine `sito`, fonte = indirizzo della pagina; un fatto di sito non sostituisce mai un valore letto nella descrizione.

Letto e NON usato (annotato qui):
  * 527 EST (pagina en-int): e' la versione export, non i 527 del catalogo (tarature diverse) -> niente.
  * 127 Autoflow (pagina 127251CST): niente materiali/pressioni; le connessioni sono di un altro codice -> niente.
  * Discal 551 (pagina 551705): vale solo per i codici 5517xx elencati (551702/03/05/06/16), non per gli altri 551.
  * 838: la pagina elenca solo 838004-838009 e 838104-838109 (non i DN65-DN100 flangiati) e dice "Class A - Group 2" (non
    messo: e' una classificazione di prodotto, non una normativa citata).
  * 592: "PTFE seal on coupling" ha eccezioni segnate con (*) non riconducibili ai codici -> guarnizione non messa.
  * Valvole di sicurezza 311-314/513: loghi ACS, WRAS, PZH solo per alcuni codici (nota "*") -> messo solo CE 2797, presente
    per tutta la serie.
  * Pagina 313/314: temperatura 5-90 °C (non 5-110 come 311/312/513).
"""
import re

from ..comuni import F

U = "https://www.caleffi.com/en-int/"
P_311 = U + "safety-relief-valve-female-connections-311-caleffi-311425"
P_312 = U + "safety-relief-valve-male--female-connections-312-caleffi-312425"
P_313 = U + "safety-relief-valve-female-connections-with-pressure-gauge-313-caleffi-313425"
P_314 = U + "safety-relief-valve-male--female-connections-with-pressure-gauge-314-caleffi-314425"
P_513 = U + "safety-relief-valve-female-connections-513-caleffi-513415"
P_5350H = U + "pressure-reducing-valve-with-self-contained-replaceable-cartridge-5350h-caleffi-535041h"
P_551 = U + "brass-deaerator-551-caleffi-551705"
P_838 = U + "solenoid-valve-for-gas-normally-closed-838-caleffi-838004"
P_592 = U + "modular-single-distribution-manifold-male-%26nbsp%3B-o-utlet-connections--592-caleffi-592525"


def _sicurezza(temp, fonte):
    return [("pn", "PN10", 10.0, "PN", fonte), ("temperatura", temp + " °C (fluido)", None, "°C", fonte),
            ("normativa", "CE 2797", None, None, fonte)]


# (regex sul codice fornitore, [(chiave, valore, num, unita, fonte)])
FATTI = [
    (r"^311[45]\d\d$", _sicurezza("5÷110", P_311)),
    (r"^3124(25|28|30|35|40|50|60|70|80)$", _sicurezza("5÷110", P_312)),
    (r"^313(425|430|432|460|470|480|525|530|532|560|570|580)$", _sicurezza("5÷90", P_313)),
    (r"^3144(25|30|60|70|80)$", _sicurezza("5÷90", P_314)),
    (r"^5134(15|20|25|30|35|60|70|80)$", _sicurezza("5÷110", P_513)),
    (r"^5350[4-9][01]H$", [
        ("materiale", "ottone resistente alla dezincificazione DR (basso tenore di piombo)", None, None, P_5350H),
        ("campo_regolazione", "1÷6 bar", None, "bar", P_5350H),
        ("temperatura", "2÷80 °C (fluido)", None, "°C", P_5350H),
        ("pressione", "25 bar (a monte)", 25.0, "bar", P_5350H),
        ("normativa", "EN 1567", None, None, P_5350H)]),
    (r"^5517(02|03|05|06|16)$", [
        ("materiale", "ottone", None, None, P_551),
        ("temperatura", "0÷110 °C (fluido)", None, "°C", P_551),
        ("pressione", "10 bar", 10.0, "bar", P_551)]),
    (r"^838[01]0[4-9]$", [
        ("grado_ip", "IP65", 65.0, "IP", P_838),
        ("pressione", "360 mbar", 0.36, "bar", P_838)]),
    (r"^592(525|535|545|625|635|645|626|636|646|726|736|746|622|632)$", [
        ("pressione", "10 bar", 10.0, "bar", P_592),
        ("temperatura", "-10÷110 °C (fluido)", None, "°C", P_592)]),
]
_FATTI = [(re.compile(rx), fatti) for rx, fatti in FATTI]


def integra(cod, descr, nome, at):
    codice = cod.strip().upper()
    for rx, fatti in _FATTI:
        if rx.match(codice):
            for chiave, valore, num, unita, fonte in fatti:
                if chiave not in at:
                    at[chiave] = F(valore, "sito", num, unita, fonte)
            break
    return nome, at
