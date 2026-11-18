# -*- coding: utf-8 -*-
"""Da descrizione + codice fornitore di un articolo Air Control ricava:

  * nomev1   - il nome piu' semplice e completo (la descrizione del catalogo ripulita: refusi, abbreviazioni espanse,
               misure con unita', modelli in maiuscolo, "per <marca> <modello>" per la compatibilita');
  * attributi - solo quelli che si trovano davvero: dalla descrizione (origine "descrizione"), dal codice ("codice")
               o dalla scheda del produttore della famiglia ("sito", con l'indirizzo della scheda come fonte).

Niente viene inventato: se un dato non c'e', la riga dell'attributo non viene creata.
"""
import json
import os
import re

from . import famiglie, sito

RANGO = {"descrizione": 3, "codice": 2, "sito": 1, "web": 1}

MARCHI = {"samsung": "Samsung", "mitsubishi": "Mitsubishi", "daikin": "Daikin", "haier": "Haier", "toshiba": "Toshiba",
          "hisense": "Hisense", "lg": "LG", "panasonic": "Panasonic", "aermec": "Aermec", "sabiana": "Sabiana",
          "fujitsu": "Fujitsu", "idema": "Idema", "bosch": "Bosch", "tcl": "TCL", "gree": "Gree", "baxi": "Baxi",
          "clivet": "Clivet", "innova": "Innova", "midea": "Midea", "parkair": "Parkair", "hitachi": "Hitachi"}
ACRONIMI = {"vmc": "VMC", "pvc": "PVC", "pal": "PAL", "ir": "IR", "pdc": "PDC", "rpet": "RPET", "led": "LED", "vrv": "VRV",
            "ac": "AC", "dc": "DC", "app": "app", "uv": "UV"}
NOMI = {"eternal": "Eternal", "smart": "Smart", "spyro": "Spyro", "domo": "Domo", "skyline": "Skyline", "unicab": "Unicab",
        "koolnova": "Koolnova", "residenziale": "Residenziale", "dual": "Dual", "fancoil": "fancoil", "sbs": "SBS", "control": "Control"}
# parole italiane comuni: mai trattate come sigle/modelli anche se compaiono nel codice
COMUNI = set("""kit tee per di da con senza in a al e x pz mt mq mm cm kg dx sx uni plenum griglia bocchetta diffusore serranda
portabocchetta controtelaio tubo curva riduzione tappo canale silenziatore stacco manicotto attuatore regolatore filtro
interfaccia raccordo collettore canotto collare collari isolante valvola comando rosone cavalletto motore chiuso chiusi
aperto cablato mandata ripresa universale singolo doppio tondo piatto rigido flessibile isolato zincato verniciato
preverniciato alluminio bianca bianco nera nero plastica tessile acciaio rame metallo naturale master slave radio filo
cartongesso muro posteriore superiore laterale integrato aux fine corsa molla ritorno""".split())

TYPO = [
    (r"\b(?:plemum|plenun|pleum)\b", "plenum"),
    (r"\b2ortabocchetta\b", "portabocchetta"),
    (r"\bgrigliia\b", "griglia"),
    (r"\bmicrofotato\b", "microforato"),
    (r"continuita'", "continuità"),
    (r"\bunita(?= controllo)", "unità"),
    (r"\bpann\.\s?forell\.?", "pannello forellinato"),
    (r"\binterf\.\s?filo\b", "con interfaccia a filo"),
    (r"\binterfaccia filo\b", "interfaccia a filo"),
    (r"\bir integrato\b", "con IR integrato"),
    (r"\bdefles\.?", "deflessione"),
    (r"\bc/(?=\w)", "con "),
    (r"\bs/(?=\w)", "senza "),
    (r"ritorno molla", "ritorno a molla"),
    (r"\bon-off/3p\b", "on-off/3 punti"),
    (r"\bacc\.\s?inox\b", "acciaio inox"),
    (r"\bacc\.", "acciaio"),
    (r"\brettang\.", "rettangolare"),
    (r"\bestens\.", "estensibile"),
    (r"\bnorm\.", "normalmente"),
    (r"\bproporz\.", "proporzionale"),
    (r"\belet\.", "elettronica"),
    (r"\bmot\.", "motorizzato"),
    (r"\bser reg\b", "serranda di regolazione"),
    (r"\bflex\b", "flessibile"),
    (r"\bcartong\.?(?=\s|$)", "cartongesso"),
    (r"\bposteriore car$", "posteriore cartongesso"),
    (r"^plenum (mandata|ripresa)\b", r"plenum di \1"),
    (r"^bocchetta mandata\b", "bocchetta di mandata"),
    (r"\bo-v\b", "ov"),
    (r"\bbco\b", "bianco"),
    (r"\bvo-(?=\d)", "ov "),
    (r"\bscomaprsa\b", "scomparsa"),
    (r"\bdiff\b\.?", "diffusore"),
    (r"\b(?:mitsusbishi|mitusbishi|mitusubishi|mtisubishi)\b", "mitsubishi"),
    (r"\b(?:mandarta|mandta)\b", "mandata"),
    (r"\bchiusp\b", "chiuso"),
    (r"\bcanallizata\b", "canalizzata"),
    (r"\ballumino\b", "alluminio"),
    (r"\bferitoe\b", "feritoie"),
    (r"\bcart\.", "cartongesso"),
    (r"\binn\b", "innesto"),
    (r"\baccopp\.", "accoppiamento"),
    (r"\bprofilialluminio\b", "profili alluminio"),
    (r"\bv-o\b", "ov"),
    (r"\bude (\d+) (v|h)\b", r"ude-\1-\2"),
    (r"\bp\.\s?(\d+)\s?cm\b", r"profonda \1 cm"),
    (r"\bfer\.", "feritoia"),
    (r"\bcirc\.", "circolare"),
    (r"\buni\b", "universale"),
    (r"\belec\.", "electric"),
    (r"\ball$", "alluminio"),
]

LESSICO = {
    "posteriore": ("pos", "posteriore"), "post": ("pos", "posteriore"),
    "superiore": ("pos", "superiore"), "sup": ("pos", "superiore"),
    "laterale": ("pos", "laterale"),
    "cartongesso": ("ins", "per cartongesso"), "muro": ("ins", "per muro"),
    "bianca": ("col", "bianca"), "bianco": ("col", "bianco"), "bianchi": ("col", "bianchi"),
    "nera": ("col", "nera"), "nero": ("col", "nero"), "grigio": ("col", "grigio"),
}
COLORI = {"bianca": "bianco", "bianco": "bianco", "bianchi": "bianco", "nera": "nero", "nero": "nero", "grigio": "grigio"}
MATERIALI = {  # parola -> (chiave attributo, valore)
    "alluminio": ("materiale", "alluminio"), "zincato": ("finitura", "zincato"), "zincata": ("finitura", "zincata"),
    "preverniciato": ("finitura", "preverniciato"), "verniciato": ("finitura", "verniciato"),
    "naturale": ("finitura", "naturale"), "pvc": ("materiale", "PVC"), "plastica": ("materiale", "plastica"),
    "tessile": ("materiale", "tessuto"), "rame": ("materiale", "rame"), "metallo": ("materiale", "metallo"),
    "acciaio": ("materiale", "acciaio"), "epp": ("materiale", "polipropilene espanso (EPP)"),
    "eps": ("materiale", "polistirene espanso (EPS)"),
}
DISP = {"pvc": "PVC", "epp": "EPP", "eps": "EPS"}
CLASSI_PLENUM = {"plenum", "portabocchetta", "piastra", "kit"}
# sigle di serie: le lettere iniziali degli schemi di codice pubblicati dal produttore (PSF, DLF, GRA, LAF, ...)
SERIE = {m.group(0).lower() for p, _ in famiglie._PREFISSI for m in [re.match(r"[A-Z]{2,6}", p)] if m} - COMUNI


def registra_codici(codici):
    """aggiunge alle sigle di serie le lettere iniziali dei codici del catalogo che compaiono almeno 3 volte"""
    from collections import Counter
    n = Counter()
    for c in codici:
        m = re.match(r"\d?([A-Z]{2,6})(?=[-0-9])", c.strip().upper())
        if m:
            n[m.group(1).lower()] += 1
    SERIE.update(w for w, k in n.items() if k >= 3 and w not in COMUNI and w not in ("air",))
FERITOIE = {"1": "1 feritoia"}


def _f(x):
    return float(str(x).replace(",", "."))


def _ph(i):
    return chr(0xE000 + i)


def _is_ph(t):
    return len(t) == 1 and 0xE000 <= ord(t) < 0xF000


def tipo_base(mid):
    p = famiglie.PAGINE.get(mid)
    if not p:
        return None

    def fix(x):
        x = (x or "").replace("\n", " ")
        x = re.sub(r"(?<=\d)�", "°", x)
        x = re.sub(r"(?i)unit�", "Unità", x)
        x = x.replace("�", "")
        return re.sub(r"\s+", " ", x).strip()
    t, s = fix(p.get("titolo")), fix(p.get("serie"))
    if re.fullmatch(r"[A-Z0-9][A-Z0-9\- ]*", t) and s:
        return f"{t} - {s.capitalize()}"
    return t


class Articolo:
    def __init__(self, cod, descr):
        self.cod = cod.strip()
        self.cu = self.cod.upper()
        self.d0 = re.sub(r"\s+", " ", descr).strip()
        self.pezzi = []
        self.attrs = {}
        self.att = []          # (n, diametro)
        self.dia = []          # diametri trovati
        self.pos = None
        self.compat = None
        self.mid = famiglie.pagina_di(cod)
        self.url = famiglie.url_pagina(self.mid) if self.mid else None
        parti = [p for p in re.split(r"[-_ ]+", self.cu) if p]
        self.parti = set(parti) | {m.group(0) for p in parti for m in [re.match(r"[A-Z]+", p)] if m}
        self.anod = bool(self.mid in sito.CODICE_A_ANODIZZATO and re.search(r"(\d+X\d+|\d+F)A$", self.cu))
        self.classe = ""

    # ------------------------------------------------------------------ attributi
    def put(self, k, v, num=None, unita=None, orig="descrizione", fonte=None):
        r = RANGO[orig]
        old = self.attrs.get(k)
        if old and old["rango"] >= r:
            return
        self.attrs[k] = dict(valore=v, num=num, unita=unita, origine=orig, fonte=fonte, rango=r)

    def ph(self, kind, text):
        self.pezzi.append([kind, text])
        return _ph(len(self.pezzi) - 1)

    def e_codice(self, tok, primo=False):
        """il token (minuscolo) e' una sigla/modello da scrivere in maiuscolo?"""
        if primo or tok in COMUNI or tok in NOMI or tok.startswith("on-off") or re.fullmatch(r"\d+-\d+c", tok):
            return False
        if re.search(r"\d", tok) and re.search(r"[a-z]", tok):
            return True
        if re.fullmatch(r"[cr]?vav[a-z]{0,2}", tok):
            return True
        base = re.sub(r"[^a-z0-9]", "", tok).upper()
        if not re.search(r"[A-Z]", base):
            return False
        if "-" in tok:
            pezzi = [x for x in tok.split("-") if x]
            if pezzi and all(x.upper() in self.parti or x in SERIE for x in pezzi):
                return True
        if 2 <= len(base) <= 6 and base in self.parti:
            return True
        if tok in SERIE:
            return True
        return bool(3 <= len(base) <= 5 and tok.isalpha() and base in self.cu)

    # ------------------------------------------------------------------ preparazione
    def prepara(self):
        s = self.d0.lower()
        cl = re.escape(self.cod.lower())
        if len(self.cod) >= 6 and re.search(r"[-\d]", self.cod):      # il codice ripetuto all'inizio, in fondo o attaccato al testo
            s = re.sub(rf"^{cl}(?=\s)|(?<=\s){cl}$|(?<=[a-z.]){cl}$", " ", s)
        s = s.replace("+", " + ")
        s = re.sub(r"(?<!\d)\bx\b(?!\d)", "per", s)
        for a, b in TYPO:
            s = re.sub(a, b, s)
        s = re.sub(r"\bov-(?=\d)", "ov ", s)
        s = re.sub(r"\s+", " ", s).strip()
        self.classe = s.split(" ")[0] if s else ""
        return s

    # ------------------------------------------------------------------ regole sulle frasi
    def r_dim3(self, m):
        a, b, c = m.group(1), m.group(2), m.group(3)
        self.put("dimensioni", f"{a} x {b} x {c} mm")
        return self.ph("dim", f"{a}x{b}x{c} mm")

    def r_lung_fer(self, m):
        L, n = m.group(1), m.group(2)
        self.put("lunghezza", f"{L} mm", int(L), "mm")
        self.put("feritoie", n, int(n))
        return self.ph("dim", f"{L} mm") + " " + self.ph("misc", f"{n} {'feritoia' if n == '1' else 'feritoie'}")

    def r_fer(self, m):
        n = m.group(1)
        self.put("feritoie", n, int(n))
        return self.ph("misc", f"{n} {'feritoia' if n == '1' else 'feritoie'}")

    def r_att(self, m):
        n, d, d2 = int(m.group(1)), m.group(2), m.group(3)
        self.att.append((n, d if not d2 else f"{d}-{d2}"))
        for x in (d, d2):
            if x:
                self.dia.append(int(x))
        return self.ph("att", f"{n}x{d}" + (f"-{d2}" if d2 else ""))

    def r_lxh(self, m):
        a, b, an = m.group(1), m.group(2), m.group(3)
        self.put("dimensioni", f"{a} x {b} mm")
        self.put("lunghezza", f"{a} mm", int(a), "mm")
        self.put("altezza", f"{b} mm", int(b), "mm")
        if an:
            self.anod = self.anod or self.mid in sito.CODICE_A_ANODIZZATO
        return self.ph("dim", f"{a}x{b} mm")

    def r_dn(self, m):
        self.put("dn", f"DN{m.group(1)}", int(m.group(1)))
        return self.ph("dim", f"DN{m.group(1)}")

    def r_dia(self, m):
        a, sep, b = m.group(1), m.group(2), m.group(3)
        self.dia += [int(a)] + ([int(b)] if b else [])
        return self.ph("dim", f"Ø{a}" + (f"{sep}{b}" if b else ""))

    def r_lungh(self, m):
        a, b = m.group(1), m.group(2)
        if b:
            self.put("lunghezza", f"{a}–{b} mm")
            return self.ph("dim", f"L{a}–{b}")
        self.put("lunghezza", f"{a} mm", int(a), "mm")
        return self.ph("dim", f"L{a}")

    def r_lungh_m(self, m):
        self.put("lunghezza", f"{m.group(1)} m", _f(m.group(1)), "m")
        return self.ph("dim", f"L{m.group(1)} m")

    def r_alt(self, m):
        a, b = m.group(1), m.group(2)
        if b:
            self.put("altezza", f"{a}–{b} mm")
            return self.ph("dim", f"H{a}–{b}")
        self.put("altezza", f"{a} mm", int(a), "mm")
        return self.ph("dim", f"H{a}")

    def r_gradi(self, m):
        return f"{m.group(1)} {m.group(2)}°"

    def r_spess(self, m):
        v = m.group(1)
        self.put("spessore", f"{v} mm", _f(v), "mm")
        return self.ph("dim", f"spessore {v} mm")

    def r_mm(self, m):
        v = m.group(1)
        if re.search(r"isolat|silenziator", self.d0.lower()):
            self.put("coibentazione", f"isolato, spessore {v} mm")
            return self.ph("misc", f"spessore isolante {v} mm")
        if self.classe in ("isolante", "guaina"):
            self.put("spessore", f"{v} mm", _f(v), "mm")
            return self.ph("dim", f"spessore {v} mm")
        if self.classe == "piastra":
            self.put("lunghezza", f"{v} mm", _f(v), "mm")
            return self.ph("dim", f"{v} mm")
        if self.classe == "profilo" or self.classe == "pannello":
            self.put("spessore", f"{v} mm", _f(v), "mm")
            return self.ph("dim", f"spessore {v} mm")
        return self.ph("dim", f"{v} mm")

    def r_isol_mm(self, m):
        v = m.group(1)
        self.put("coibentazione", f"isolato, spessore {v} mm")
        return self.ph("w", f"isolato {v} mm")

    def r_slash(self, m):
        a, b, c = m.group(1), m.group(2), m.group(3)
        out = self.ph("dim", f"{a}/{b} mm")
        if c:
            self.put("colore", "bianco")
            out += " " + self.ph("col", c)
        return out

    def r_profonda(self, m):
        return self.ph("misc", f"profondità {m.group(1)} cm")

    def r_confmin(self, m):
        self.put("confezione", f"{m.group(1)} pz (confezione minima)")
        return self.ph("misc", f"(confezione minima {m.group(1)} pz)")

    def r_box(self, m):
        self.put("confezione", f"{m.group(1)} pz (box)")
        return self.ph("misc", f"box da {m.group(1)} pz")

    def r_pz_par(self, m):
        self.put("confezione", f"{m.group(1)} pz")
        return self.ph("misc", f"({m.group(1)} pz)")

    def r_pz(self, m):
        self.put("confezione", f"{m.group(1)} pz")
        return self.ph("misc", f"{m.group(1)} pz")

    def r_rotolo(self, m):
        self.put("confezione", f"rotolo da {m.group(1)} m")
        return self.ph("misc", f"rotolo da {m.group(1)} m")

    def r_mt(self, m):
        v = m.group(1)
        if self.classe in ("bobina",):
            self.put("confezione", f"bobina da {v} m")
            return self.ph("misc", f"bobina da {v} m")
        self.put("lunghezza", f"{v} m", _f(v), "m")
        return self.ph("dim", f"{v} m")

    def r_prezzo_mt(self, m):
        self.put("confezione", "venduto al metro")
        return self.ph("misc", "al metro")

    def r_prezzo_mq(self, m):
        self.put("confezione", "venduto al m²")
        return self.ph("misc", "al m²")

    def r_mq(self, m):
        self.put("confezione", "venduto al m²")
        return self.ph("misc", "al m²")

    def r_kg(self, m):
        self.put("confezione", f"{m.group(1)} kg")
        return self.ph("misc", f"{m.group(1)} kg")

    def r_gr(self, m):
        self.put("confezione", f"{m.group(1)} g")
        return self.ph("misc", f"{m.group(1)} g")

    def r_volt(self, m):
        v, tipo = m.group(1), m.group(2)
        if v not in ("3", "5", "12", "24", "48", "110", "115", "220", "230", "240", "380", "400"):
            return m.group(0)
        txt = f"{v} V" + (f" {tipo.upper()}" if tipo else "")
        self.put("tensione", txt, _f(v), "V")
        return self.ph("misc", txt)

    def r_nm(self, m):
        txt = f"{m.group(1)} Nm"
        self.put("coppia", txt, _f(m.group(1)), "Nm")
        return self.ph("misc", txt)

    def r_temp(self, m):
        txt = f"{m.group(1)} °C"
        self.put("taratura", txt, int(m.group(1)), "°C")
        return self.ph("misc", txt)

    def r_portata(self, m):
        txt = f"{m.group(1)}–{m.group(2)} m³/h"
        self.put("portata", txt)
        return self.ph("misc", txt)

    def r_compat_per(self, m):
        ogg, mod = m.group(1), m.group(2)
        if not self.e_codice(mod):
            return m.group(0)
        self.compat = f"{ogg} {mod.upper()}"
        return self.ph("comp", f"per {ogg} {mod.upper()}")

    def applica_regole(self, s):
        R = [
            (r"(?<![\d,.x])(\d{2,4})x(\d{2,4})x(\d+(?:,\d+)?)(?![\d])", self.r_dim3),
            (r"\b(\d{3,4})x(\d)f\b", self.r_lung_fer),
            (r"\b(\d{3,4})\s+(\d)\s*(?:feritoi[ae]|f)\b", self.r_lung_fer),
            (r"\b(\d)\s+feritoi[ae]\b", self.r_fer),
            (r"\b([1-9])\s?x\s?d?(\d{2,3})(?:-(\d{2,3}))?\b", self.r_att),
            (r"(?<![\d,.])(\d{2,4})x(\d{2,4})(a?)\b(?:\s*mm)?", self.r_lxh),
            (r"\bdn\s?(\d{2,3})\b", self.r_dn),
            (r"\b(?:ø|d)\s?(\d{2,4})(?:\s?([-/])\s?(\d{2,4}))?\b", self.r_dia),
            (r"\bl\.?\s?(\d{2,4})(?:\s?-\s?(\d{2,4}))?(?:\s?mm)?\b", self.r_lungh),
            (r"\bl\.(\d)m\b", self.r_lungh_m),
            (r"\bh\.?\s?(\d{2,4})(?:\s?-\s?(\d{2,4}))?(?:\s?mm)?\b", self.r_alt),
            (r"\b(curva|sella|tee|angolare|singolo|doppio)\s+(45|90)\b", self.r_gradi),
            (r"\b(?:spessore|sp\.)\s?(\d+(?:[.,]\d+)?)\s?mm\b", self.r_spess),
            (r"\bprofonda\s+(\d+)\s?cm\b", self.r_profonda),
            (r"\(conf\.?\s?min\.?\s?da\s?(\d+)\s?pz\)", self.r_confmin),
            (r"\bbox\s+(\d+)\s?pz\b", self.r_box),
            (r"\((\d+)\s?pz\)", self.r_pz_par),
            (r"\b(\d+)\s?pz\b", self.r_pz),
            (r"\brotolo\s+(\d+)\s?mt\b", self.r_rotolo),
            (r"\bprezzo al mt\b", self.r_prezzo_mt),
            (r"\bprezzo al mq\b", self.r_prezzo_mq),
            (r"\b(\d+)\s?mt\b", self.r_mt),
            (r"\b(\d+(?:[.,]\d+)?)\s?v\b(?:\s?(ac/dc|ac|dc)\b)?", self.r_volt),
            (r"\b(\d+(?:,\d+)?)\s?nm\b", self.r_nm),
            (r"\b(\d+)-(\d+)\s?mc(?:/h)?\b", self.r_portata),
            (r"\bisolato\s+(\d+)\s?mm\b", self.r_isol_mm),
            (r"\b(\d{3})\s?mc\b", lambda m: self.ph("misc", f"{m.group(1)} mc")),
            (r"\b(\d{2,3})/(\d{2,3})(bianco|bianca)?\b", self.r_slash),
            (r"\b(\d+(?:[.,]\d+)?)\s?mm\b", self.r_mm),
            (r"\b(\d+)\s?kg\b", self.r_kg),
            (r"\b(\d+)\s?gr\b", self.r_gr),
            (r"\bper (griglia|griglie|diffusori|diffusore|bocchetta|portabocchetta|serranda tagliafuoco|attuatori)\s+"
             r"([a-z0-9]+(?:-[a-z0-9]+)*)(?=\s|$)", self.r_compat_per),
        ]
        for rx, fn in R:
            s = re.sub(rx, fn, s)
        if "termofusibile" in s:
            s = re.sub(r"\b(\d{2,3})\s?c\b", self.r_temp, s)
        if re.search(r"\bmq\b", s):
            s = re.sub(r"\bmq\b", self.r_mq, s)
        # tipo di comando (attuatori, serrande, elettromagneti)
        cmd = []
        if "on-off/3 punti" in s:
            cmd.append("on-off / 3 punti")
        elif re.search(r"\bon-off\b", s):
            cmd.append("on-off")
        if "proporzionale" in s:
            cmd.append("proporzionale")
        for rx in (r"\b(?:con|senza) ritorno a molla\b", r"\bnormalmente (?:eccitato|diseccitato)\b"):
            mm = re.search(rx, s)
            if mm:
                cmd.append(mm.group(0))
        mm = re.search(r"\bcomando (meccanico|manuale)\b", s)
        if mm:
            cmd.append(mm.group(1))
        if cmd:
            self.put("comando", ", ".join(cmd))
        if self.classe in ("tubo", "silenziatore") and re.search(r"\b(?:iso|isolat[oa])\b", s):
            self.put("coibentazione", "isolato")
        return s

    # ------------------------------------------------------------------ parole
    def parola(self, t, primo=False):
        if t in ("-", "–", "+"):
            return ("sep", t)
        if t in ("m-m", "m/m", "mm") and self.classe in ("riduzione", "nipplo", "manicotto"):
            self.put("maschio_femmina", "maschio–maschio")
            return ("w", "maschio-maschio")
        if t == "m/f":
            self.put("maschio_femmina", "maschio–femmina")
            return ("w", "maschio/femmina")
        if t in ("m-m", "m/m"):
            return ("w", "M-m")
        if t == "m/r":
            return ("w", "M/R")
        if t == "ec":
            return ("m", "EC")
        if t == "iso":
            return ("w", "isolata" if self.classe in ("riduzione", "curva", "guaina", "isolina") else "isolato")
        if self.classe == "flangia" and t in ("xs", "s", "m", "l", "xl"):
            return ("w", "taglia " + t.upper())
        if t in LESSICO:
            k, txt = LESSICO[t]
            if k == "col":
                self.put("colore", COLORI[t])
            if k == "pos":
                self.pos = txt
            if k == "ins":
                self.put("installazione", txt.replace("per ", ""))
            return (k, txt)
        if t in MARCHI:
            return ("marca", MARCHI[t])
        if t in MATERIALI:
            k, v = MATERIALI[t]
            if t == "alluminio" and self.anod:
                self.put("materiale", "alluminio")
                self.put("finitura", "alluminio anodizzato", orig="codice", fonte=self.url)
                return ("w", "alluminio anodizzato")
            self.put(k, v)
            return ("w", DISP.get(t, t))
        if t in ("dx", "sx"):
            return ("w", t.capitalize())
        if t in ACRONIMI:
            return ("w", ACRONIMI[t])
        if t in NOMI:
            return ("w", NOMI[t])
        if re.fullmatch(r"\d+\.\d+", t):
            return ("m", t)
        if self.e_codice(t, primo):
            return ("m", t.upper())
        if re.fullmatch(r"\(.+\)", t):
            return ("misc", t)
        if re.fullmatch(r"[a-z]", t) and t not in ("a", "e", "x"):
            return ("w", t.upper())
        return ("w", t)

    def modello_fmt(self, t):
        if re.search(r"\d", t):
            return t.upper()
        if t in ACRONIMI:
            return ACRONIMI[t]
        return t.capitalize()

    def tokenizza(self, s):
        pezzi = []
        toks = s.split(" ")
        marca = None
        modello = []
        prima = True
        for t in toks:
            if not t:
                continue
            primo, prima = prima, False
            if _is_ph(t[0]) and all(_is_ph(ch) or ch == " " for ch in t):
                for ch in t:
                    pezzi.append(self.pezzi[ord(ch) - 0xE000][:])
                continue
            # un segnaposto puo' essere attaccato ad altro testo (es. "vo-" + misura)
            if any(_is_ph(ch) for ch in t):
                for seg in re.split("([-])", t):
                    if not seg:
                        continue
                    if _is_ph(seg[0]):
                        pezzi.append(self.pezzi[ord(seg[0]) - 0xE000][:])
                    else:
                        seg = seg.strip("-")
                        if seg:
                            k, txt = self.parola(seg, False)
                            pezzi.append([k, txt])
                continue
            if marca is not None:
                if t in ("-", "–") or re.fullmatch(r"\d+\.\d+", t):
                    if re.fullmatch(r"\d+\.\d+", t):
                        modello.append(("ver", t))
                    continue
                modello.append(("mod", t))
                continue
            k, txt = self.parola(t, primo)
            if k == "marca":
                marca = txt
                continue
            pezzi.append([k, txt])
        if self.anod and not any("alluminio" in p[1] for p in pezzi if p[0] == "w"):
            pezzi.append(["col", "alluminio anodizzato"])
        if marca is not None:
            mod = [self.modello_fmt(t) for k, t in modello if k == "mod"]
            ver = [t for k, t in modello if k == "ver"]
            self.compat = " ".join([marca] + mod)
            pezzi.append(["comp", "per " + " ".join([marca] + mod + ver)])
        return pezzi

    # ------------------------------------------------------------------ composizione del nome
    def componi(self, pezzi):
        # fusione att [+|-] att e posizione agganciata all'attacco
        out = []
        i = 0
        plenum_like = self.classe in CLASSI_PLENUM
        while i < len(pezzi):
            k, t = pezzi[i]
            if k == "att":
                gruppi = [t]
                j = i + 1
                while j + 1 < len(pezzi) and pezzi[j][0] in ("sep", "w") and pezzi[j][1] in ("+", "-") and pezzi[j + 1][0] == "att":
                    gruppi.append(pezzi[j + 1][1])
                    j += 2
                out.append(["att", gruppi])
                i = j
                continue
            out.append([k, t])
            i += 1
        # testo degli attacchi
        pezzi2 = []
        for k, t in out:
            if k != "att":
                pezzi2.append([k, t])
                continue
            parti = []
            for ix, g in enumerate(t):
                m = re.fullmatch(r"(\d+)x(\d+(?:-\d+)?)", g)
                n, d = int(m.group(1)), m.group(2)
                if self.classe == "collettore":
                    if ix == 0 and n == 1:
                        parti.append(f"ingresso Ø{d}")
                    else:
                        parti.append(f"{n} stacchi Ø{d}")
                elif plenum_like:
                    parti.append(f"{n} {'attacco' if n == 1 else 'attacchi'} Ø{d}")
                else:
                    parti.append(f"{n}xØ{d}")
            pezzi2.append(["att", " + ".join(parti)])
        # pos agganciata all'attacco precedente
        pezzi3 = []
        for k, t in pezzi2:
            if k == "pos" and pezzi3 and pezzi3[-1][0] == "att":
                pezzi3[-1][1] += " " + t
            elif k == "pos":
                pezzi3.append(["w", t])
            else:
                pezzi3.append([k, t])
        # ordine: parole iniziali + modelli + compatibilita' + resto + installazione + colore
        def idx(kinds, solo_modelli=False):
            return [i for i, p in enumerate(pezzi3) if p[0] in kinds and not (solo_modelli and re.fullmatch(r"\d+\.\d+", p[1]))]
        i_comp, i_col, i_ins, i_mod = idx(("comp",)), idx(("col",)), idx(("ins",)), idx(("m",), True)
        tolti = set(i_comp + i_col + i_ins + i_mod)
        corpo = [p for i, p in enumerate(pezzi3) if i not in tolti]
        testa = []
        while corpo and corpo[0][0] == "w":
            testa.append(corpo.pop(0))
        modelli = [pezzi3[i] for i in i_mod]
        comp = [pezzi3[i] for i in i_comp]
        ins = [pezzi3[i] for i in i_ins]
        col = [pezzi3[i] for i in i_col]
        seq = testa + modelli + comp + corpo + ins + col
        # virgole
        s = ""
        prev = None
        visto_dim = False
        for ix, (k, t) in enumerate(seq):
            if ix == 0:
                s = t
            elif k == "sep" or prev == "sep":
                s += " " + t
            elif k in ("w", "m") and prev in ("w", "m", "comp"):
                s += " " + t
            elif k == "comp" and prev in ("w", "m"):
                s += " " + t
            elif k == "dim" and prev in ("w", "m", "comp") and not visto_dim:
                s += " " + t
            elif k == "att" and prev in ("w", "m", "comp") and not plenum_like:
                s += " " + t
            elif k == "misc" and prev == "w" and not modelli and not visto_dim and ix == len(testa):
                s += " " + t
            elif k == "pos" or t.startswith("("):
                s += " " + t
            else:
                s += ", " + t
            if k == "dim":
                visto_dim = True
            prev = k
        s = re.sub(r"\s+", " ", s).replace(" ,", ",").strip(" ,")
        return s[:1].upper() + s[1:]

    # ------------------------------------------------------------------ attributi dedotti
    def attrs_da_attacchi(self):
        if self.att:
            parti, n_tot = [], 0
            for ix, (n, d) in enumerate(self.att):
                parti.append(f"{n} x Ø{d} mm")
                n_tot += n
            if self.classe == "collettore" and self.att[0][0] == 1 and len(self.att) > 1:
                n_tot -= 1
            txt = " + ".join(parti) + (f", {self.pos}" if self.pos else "")
            self.put("attacco", txt)
            if self.classe in CLASSI_PLENUM or self.classe == "collettore":
                self.put("n_derivazioni", str(n_tot), n_tot)
        if self.dia:
            uniq = sorted(set(self.dia), key=self.dia.index)
            if len(uniq) == 1:
                self.put("diametro", f"{uniq[0]} mm", uniq[0], "mm")
            else:
                self.put("diametro", " / ".join(str(x) for x in uniq) + " mm")

    def da_codice(self):
        # installazione dai suffissi del codice quando la descrizione non la dice
        if re.match(r"\d?PS\w*-(CB|MB)-", self.cu):
            self.put("installazione", "cartongesso" if "-CB-" in self.cu else "muro", orig="codice", fonte=self.url)
        if self.anod:
            self.put("materiale", "alluminio", orig="codice", fonte=self.url)
            self.put("finitura", "alluminio anodizzato", orig="codice", fonte=self.url)

    def da_sito(self):
        if not self.mid:
            return
        fam = sito.FAM.get(self.mid, {})
        for k, v in fam.items():
            old = self.attrs.get(k)
            if k == "materiale" and old and old["origine"] == "descrizione":
                if old["valore"].lower() in v.lower():
                    self.attrs[k] = dict(valore=v, num=None, unita=None, origine="sito", fonte=self.url, rango=RANGO["sito"])
                continue
            self.put(k, v, orig="sito", fonte=self.url)
        fs = sito.FINITURA_STANDARD.get(self.mid)
        if fs:
            col = self.attrs.get("colore")
            if col and col["valore"] == fs[1] and "finitura" not in self.attrs and fs[0]:
                self.put("finitura", fs[0], orig="sito", fonte=self.url)
            elif (not col and not self.anod and self.mid in sito.CODICE_A_ANODIZZATO
                  and self.attrs.get("materiale", {}).get("origine") != "descrizione" and fs[1]):
                # la scheda indica la finitura standard (bianca) e dice che la "A" finale del codice e' la versione in
                # alluminio: un codice senza "A" e' quindi la versione standard
                self.put("colore", fs[1], orig="sito", fonte=self.url)
                if fs[0]:
                    self.put("finitura", fs[0], orig="sito", fonte=self.url)
        tb = tipo_base(self.mid)
        if tb:
            self.put("tipo_base", tb, orig="sito", fonte=self.url)

    def righe(self):
        return {k: {kk: vv for kk, vv in v.items() if kk != "rango"} for k, v in self.attrs.items()}


# descrizioni del catalogo troppo anomale per le regole: nome scritto a mano (gli attributi si ricavano comunque)
OVERRIDE = {
    "PSF-CB-800X40-1A-P": "Plenum bocchetta PSF 800x40 mm, 1 attacco Ø150 posteriore, per cartongesso",
    "PSF-CB-800X40-1A-S": "Plenum bocchetta PSF 800x40 mm, 1 attacco Ø150 superiore, per cartongesso",
    "PS2F-MB-1000X50-C-5": "Plenum bocchetta PS2F 1000x50 mm, M-m VMC, L850 - L150, chiuso, per muro",
    "BMA-OV-1200X200": "Bocchetta di mandata a doppia deflessione OV 1200x200 mm, bianca",
    "4COM-R-B": "Kit comandi radio 1 Eternal + 3 Smart, bianco",
}


def analizza(cod, descr):
    """-> (nomev1, {chiave: {valore, num, unita, origine, fonte}})"""
    a = Articolo(cod, descr)
    s = a.prepara()
    s = a.applica_regole(s)
    pezzi = a.tokenizza(s)
    nome = a.componi(pezzi)
    a.attrs_da_attacchi()
    if a.compat:
        a.put("compatibilita", a.compat)
    a.da_codice()
    a.da_sito()
    nome = OVERRIDE.get(a.cod, nome)
    if a.cod == "4COM-R-B":
        a.put("colore", "bianco", orig="codice")
    return nome, a.righe()


if __name__ == "__main__":
    import sys
    for cod in sys.argv[1:]:
        import psycopg2
        c = psycopg2.connect(dbname="db_serio_finale", user="postgres", host="localhost")
        cur = c.cursor()
        cur.execute("select descrizione from materiale where cod_fornitore = %s", (cod,))
        for (d,) in cur.fetchall():
            n, at = analizza(cod, d)
            print(cod, "|", d, "\n   ->", n)
            for k, v in at.items():
                print("     ", k, "=", v["valore"], f"[{v['origine']}]")
