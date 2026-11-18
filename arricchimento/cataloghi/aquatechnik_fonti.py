# -*- coding: utf-8 -*-
"""Dati di FAMIGLIA presi dalle pagine HTML del catalogo online del produttore (Aquatechnik, pinaxo.com), origine `sito`.
Letti nel novembre 2026, solo pagine HTML (nessun PDF scaricato). Ogni valore porta la pagina in `fonte`.

Regola: un valore vale per un articolo solo se la pagina lo dice per QUELLA famiglia e l'articolo e' di quella famiglia
(i tubi "Fiber-T", "Fiber-Cond", ... non sono i raccordi). Mai sovrascritto un valore gia' presente nella descrizione;
se la descrizione e la scheda dicono cose diverse il valore della scheda NON entra.

Pagine lette
  FT/8   Curva di regressione ISO 9080 (PP-R 80 Super, PP-RCT, tubi faser a 3 strati)
  FT/17  faser FIBER-T      FT/19  faser FIBER-COND   FT/21  faser FIBER-LIGHT   FT/23  UVRES   FT/25  FIRES (tubi)
  FT/29  raccorderia FIRES ("Caratteristiche tecniche e Marcatura"; letta due volte, stesso risultato)
  SF/16  tubi multi-calor rivestiti con guaina corrugata       SF/42  caratteristiche tecniche Safety / Isoline
Pagine senza dati per famiglia: FT/27 (tabella delle applicazioni dei tubi, con "acqua piovana" ma senza materiale, colore,
SDR...), FT/30 (caratteristiche generali del sistema: conduttivita' termica, ciclo di vita; le tabelle di pressione e
temperatura sono grafiche e non si leggono nell'HTML).
Non trovate (nessun dato): Rain-Water, raccordi Safety-Plus (pressione/temperatura), Superflux (non presente nel catalogo).
Non inserito perche' dubbio: temperatura/pressione di esercizio dei tubi faser (la pagina rimanda a tabelle non lette);
Fiber-T con "Fires" nel nome (non e' chiaro a quale scheda appartiene); "NON IDONEO AL TRASPORTO DI ACQUA POTABILE" dei raccordi
Fires (e' una negazione: un attributo `fluidi` con quel testo uscirebbe nelle ricerche per "acqua potabile"); SDR 5 dei raccordi
Fires (la pagina dice "salvo eccezioni": entra solo quando e' scritto nella descrizione); lambda 0,22 / 0,19 W/mK (nessun
attributo adatto).
Valori contraddittori: il collare Fires ha SDR 7,4 nella descrizione, la pagina dice SDR 5 per i raccordi (salvo eccezioni):
vale la descrizione.
"""
import re

from ..comuni import F

FT = "https://bertani.pinaxo.com/public/3211fc0163c15d6eb9fe5c103264dc85/aquatechnik-fusio-technik/"
SF = "https://bertani.pinaxo.com/public/5bd03bc1be395e5374c346374e81a5fa/aquatechnik-safety-safetyplus/"

STRATI_FAISER = "PP-RCT WOR/PP-RF/PP-R"          # strato interno / intermedio fibrorinforzato / esterno


def _metti(at, chiave, valore, fonte, num=None, unita=None):
    if chiave not in at:                                           # mai sovrascrivere la descrizione
        at[chiave] = F(valore, "sito", num, unita, fonte)


def _sdr_coerente(at, sdr):
    """True se Ø / spessore dell'articolo e' compatibile con l'SDR della scheda (o se non si puo' verificare)."""
    d, e = at.get("diametro", {}).get("num"), at.get("spessore", {}).get("num")
    if not d or not e:
        return True
    return abs(d / e - sdr) / sdr <= 0.08


def integra(cod, descr, nome, at):
    d = " " + descr.lower() + " "
    tubo = bool(re.match(r"^(?:\S+\s+){0,3}tubo\b", descr, re.I))
    diam = at.get("diametro", {}).get("num")
    if tubo and re.search(r"\bfiber-t\b", d) and not re.search(r"\bfires\b", d):
        f = FT + "17"
        _metti(at, "materiale", STRATI_FAISER, f)
        if diam:
            _metti(at, "colore", "strato interno bianco, strato esterno verde con strisce rosse" if diam <= 125
                   else "strato interno bianco, strato esterno bianco con strisce rosse", f)
        _metti(at, "fluidi", "acqua potabile", f)
    elif tubo and re.search(r"\bfiber-cond\b", d):
        f = FT + "19"
        _metti(at, "materiale", STRATI_FAISER, f)
        _metti(at, "colore", "strato interno bianco, strato esterno bianco con strisce grigie", f)
        if _sdr_coerente(at, 11):
            _metti(at, "sdr", "SDR 11", f, 11.0, "SDR")
        _metti(at, "fluidi", "acqua potabile", f)
    elif tubo and re.search(r"\bfiber-light\b", d):
        f = FT + "21"
        _metti(at, "materiale", STRATI_FAISER, f)
        _metti(at, "colore", "strato interno bianco, strato esterno bianco con strisce verdi", f)
        if _sdr_coerente(at, 17.6):
            _metti(at, "sdr", "SDR 17,6", f, 17.6, "SDR")
        _metti(at, "fluidi", "acqua potabile a bassa temperatura", f)
    elif tubo and re.search(r"\buvres\b", d):
        f = FT + "23"
        _metti(at, "materiale", STRATI_FAISER, f)
        _metti(at, "colore", "strato interno bianco, strato esterno nero", f)
        _metti(at, "fluidi", "acqua potabile", f)
    elif tubo and re.search(r"\bfires\b", d) and not re.search(r"\bfiber-t\b", d):
        f = FT + "25"
        _metti(at, "materiale", "PP-R/PP-RF/PP-R", f)
        _metti(at, "colore", "strato interno ed esterno rossi", f)
    elif (not tubo and re.search(r"\bfires\b", d)
          and not re.search(r"\b(?:fiber-t|safety|valvola|rubinetto)\b", d)):          # raccorderia FIRES (FT/29)
        f = FT + "29"
        filettato = bool(re.search(r'\d"', descr))
        if filettato or (diam and diam <= 125):                      # "fino a Ø 125 mm: rosso (inserto in ottone se filettati)"
            _metti(at, "colore", "rosso", f)
        _metti(at, "normativa", "DAU ITeC (rif. EN 12845)", f)
        if filettato:
            _metti(at, "filettatura", "ISO 228", f)                  # "Realizzate secondo la normativa ISO 228"
    if tubo and re.search(r"\bmulti-calor\b", d) and re.search(r"\bisoline(?:-plus)?\b", d):
        f = SF + "42"
        _metti(at, "coibentazione", "polietilene espanso a celle chiuse", f)
        _metti(at, "temperatura", "da -45 °C a +95 °C", f, None, "°C")
    if tubo and re.search(r"\bmulti-calor\b", d) and re.search(r"\bcorrugato\b", d):
        f = SF + "16"
        _metti(at, "pressione", "10 bar", f, 10.0, "bar")
        _metti(at, "normativa", "EN ISO 21003", f)
        _metti(at, "fluidi", "acqua", f)
    return nome, at
