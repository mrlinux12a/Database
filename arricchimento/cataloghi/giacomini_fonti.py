# -*- coding: utf-8 -*-
"""Dati di famiglia di Giacomini letti sulle pagine HTML del produttore (it.giacomini.com/prodotto/<modello>), origine `sito`
con la pagina come fonte. Un fatto vale SOLO per i codici elencati nella tabella della stessa pagina (regola 3 di CLAUDE.md).
Letto due volte (2026-11-20), la seconda con controllo della frase letterale. Nessun PDF scaricato (le schede tecniche PDF
dam.giacomini.com non sono state aperte: servirebbe il permesso dell'utente).

Letto e usato (citazioni letterali):
  R250D  «Valvola a sfera, in ottone cromato, con attacchi femmina-femmina.» «Campo di temperatura -20÷185 °C.» «Campo di
         temperatura con idrocarburi liquidi -20÷60 °C.» «Per impianti idraulici e idrocarburi liquidi.» Tabella «G 1/2"F»…
         codici R250X001…R250X011.
  R910   «… in ottone nichelato, con attacchi femmina-femmina.» stesse temperature e fluidi; codici R910X022…R910X031.
  R850   «… in ottone cromato …» stesse temperature e fluidi; codici R850X021…R850X031.
  R999   «Tubo multistrato metallo-plastico PEX-b/Al/PEX-b.»; codici R999Y122…R999GY190.
  R553FK «Kit collettore premontato in ottone …» «Pressione massima di esercizio 10 bar.» «Campo di temperatura 5÷110 °C.»
         «Interasse tra le uscite 50 mm.»; codici R553FK102…R553FK112.
  R18    «In ottone.» «Pressione massima di esercizio 10 bar.» «Campo di temperatura: 5÷160 °C per misure 3/8”, 1/2”, 3/4”, 1”,
         1-1/4”; 5÷110 °C per misure 1-1/2”, 2”.» Codici R18Y002…R18Y008, R18Y017, R18Y018 (non cromati). La temperatura NON
         e' messa a R18Y007/R18Y008 (filetto «Rc 1-1/2” x R 1-1/2”», «Rc 2” x R 2”»: la pagina non dice se vale anche per loro).
         I bocchettoni «Cig Uni 7129» (R18Y063…065, R19…) non sono nella tabella: niente dati.
  R551   «Collettore di distribuzione in ottone, con attacchi filettati femmina.» «Pressione massima di esercizio 16 bar.»
         «Campo di temperatura 5÷110 °C.»; 76 codici R551Y002…R551Y192. L'interasse della pagina («Da R551Y002 a R551Y012:
         interasse attacchi 35 mm» …) coincide con quello della descrizione per tutti i codici.
  R978   tabelle «Colore rosso» (R978Y272, Y275, Y223, Y226, Y227, Y233, Y235, Y237, Y255, Y256) e «Colore grigio» (R978Y114,
         Y116, Y117). «Tubo in polietilene PE-RT Type II …» (il materiale PE-RT c'e' gia' nella descrizione).
Letto e NON usato:
  R978 «non idoneo al trasporto di acqua potabile» (una negazione non va in un attributo di compatibilita'); «classe di
       applicazione 4»; certificazioni ATG/KIWA KOMO/CSTB (sono nomi di link, non e' detto a quale norma).
  R999 «Classi di applicazione 1, 2, 4 e 5, idoneo per impianti sanitari, di riscaldamento e raffrescamento» (non ha un
       attributo adatto). Pressione e temperatura del R999 sono solo nel PDF: non letto.
  R250D/R910/R850: certificazioni ACS, WRAS, FM, UL GAS (nomi di link, diverse per misura): non usate.
Valori contraddittori (NON inseriti, segnalati):
  R999GY140, R999GY150, R999GY163: la descrizione dice «Barra 25m», la pagina li mette sotto «TUBO IN BARRE DA 5 m»
  (forse 25 m = 5 barre per confezione, ma non e' scritto): la lunghezza di questi tre codici viene tolta.
"""
from ..comuni import F

URL = "https://it.giacomini.com/prodotto/%s"


def _cod(prefisso, numeri, fmt="%03d"):
    return {prefisso + fmt % n for n in numeri}


VALVOLE_FLUIDI = ("fluidi", "impianti idraulici e idrocarburi liquidi", None, None)
VALVOLE_TEMP = ("temperatura", "-20÷185 °C (con idrocarburi liquidi -20÷60 °C)", 185.0, "°C")

FATTI = [   # (insieme di codici fornitore, [(chiave, valore, num, unita)], url)
    (_cod("R250X", range(1, 12)), [("materiale", "ottone", None, None), ("finitura", "cromato", None, None), VALVOLE_TEMP,
                                   VALVOLE_FLUIDI, ("filettatura", "G", None, None)], URL % "R250D"),
    (_cod("R910X", range(22, 32)), [("materiale", "ottone", None, None), ("finitura", "nichelato", None, None), VALVOLE_TEMP,
                                    VALVOLE_FLUIDI, ("filettatura", "G", None, None)], URL % "R910"),
    (_cod("R850X", range(21, 32)), [("materiale", "ottone", None, None), ("finitura", "cromato", None, None), VALVOLE_TEMP,
                                    VALVOLE_FLUIDI, ("filettatura", "G", None, None)], URL % "R850"),
    ({"R999Y122", "R999Y123", "R999Y124", "R999Y142", "R999Y143", "R999Y173", "R999Y183", "R999Y125", "R999Y145", "R999Y174",
      "R999Y184", "R999GY140", "R999GY150", "R999GY163", "R999GY175", "R999GY190"},
     [("materiale", "PEX-b/Al/PEX-b", None, None)], URL % "R999"),
    (_cod("R553FK", range(102, 113)), [("materiale", "ottone", None, None), ("pressione", "10 bar", 10.0, "bar"),
                                       ("temperatura", "5÷110 °C", 110.0, "°C"), ("interasse", "50 mm", 50.0, "mm")],
     URL % "R553FK"),
    (_cod("R18Y", (2, 3, 4, 5, 6, 7, 8, 17, 18)), [("materiale", "ottone", None, None), ("pressione", "10 bar", 10.0, "bar")],
     URL % "R18"),
    (_cod("R18Y", (2, 3, 4, 5, 6)), [("temperatura", "5÷160 °C", 160.0, "°C")], URL % "R18"),
    (_cod("R18Y", (17, 18)), [("temperatura", "5÷110 °C", 110.0, "°C")], URL % "R18"),
    (_cod("R551Y", list(range(2, 13)) + list(range(22, 33)) + list(range(42, 53)) + list(range(62, 73)) +
          list(range(82, 93)) + list(range(102, 107)) + list(range(162, 167)) + list(range(182, 193))),
     [("materiale", "ottone", None, None), ("pressione", "16 bar", 16.0, "bar"), ("temperatura", "5÷110 °C", 110.0, "°C")],
     URL % "R551"),
    (_cod("R978Y", (272, 275, 223, 226, 227, 233, 235, 237, 255, 256)), [("colore", "rosso", None, None)], URL % "R978"),
    (_cod("R978Y", (114, 116, 117)), [("colore", "grigio", None, None)], URL % "R978"),
]
TOGLI = {c: ("lunghezza",) for c in ("R999GY140", "R999GY150", "R999GY163")}     # fonti in contrasto (vedi sopra)


def integra(cod, attrs):
    """Aggiunge i dati di famiglia (senza toccare quelli letti nella descrizione) e toglie i valori in contrasto."""
    for chiave in TOGLI.get(cod, ()):
        attrs.pop(chiave, None)
    for codici, valori, url in FATTI:
        if cod in codici:
            for chiave, valore, num, unita in valori:
                attrs.setdefault(chiave, F(valore, "sito", num, unita, url))
    return attrs
