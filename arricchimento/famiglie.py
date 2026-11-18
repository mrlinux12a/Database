"""Collega ogni articolo alla scheda prodotto (famiglia) del sito del produttore, aircontrolclima.it.

1. regole esplicite (ESPLICITE): per i gruppi di codici che la scheda non descrive con un prefisso (plenum per macchina PLM/PLR/PCAB,
   plenum per griglia PLPxxx, accessori dei canali microforati, ...);
2. altrimenti gli schemi di codice che il produttore pubblica nella scheda (campo "Codice": GRA-LXH, PSF-CB-LXH-..., LAF15-LXH ...),
   tagliati prima del segnaposto delle misure, vengono usati come prefissi (vince il piu' lungo).

pagina_di(cod_fornitore) -> id della scheda (stringa) oppure None.
"""
import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTE_SITO = os.path.join(BASE, "fonti", "aircontrolclima_it", "pagine.json")
with open(FONTE_SITO, encoding="utf-8") as _f:
    PAGINE = json.load(_f)

# (regex sul codice in maiuscolo senza il numero iniziale, id scheda) - la prima che combacia vince
ESPLICITE = [
    (r"^PLMB-", "141"),                                  # plenum bocchetta canalizzata
    (r"^PLM-|^PLR-", "140"),                             # plenum canalizzata (mandata / ripresa)
    (r"^PCAB-", "221"),                                  # plenum cablato motorizzato
    (r"^UNICAB", "274"),                                 # piastra universale cablata
    (r"^PLMUNI|^FLEXTUNI", "276"),                       # plenum universale standard
    (r"^CANOTTO-PL", "260"),                             # canotto ad innesto rapido
    (r"^BOX-CAN-PL", "260"),
    (r"^CANOTTO-AL|^CANOTTO-", "152"),                   # canotto di giunzione
    (r"^PLPDLF", "142"),                                 # plenum per diffusori lineari DLF
    (r"^PLPDLN", "270"),                                 # plenum per diffusori lineari DLN
    (r"^PLPS-", "269"),                                  # plenum compatto porta bocchetta
    (r"^PLP-[A-Z]+-\d+X150-", "268"),                    # plenum porta bocchetta H150
    (r"^PLP-", "143"),                                   # plenum porta bocchetta H100..500
    (r"^PLP(GRA|GRS|BQ|AQN)", "143"),                    # plenum per griglie/diffusori (stesso pannello PLP)
    (r"^PSB-[A-Z]+-\d+X150-", "271"),                    # plenum bocchetta a scomparsa H150
    (r"^BMA-OV", "181"),
    (r"^SC-|^SCN-", "193"),                              # serranda di taratura
    (r"^SK-", "178"),
    (r"^CT-|^CTP-|^CTFP-", "194"),                       # controtelaio
    (r"^DCG", "210"),
    (r"^SF-\d", "207"),                                  # serranda a farfalla per DC/DCP
    (r"^S-SOO?-", "246"),                                # silenziatore circolare
    (r"^CURVA-\d+-T|^ANELLI-|^EQUAL-", "168"),           # accessori canale in tessuto microforato
    (r"^ID-\d+-T", "168"),
    (r"^ID-|^TAPPO-|^CURVA\d*-|^TEE-|^RIDUZIONE-|^ROSONE-", "169"),   # canale e accessori in acciaio microforato
    (r"^CURVA-", "168"),
    (r"^PLENUMVMC", "215"),
    (r"^KK-43", "153"),
    (r"^FSI60", "154"),
    (r"^R900BIS", "161"),
    (r"^C50PFS001", "155"),
    (r"^C50PRF001", "156"),
    (r"^C50PFH001", "157"),
    (r"^C50PFS003", "158"),
    (r"^C50SQZ001", "258"),
    (r"^AIR10003|^AIR10005", "214"),
    (r"^AIR10067", "219"),
    (r"^FILTRO-R-", None),                               # filtri di ripresa per macchina: nessuna scheda
]

PLACEHOLDER = re.compile(r"(LXH|LxH|LXN|L-N|L-|-L\b|N°|Ø|\*|CODICE MACCHINA|CODICE)")


def _prefissi(codice_meta):
    out = []
    for pat in re.split(r"\s*/\s*|\s+-\s+|\n", codice_meta):
        pat = re.sub(r"^N°", "", pat.strip().upper())
        m = PLACEHOLDER.search(pat)
        taglio = pat[:m.start()] if m else pat
        taglio = taglio.rstrip("-").rstrip()
        if m and taglio and pat[len(taglio):len(taglio) + 1] == "-":
            taglio += "-"
        if len(taglio) >= 2:
            out.append(taglio)
    return out


_PREFISSI = sorted(
    ((x, mid) for mid, p in PAGINE.items()
     if p["meta"].get("Codice", "").strip() not in ("", "-")
     for x in _prefissi(p["meta"]["Codice"])),
    key=lambda t: -len(t[0]))


def stem(cod):
    return re.sub(r"^\d+(?=[A-Z])", "", cod.strip().upper())


def pagina_di(cod):
    s = stem(cod)
    for rx, mid in ESPLICITE:
        if re.search(rx, s):
            return mid
    for pref, mid in _PREFISSI:
        if s.startswith(pref):
            return mid
    return None


def url_pagina(mid):
    return PAGINE[mid]["url"] if mid in PAGINE else None
