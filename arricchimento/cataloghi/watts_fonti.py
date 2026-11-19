# -*- coding: utf-8 -*-
"""Dati di famiglia di Watts letti sulle pagine HTML del produttore (watts.eu/it), origine `sito` con la pagina come fonte.
Un fatto vale SOLO per i codici elencati nella tabella della stessa pagina (regola 3 di CLAUDE.md). Letto due volte (2026-11-19),
la seconda con citazione letterale.

Letto e usato:
  VST (valvola di sicurezza a membrana INAIL), 30 codici 0212122…0214160:
    «Corpo e calotta in ottone CW617N.» «PN 10.» «Temperatura di esercizio: -10÷120°C.» «Fluidi: acqua con glicole fino al 50%.»
    «Attacchi FF con uscita maggiorata.» (-> femmina/femmina). «Qualificata e tarata INAIL ex ISPESL» e «PED 2014/68/EU»: INAIL
    c'e' gia' nella descrizione, PED non aggiunto (un valore per attributo).
  MG1-INOX 63, 11 codici PE340114LF…PE354014LF (nel catalogo ce ne sono 10):
    «Manometro a bagno di glicerina DN 63 ad attacco radiale con cassa in acciao inox» «Classe di precisione 1,6.» attacco G1/4B.
    I 4 MG1-INOX 63 con scala 0-160/250/400/600 bar (PE365414LF, PE366014LF, PE366614LF, PE367014LF) NON sono nella tabella:
    niente dati per loro.
Letto e NON usato:
  M1-ABS 63/R (watts.eu …/m1-abs-63-r): «DN 63 … cassa in plastica … Classe di precisione 1,6 … EN 837-1 … INAIL», ma i codici
    della pagina sono PA3101BB02… e quelli del catalogo PZFEA3101BB02…: codici diversi, il fatto non vale.
  ZKB/ZKT (giunti in EPDM): nessuna pagina watts.eu trovata, solo rivenditori: niente.
Non cercato (tempo): le altre famiglie (SV, MSL/MSV, NVFN, VTFN, 296, termometri TB, termostati, gruppi HK).
"""
from ..comuni import F

VST = "https://www.watts.eu/it/products/eu/safety-control-accessories-for-heating/safety-valves/safety-valve-vst"
MG1_INOX_63 = ("https://www.watts.eu/it/products/eu/pressure-gauges-and-thermometers/pressure-gauges/"
               "glycerine-filled-pressure-gauges-for-industrial-applications/mg1-inox-63")

CODICI_VST = {"02121%02d" % n for n in (22, 25, 27, 30, 35, 40, 45, 50, 54, 60)} | \
             {"02131%02d" % n for n in (22, 25, 27, 30, 35, 40, 45, 50, 54, 60)} | \
             {"02141%02d" % n for n in (22, 25, 27, 30, 35, 40, 45, 50, 54, 60)}
CODICI_MG1_INOX_63 = {"PE340114LF", "PE340214LF", "PE350314LF", "PE350414LF", "PE350614LF", "PE351014LF", "PE351214LF",
                      "PE351614LF", "PE352014LF", "PE352514LF", "PE354014LF"}


def integra(cod, attrs):
    """Aggiunge i dati di famiglia (senza toccare quelli letti nella descrizione)."""
    def metti(chiave, valore, num=None, unita=None, fonte=None):
        attrs.setdefault(chiave, F(valore, "sito", num, unita, fonte))
    if cod in CODICI_VST:
        metti("materiale", "ottone CW617N", fonte=VST)
        metti("pn", "PN10", 10.0, "PN", VST)
        metti("temperatura", "-10÷120 °C", fonte=VST)
        metti("fluidi", "acqua con glicole fino al 50%", fonte=VST)
        metti("maschio_femmina", "femmina/femmina", fonte=VST)
    if cod in CODICI_MG1_INOX_63:
        metti("dn", "DN63", 63.0, "DN", MG1_INOX_63)
        metti("materiale", "acciaio inox (cassa)", fonte=MG1_INOX_63)
        metti("accuratezza", "classe 1,6", fonte=MG1_INOX_63)
        metti("filettatura", "G1/4B", fonte=MG1_INOX_63)
    return attrs
