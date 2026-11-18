# -*- coding: utf-8 -*-
"""Famiglie COMUNI a piu' cataloghi: il tipo di prodotto che due cataloghi chiamano in modo diverso ma e' la stessa cosa
(il «Tee» di Aquatechnik e il «Raccordo tee» di Air Control). Lista controllata e condivisa: si allunga a mano, una voce alla
volta, solo quando i prodotti sono davvero dello stesso tipo (vedi i dubbi nelle note).

Ogni voce: (nome della famiglia, regex sul nomeV2 in minuscolo). La prima che combacia vince. Si applica a TUTTI gli articoli
con nomeV2 (anche a quelli dei gruppi piu' piccoli di --min di proponi_famiglie.py): e' la prima parola/le prime parole del
nomeV2 a dire che tipo di prodotto e'. Le varianti (ridotto, intermedio, 45°, 90°, con girello...) NON sono famiglie: restano
nel nomeV2 e sono attributi candidati (proponi_attributi.py).

Si applica con  py -3.15 unisci_famiglie.py  (dopo proponi_famiglie.py --assegna, ripetibile quando si vuole).

Dubbi / non unite (di proposito)
  * «Collare»: in Aquatechnik sono collari da saldare sul tubo (presa), in Air Control collari di fissaggio dei canali: non e' la
    stessa cosa, a parte il nome.
  * «Valvola»: la valvola a sfera (acqua) non e' la valvola di mandata/ripresa (aria).
  * «Attacco a sella» (tubo dell'acqua) e «Stacco a sella» (canale dell'aria): stessa funzione, pezzi diversi.
  * «Kit», «Raccordo», «Bocchettone/Bocchetta»: nomi generici o falsi amici, non sono tipi di prodotto.
  * Caleffi: «Tee di bypass» (con ugello, per valvole di zona), «Tee Dirtmag» (per lavaggio impianti), «Tee sdoppiatore» (prese
    di pressione) sono componenti, non raccordi a T; «Giunto antivibrante» e «Giunto estensibile» (per gas) sono tubi flessibili
    / compensatori, non giunti di raccordo: restano famiglie del catalogo.
Poco sicure ma unite (da confermare): Giunto (giunto filettato dell'acqua / giunto dei tubi rigidi isolati), Collettore (collettore
dell'acqua / collettore del plenum VMC), Curva e gomito (sono sinonimi: curva per i canali, gomito per i tubi).
"""
import re

COMUNI = [
    ("Tee", r"^(?:fires\s+)?tee\b(?!\s+(?:di\s+by-?pass|dirtmag|sdoppiatore))|^raccordo tee\b"),
    ("Curva / Gomito", r"^(?:fires\s+)?(?:gomito|curva)\b"),
    ("Riduzione", r"^(?:fires\s+)?riduzione\b"),
    ("Tappo", r"^tappo\b"),
    ("Manicotto", r"^(?:fires\s+)?manicotto\b"),
    ("Giunto", r"^(?:fires\s+)?giunto\b(?!\s+(?:antivibrante|estensibile))"),
    ("Tubo", r"^tubo\b|^isoline(?:-plus)?\s+tubo\b"),
    ("Collettore", r"^collettore\b"),
]
_REGOLE = [(nome, re.compile(rx)) for nome, rx in COMUNI]


def famiglia_comune(nomev2):
    """-> nome della famiglia comune per questo nomeV2, oppure None."""
    n = (nomev2 or "").strip().lower()
    for nome, rx in _REGOLE:
        if rx.search(n):
            return nome
    return None
