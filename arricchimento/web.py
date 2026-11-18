# -*- coding: utf-8 -*-
"""Dati trovati con ricerche sul web per gli articoli che NON sono prodotti da Air Control (ricambi di terzi)
e che quindi non hanno una scheda sul sito del produttore (aircontrolclima.it).

Sono quasi tutti componenti Belimo (attuatori per serrande, posizionatori, motori per serrande tagliafuoco,
regolatore VAV) e i deumidificatori UDE.  Le ricerche sono state fatte il 16/11/2026 sulle pagine di
prodotto / schede tecniche pubblicate dal costruttore (nessun file scaricato: i valori sono quelli letti dai risultati di ricerca).

Regole seguite
  * ogni valore ha come `fonte` l'indirizzo della scheda/pagina in cui e' stato trovato (origine = "web");
  * un valore specifico di un modello (peso, assorbimento) e' inserito SOLO per il modello di cui e' stata letta la scheda;
  * il grado di protezione IP e' una caratteristica della serie: per le varianti della stessa serie (es. LM24A, LM230A-SR)
    e' stato esteso indicando come fonte la scheda del modello della serie in cui e' stato letto;
  * dove le schede danno valori diversi tra loro (versioni UE / USA, revisioni diverse) il valore NON e' stato inserito;
  * i valori gia' presenti nella descrizione del catalogo non vengono mai sovrascritti.

Per aggiungere altri dati basta aggiungere una riga a DATI (o a SERIE se vale per tutta una serie).
"""
import re

_DS = "https://www.belimo.com/mam/general-documents/datasheets/%s/belimo_%s_datasheet_%s.pdf"
_SHOP = "https://www.belimo.com/%s/shop/en_GB/p?code=%s"


def ds(modello, lingua="en-gb"):
    """Scheda tecnica del modello sul sito Belimo."""
    return _DS % (lingua, modello, lingua)


def shop(modello, paese="at"):
    """Pagina prodotto del modello sullo shop Belimo."""
    return _SHOP % (paese, modello)


def F(valore, fonte, num=None, unita=None):
    return {"valore": valore, "num": num, "unita": unita, "origine": "web", "fonte": fonte}


def ip(v, fonte):
    return F("IP" + str(v), fonte)


def peso(kg, fonte):
    return F(("%g" % kg).replace(".", ",") + " kg", fonte, kg, "kg")


def _n(x):
    return ("%g" % x).replace(".", ",")


def potenza(esercizio, riposo, va, fonte):
    """Assorbimento: W in esercizio, W a riposo, VA per il dimensionamento (dove indicati)."""
    parti = []
    if esercizio is not None:
        parti.append(_n(esercizio) + " W in esercizio")
    if riposo is not None:
        parti.append(_n(riposo) + " W a riposo")
    t = ", ".join(parti)
    if va is not None:
        t += (" " if t else "") + "(" + _n(va) + " VA per il dimensionamento)"
    return F(t, fonte, esercizio, "W")


def ambiente(minimo, massimo, fonte):
    return F("ambiente da %s a %s °C" % (minimo, massimo), fonte)


CAVO_4 = "1 m (4 × 0,75 mm²)"
CAVO_2_AUX = "1 m (2 × 0,75 mm²); contatti ausiliari 1 m (6 × 0,75 mm²)"
CLASSE_III = "III (bassissima tensione di sicurezza, SELV)"
CLASSE_II = "II (isolamento rinforzato)"

# --------------------------------------------------------------------------------------------------------------
# Dati per codice fornitore:  {codice: {chiave attributo: valore}}
# --------------------------------------------------------------------------------------------------------------
DATI = {
    # ---- Belimo senza ritorno a molla ----------------------------------------------------------------------
    "LM24A-SR": {
        "grado_ip": ip(54, ds("LM24A-SR")),
        "classe_isolamento": F(CLASSE_III, ds("LM24A-SR", "it-it")),
        "peso": peso(0.47, ds("LM24A-SR")),
        "potenza": potenza(1, 0.4, 2, ds("LM24A-SR")),
        "temperatura": ambiente(-30, 50, ds("LM24A-SR")),
        "lunghezza_cavo": F(CAVO_4, ds("LM24A-SR")),
    },
    "LM24A-S": {
        "grado_ip": ip(54, ds("LM24A-S")),
        "peso": peso(0.54, ds("LM24A-S")),
    },
    "LM230A": {
        "grado_ip": ip(54, ds("LM230A")),
        "classe_isolamento": F(CLASSE_II, ds("LM230A")),
        "peso": peso(0.46, ds("LM230A")),
        "potenza": potenza(1.5, 0.5, 3.5, ds("LM230A")),
    },
    "LM230A-S": {
        "grado_ip": ip(54, ds("LM230A-S")),
        "peso": peso(0.54, ds("LM230A-S")),
    },
    "NM24A-SR": {
        "grado_ip": ip(54, shop("NM24A-SR")),
        "peso": peso(0.73, ds("NM24A-SR")),
        "potenza": potenza(2, 0.4, 4, ds("NM24A-SR")),
    },
    "SM24A": {
        "grado_ip": ip(54, shop("SM24A", "uk")),
        "peso": peso(0.94, ds("SM24A")),
        "potenza": potenza(2, 0.2, 4, ds("SM24A")),
    },
    "SM230A": {
        "grado_ip": ip(54, ds("SM230A")),
        "peso": peso(0.94, ds("SM230A")),
        "potenza": potenza(2.5, 0.6, 6, ds("SM230A")),
    },
    "GM24A": {
        "grado_ip": ip(54, ds("GM24A")),
        "peso": peso(1.6, ds("GM24A")),
        "potenza": potenza(4, 2, 6, ds("GM24A")),
    },
    "GM230A": {
        "grado_ip": ip(54, shop("GM230A")),
    },
    "CM24-SR-L": {
        "grado_ip": ip(54, ds("CM24-SR-L")),
        "peso": peso(0.25, ds("CM24-SR-L")),
    },
    "CM230-L": {
        "grado_ip": ip(54, ds("CM230-L")),
    },

    # ---- Belimo con ritorno a molla ------------------------------------------------------------------------
    "LF24": {
        "grado_ip": ip(54, ds("LF24")),
        "classe_isolamento": F(CLASSE_III, ds("LF24")),
        "peso": peso(1.4, ds("LF24")),
        "temperatura": ambiente(-30, 50, ds("LF24")),
        "potenza": potenza(5, 2.5, 7, ds("LF24_US", "en-us")),
    },
    "LF24-S": {
        "grado_ip": ip(54, ds("LF24")),
        "peso": peso(1.5, ds("LF24-S")),
        "potenza": potenza(5, 2.5, 7, ds("LF24-S")),
    },
    "LF230": {
        "grado_ip": ip(54, ds("LF230")),
        "classe_isolamento": F(CLASSE_II, ds("LF230")),
        "peso": peso(1.6, ds("LF230")),
    },
    "LF230-S": {
        "grado_ip": ip(54, ds("LF230-S")),
        "classe_isolamento": F(CLASSE_II, ds("LF230-S")),
        "peso": peso(1.7, ds("LF230-S")),
    },
    "NF24A": {
        "grado_ip": ip(54, ds("NF24A-SR")),
        "peso": peso(2.0, ds("NF24A", "fi-fi")),
    },
    "NF24A-S2": {
        "grado_ip": ip(54, ds("NF24A-S2")),
        "classe_isolamento": F(CLASSE_III, ds("NF24A-S2", "de-ch")),
        "peso": peso(2.1, ds("NF24A-S2")),
        "potenza": potenza(6, 2.5, 8.5, ds("NF24A-S2")),
        "lunghezza_cavo": F(CAVO_2_AUX, ds("NF24A-S2")),
    },
    "NF24A-SR": {
        "grado_ip": ip(54, ds("NF24A-SR")),
        "peso": peso(2.0, ds("NF24A-SR")),
        "temperatura": ambiente(-30, 50, ds("NF24A-SR")),
    },
    "SF24A": {
        "grado_ip": ip(54, ds("SF24A")),
        "peso": peso(2.1, ds("SF24A")),
        "temperatura": ambiente(-30, 50, ds("SF24A")),
        "frequenza": F("50/60 Hz", ds("SF24A"), None, "Hz"),
    },
    "SF24A-S2": {
        "grado_ip": ip(54, ds("SF24A-S2")),
        "classe_isolamento": F(CLASSE_III, ds("SF24A-S2", "fr-fr")),
        "peso": peso(2.3, ds("SF24A-S2", "fr-fr")),
        "potenza": potenza(5.5, 1.5, 7.5, ds("SF24A-S2")),
        "lunghezza_cavo": F(CAVO_2_AUX, ds("SF24A-S2")),
    },
    "SF24A-SR": {
        "grado_ip": ip(54, "https://www.belimo.com/se/shop/en_GB/Actuators/Fail-Safe-Actuators/SF24A-SR/p?code=SF24A-SR"),
        "peso": peso(2.2, ds("SF24A-SR")),
        "lunghezza_cavo": F(CAVO_4, ds("SF24A-SR")),
    },
    "TF24": {
        "grado_ip": ip(42, ds("TF24")),
        "peso": peso(0.62, ds("TF24")),
        "potenza": potenza(2.5, 1.5, 5, ds("TF24")),
    },
    "TF24-SR": {
        "grado_ip": ip(42, ds("TF24-SR")),
        "peso": peso(0.62, ds("TF24-SR")),
        "potenza": potenza(1.3, 0.6, 2.6, ds("TF24-SR")),
    },
    "TF230": {
        "grado_ip": ip(42, ds("TF230")),
        "peso": peso(0.62, ds("TF230")),
        "potenza": potenza(2.5, 1.5, 5, ds("TF230")),
    },

    # ---- Belimo: posizionatori, unita' di controllo, regolatore VAV ----------------------------------------
    "SGA24": {
        "tensione": F("24 V AC/DC (19,2–28,8 V)", ds("SGA24"), 24, "V"),
        "frequenza": F("50/60 Hz", ds("SGA24"), None, "Hz"),
        "potenza": potenza(0.3, None, 1, ds("SGA24")),
        "temperatura": ambiente(-20, 50, ds("SGA24")),
        "peso": peso(0.14, ds("SGA24")),
        "campo_regolazione": F("segnale 2…10 V (selezionabile 0…10 V)", ds("SGA24")),
    },
    "SGF24": {
        "tensione": F("24 V AC/DC (19,2–28,8 V)", ds("SGF24"), 24, "V"),
        "frequenza": F("50/60 Hz", ds("SGF24"), None, "Hz"),
        "potenza": potenza(0.3, None, 1, ds("SGF24")),
        "temperatura": ambiente(-20, 50, ds("SGF24")),
        "campo_regolazione": F("segnale 2…10 V (commutabile a 0,5…10 V)", ds("SGF24")),
        "compatibilita": F("attuatori modulanti LM..A-SR, NM..A-SR, SM..A-SR, GM..A-SR",
                           ds("SGF24", "en-us")),
    },
    "S-BKS241B": {
        "tensione": F("24 V AC", shop("BKS24-1B"), 24, "V"),
    },
    "R-LMV-D3-MP": {
        "tensione": F("24 V AC/DC", ds("LMV-D3-MP"), 24, "V"),
        "grado_ip": ip(54, ds("LMV-D3-MP")),
        "coppia": F("5 Nm", ds("LMV-D3-MP"), 5, "Nm"),
        "potenza": potenza(2, 1, 4, ds("LMV-D3-MP")),
        "temperatura": ambiente(0, 50, ds("LMV-D3-MP")),
        "lunghezza_cavo": F(CAVO_4, ds("LMV-D3-MP")),
        "campo_regolazione": F("campo funzionale 0–500 Pa (regolazione 38–500 Pa alla portata nominale)",
                               ds("LMV-D3-MP")),
    },

    # ---- deumidificatori UDE (costruttore dell'unita': Elettroclima / Sabiana) -------------------------------
    "AC-UDE-30-H-D": {
        "portata": F("300 m³/h a 150 Pa; deumidificazione 18,9 l/24 h (20 °C, 50% UR)",
                     "https://elettroclimashop.com/cdn/3220986.pdf", 300, "m³/h"),
    },
}

# la sigla '230mc' del catalogo e' la portata d'aria in m³/h (la scheda dell'UDE 30 H conferma che '300mc' = 300 m³/h)
DATI_DESCRIZIONE = {
    "AC-UDE-23-V-D": {"portata": {"valore": "230 m³/h", "num": 230, "unita": "m³/h", "origine": "descrizione",
                                  "fonte": None}},
}

# Nomi migliori dove la descrizione del catalogo e' ambigua
NOMI = {
    "AC-UDE-23-V-D": "Deumidificatore verticale UDE 23 V, 230 m³/h",
    "AC-UDE-30-H-D": "Deumidificatore orizzontale UDE 30 H, 300 m³/h",
    "AC-CNV-UDE": "Pannello remoto con sensore T/H per deumidificatore UDE",
}

# --------------------------------------------------------------------------------------------------------------
# Caratteristiche di serie, estese alle varianti dello stesso modello base (solo dove manca il dato specifico)
# --------------------------------------------------------------------------------------------------------------
SERIE = [
    # (espressione sul codice fornitore, {attributo: valore})
    (r"^LM24A(-S|-SR)?$", {"grado_ip": ip(54, ds("LM24A-S"))}),
    (r"^LM230A", {"grado_ip": ip(54, ds("LM230A"))}),
    (r"^NM24A", {"grado_ip": ip(54, shop("NM24A-SR"))}),
    (r"^SM24A", {"grado_ip": ip(54, shop("SM24A", "uk"))}),
    (r"^SM230A", {"grado_ip": ip(54, ds("SM230A"))}),
    (r"^GM(24|230)A", {"grado_ip": ip(54, ds("GM24A"))}),
    (r"^LF24", {"grado_ip": ip(54, ds("LF24"))}),
    (r"^LF230", {"grado_ip": ip(54, ds("LF230"))}),
    (r"^NF24A", {"grado_ip": ip(54, ds("NF24A-SR"))}),
    (r"^SF24A", {"grado_ip": ip(54, ds("SF24A"))}),
    # serie TF: tutte le schede indicano IP42
    (r"^TF(24|230)", {"grado_ip": ip(42, ds("TF24"))}),
    # motori per serrande tagliafuoco BFL (4 Nm) e BFN (9 Nm) con sgancio termoelettrico BAT a 72 °C
    (r"^S-BFL", {"grado_ip": ip(54, "https://www.belimo.com/ch/shop/en_GB/Actuators/Fire-Damper-Actuators/BFL24-T/p?code=BFL24-T"),
                 "coppia": F("4 Nm (motore), 3 Nm (ritorno a molla)", ds("BFL24-T"), 4, "Nm"),
                 "taratura": F("sgancio termoelettrico BAT a 72 °C", ds("BFL24-T"), 72, "°C")}),
    (r"^S-BFN", {"grado_ip": ip(54, shop("BFN24-T", "se")),
                 "coppia": F("9 Nm (motore), 7 Nm (ritorno a molla)", ds("BFN24-T_500"), 9, "Nm"),
                 "taratura": F("sgancio termoelettrico BAT a 72 °C", ds("BFN24-T_500"), 72, "°C")}),
    (r"^S-BFN24T$", {"potenza": F("4,3 VA per il dimensionamento", ds("BFN24-T_500"), None, "VA")}),
]
_SERIE = [(re.compile(r), d) for r, d in SERIE]


def integra(forn, descr, nome, at):
    """Aggiunge ad `at` i valori trovati sul web per l'articolo `forn`; restituisce (nome, at).
    Non sovrascrive mai un valore gia' presente (descrizione, codice, scheda del produttore)."""
    for chiave, v in DATI.get(forn, {}).items():
        at.setdefault(chiave, dict(v))
    for chiave, v in DATI_DESCRIZIONE.get(forn, {}).items():
        at.setdefault(chiave, dict(v))
    for rx, d in _SERIE:
        if rx.search(forn):
            for chiave, v in d.items():
                at.setdefault(chiave, dict(v))
    return NOMI.get(forn, nome), at
