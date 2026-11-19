# -*- coding: utf-8 -*-
"""Catalogo "Watts" (Watts Industries Italia: sicurezza e controllo per centrale termica, gruppi di rilancio e distribuzione,
manometri, termometri, termostati e cronotermostati). 703 articoli. Tutti i valori vengono dal TESTO della descrizione
(origine `descrizione`); i dati presi dal sito del produttore, se ci sono, sono in `watts_fonti.py`.

Come si legge la descrizione: «<sigla del modello Watts> <tipo di prodotto> <specifiche>», in Title Case.
  Sv Valvola Sicurezza Ordinaria Ø1/2"x3/4" 2,5bar     la sigla iniziale (SV) e' il MODELLO -> tipo_base «modello SV», scritto
                                                      in fondo al nomeV1 («…, modello SV») e tolto dal nomeV2
  Nvfn Flamstop Valvola Intercettazione …            dopo il modello puo' esserci un nome di gamma (Flamstop, Fillmatic,
                                                      Termoflux, Eurovent…): va subito dopo il tipo di prodotto
  M1-abs 63/r Manometro Radiale Ø1/4" 0-10bar …       la sigla comprende anche la grandezza (40, 50, 63, 80, 100, 150): NON si
                                                      legge come diametro della cassa (la descrizione non lo dice): resta nel modello
  … D+c+qk+lf  B/a+c+t+vv+qa+ec  G+qisp  Nk+g+lf      codici delle opzioni Watts (il catalogo non li spiega): restano nel nome,
                                                      in maiuscolo
Valori:
  Ø1/2"x3/4"  Ø1"m  Ø3/4"mf  Ø1/2"ff  Ø1.1/2"fx1"f   attacco (e maschio/femmina; anche le parole «Maschio/femmina»)
  G3/8b  G1/2b                                       attacco G3/8" / G1/2"; la «b» resta nel nome (classe del filetto o codice
                                                      opzione: non si sa)
  valvola di sicurezza «3bar»                        taratura
  valvola di sovrapressione «0,03-0,50bar»           campo_regolazione (come i bypass di Caleffi)
  gruppo (di rilancio e) miscelazione «20-55°c»      campo_regolazione
  «Con capillare 100mm», «capil.100mm», «Capillare L.1300mm»   lunghezza_cavo «capillare 100 mm» (i fratelli scritti senza
                                                      «mm» — «Con Capillare 50 G» — hanno la stessa grafia dei «50mm»: mm)
  DN solo se e' una misura DN normale (6…600): «Dn55/85/93/97/103» degli STS.S non lo sono -> restano nel nome
  «Classe di precisione 0,25»                        accuratezza «classe 0,25»
  «L.200mm», «L.10cm», «L.3m»                        lunghezza
Casi lasciati nel nome (ambigui):
  scale di manometri/termometri/termomanometri («0-10bar», «0-120°c», «0 10m H2o», «0-16» senza unita'): non c'e' un attributo
  «campo di misura» (proposto, non aggiunto); «16bar» dei rubinetti portamanometro e «10bar» delle valvole di ritegno (massima?
  di prova? non e' scritto); «3bar/5bar» dei pressostati; numeri senza unita' («G 100», «Tbx 63 … 100», «Tp … L.35», «30» dei
  Tb 40); «220mm/280mm» dei gruppi Hk e «130mm» dell'adattatore pompa (che cosa misurano?); materiale scritto solo nella sigla
  del modello («Mg1 Inox100», «M1-abs», «S Inox 63»: non e' detto di quale parte sia); «2t/4t» dei termostati fan-coil.
Da segnalare: «Tb-abs 51 Manometro 100-120°c» e «Tirm Abs80 Manometro … 0-120°c» stanno tra termometri/termomanometri ma sono
scritti «Manometro» (lasciato come scritto).
"""
import re

from ..comuni import F, it, numero
from . import watts_fonti

# --- tipi di prodotto: la prima di queste parole apre il nome; quello che c'e' prima e' il modello (e la gamma) -------------
PRODOTTI = (r"valvola|manometro|termomanometro|termometro|bitermostato|microtermostato|cronotermostato|termostato|gruppo|"
            r"rilancio|separatore|defangatore|giunto|guaina|guscio|imbuto|kit|pozzetto|ammortizzatore|vaso|flussostato|"
            r"pressostato|sifone|tronchetto|rubinetto|ricciolo|staffa|serpentina|custodia|molla|collettore|adattatore|"
            r"attuatore|sensore|ripetitore|ricevitore|unit[aà]|modulo|sonda|presa|regolatore|alimentatore|antenna|coppia|scarico")
_RX_PROD = re.compile(r"(?<![\w-])(?:%s)(?![\w-])" % PRODOTTI, re.I)
# nomi di gamma che stanno nella sigla iniziale: vanno dopo il tipo di prodotto (con questa grafia)
GAMME = ["Flow Box Circu", "Milux 2 Weekly", "Battery Electronic", "Flamstop", "Fillmatic", "Termoflux", "Eurovent",
         "Securflux", "Vision"]
# parole della sigla iniziale che non sono modello: dove vanno nel nome
QUALIFICHE = [(r"a pressare", "a pressare", "dopo"), (r"nuovo", "nuovo", "dopo"), (r"ntc", "NTC", "subito"),
              (r"rj45", "RJ45", "subito"), (r"fan-coil (\d)t", "fan-coil \\1T", "dopo")]
SIGLE = {"inail", "ispesl", "epdm", "ntc", "rj45", "rf", "rh", "hc", "fc", "lf", "lw", "nk", "qk", "qisp", "sg", "ort", "abs",
         "ce", "h+", "ve"}
NON_MODELLI = {"AL", "CE", "ABS", "INOX", "FUSS"}   # pezzi di sigla che sono anche parole: in mezzo al testo non si toccano
DN_NORMALI = {6, 8, 10, 15, 20, 25, 32, 40, 50, 65, 80, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500, 600}
MATERIALI = [(r"acciaio\s+inox|inox", "acciaio inox"), (r"ottone", "ottone"), (r"ghisa", "ghisa"), (r"acciaio", "acciaio"),
             (r"rame", "rame"), (r"polipropilene", "polipropilene"), (r"epdm", "EPDM")]
COLORI = {"bianco": "bianco", "bianca": "bianco", "nero": "nero", "nera": "nero"}
COMPAT_PRODOTTI = ["valvola di sicurezza", "gruppo di sicurezza", "idrometro/manometro", "collettori"]

CORREZIONI = [
    (r"ø", "Ø"), (r"(?<=[a-zà-ù°])Ø", " Ø"), (r"''", '"'),
    (r"\bvavola\b", "valvola"), (r"\bgompatto\b", "compatto"), (r"\bunita\b", "unità"), (r"\bdensita'", "densità"),
    (r"\+\s*capil(?:lare|\.)\s*", " con capillare "), (r"\bcapil\.\s*", "capillare "),
    (r"(\d)(raccordi|zone|gruppi)\b", r"\1 \2"), (r"\bporta\s+manometro\b", "portamanometro"),
    (r"\bportamanometro\+flangia\b", "portamanometro con flangia"), (r'(\d")(maschio|femmina)\b', r"\1 \2"),
    (r"\bmaschio\s+femmina\b", "maschio/femmina"), (r"\btre vie\b", "3 vie"), (r"(\d)vie\b", r"\1 vie"),
    (r'\bG(\d+(?:\.\d+)?/\d+)b(?![a-z])', r'G\1" B'), (r'(\d")b(?![a-z])', r"\1 B"),
    (r"\bdn\s+(?=\d+\b(?![\"./]))", "Dn"), (r"(?<=\d)\.(?=\d+\s*m?bar\b)", ","), (r"(\d)\+(\d+)bar\b", r"\1+\2 bar"),
    # forme brevi -> forma piena (come in Caleffi: servono a mettere insieme le famiglie)
    (r"\bvalvola (?=sicurezza|zona|ritegno|bilanciamento|intercettazione|regolazione|sfogo)", "valvola di "),
    (r"\bmiscelatrice settore\b", "miscelatrice a settore"), (r"\bvalvola automatica riempimento\b", "valvola automatica di riempimento"),
    (r"\bvaso (?=espansione)", "vaso di "), (r"\bseparatore aria\b", "separatore d'aria"),
    (r"\bgruppo (?=sicurezza|riempimento|regolazione|collegamento|circolazione|distribuzione|miscelazione)", "gruppo di "),
    (r"\bscarico sicurezza termico\b", "scarico di sicurezza termico"),
]
_CORREZIONI = [(re.compile(a, re.I), b) for a, b in CORREZIONI]

_A, _B, _BASE = "", "", 0xE100
_RX_SEGNA = re.compile(_A + "(.)" + _B)
POLL = r'\d+(?:\.\d+/\d+|/\d+)?"'
GEN = r"(?:mf|fm|ff|mm|m|f)"
_GEN_TESTO = {"": "", "m": "M", "f": "F", "mf": "M/F", "fm": "F/M", "ff": "F/F", "mm": "M/M"}
_GENERI = {"m": "maschio", "f": "femmina"}
MODELLI = set()                       # sigle di modello del catalogo (da prepara): nel testo restano in maiuscolo


def _pollici(t):
    t = t.rstrip('"')
    if "/" in t:
        intero, fraz = t.split(".", 1) if "." in t else ("0", t)
        a, b = fraz.split("/")
        return float(intero) + float(a) / float(b)
    return float(t)


def _correggi(descr):
    s = " ".join(descr.split())
    for rx, sost in _CORREZIONI:
        s = rx.sub(sost, s)
    return " ".join(s.split())


def _dividi(s):
    """-> (modello, gamme, qualifiche [(testo, dove)], corpo)"""
    m = _RX_PROD.search(s)
    pref, corpo = (s[:m.start()].strip(), s[m.start():]) if m else ("", s)
    gamme, qual = [], []
    for g in GAMME:
        rx = re.compile(r"(?<![\w-])%s(?![\w-])" % re.escape(g), re.I)
        if rx.search(pref):
            pref = rx.sub(" ", pref)
            gamme.append(g)
    for rx, t, dove in QUALIFICHE:
        mq = re.search(r"(?<![\w-])%s(?![\w-])" % rx, pref, re.I)
        if mq:
            qual.append((mq.expand(t), dove))
            pref = pref[:mq.start()] + " " + pref[mq.end():]
    if re.match(r"rilancio\b", corpo, re.I):                 # «Hkm20 Rilancio Premontato»: i fratelli scrivono «Gruppo Rilancio»
        corpo = "Gruppo " + corpo
    return " ".join(pref.split()).upper(), gamme, qual, corpo


def prepara(righe):
    MODELLI.clear()
    for _cod, descr in righe:
        modello = _dividi(_correggi(descr))[0]
        for t in re.split(r"[\s/-]+", modello):
            if re.fullmatch(r"[A-Z][A-Z.]{1,5}", t) and t not in NON_MODELLI:
                MODELLI.add(t)


class _Stato:
    def __init__(self):
        self.pezzi, self.at = [], {}

    def segna(self, testo):
        self.pezzi.append(testo)
        return _A + chr(_BASE + len(self.pezzi) - 1) + _B

    def metti(self, chiave, valore, num=None, unita=None):
        self.at.setdefault(chiave, F(valore, "descrizione", num, unita))


def _render(testo, pezzi):
    parole = []
    for w in testo.split(" "):
        base = re.sub(r"[^\w+]", "", w).lower()
        if _A in w or not w:
            parole.append(w)
        elif "+" in w or (re.search(r"\d", w) and re.search(r"[A-Za-z]", w)):
            parole.append(w.upper())
        elif base in SIGLE or re.sub(r"[^\w.]", "", w).upper() in MODELLI:
            parole.append(w.upper())
        elif re.fullmatch(r"[b-df-hj-np-z]", w, re.I):             # lettera sola (codice opzione: G, B, D, R…), non a/e/i/o
            parole.append(w.upper())
        else:
            parole.append(w.lower())
    s = " ".join(parole)
    for g in GAMME:
        s = re.sub(r"(?<![\w-])%s(?![\w-])" % re.escape(g.lower()), g, s)
    s = s.replace("wifi", "Wi-Fi").replace(" h2o", " H2O")
    s = _RX_SEGNA.sub(lambda m: pezzi[ord(m.group(1)) - _BASE], s)
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s[:1].upper() + s[1:]


def analizza(cod, descr):
    st = _Stato()
    modello, gamme, qual, s = _dividi(_correggi(descr))
    tipo = s.lower()

    # --- Ø: attacchi in pollici (il primo gruppo e' l'attacco) e diametri in mm --------------------------------------------
    usato = {"attacco": False}

    def f_od(m):
        p1, g1, p2, g2 = m.group(1), (m.group(2) or "").lower(), m.group(3), (m.group(4) or "").lower()
        parti = [(p1, g1)] + ([(p2, g2)] if p2 else [])
        testo = "Ø" + "x".join(p + _GEN_TESTO[g] for p, g in parti)
        if not usato["attacco"]:
            usato["attacco"] = True
            st.metti("attacco", " x ".join(p + (" " + _GEN_TESTO[g] if g else "") for p, g in parti), _pollici(p1), '"')
            lettere = [c for _p, g in parti for c in g]
            if lettere:
                st.at["_gen"] = F("/".join(_GENERI[c] for c in lettere) if len(lettere) > 1 else _GENERI[lettere[0]])
        return st.segna(testo)
    s = re.sub(r'Ø\s?(%s)(%s)?(?:\s?x\s?Ø?(%s)(%s)?)?(?![\w"])' % (POLL, GEN, POLL, GEN), f_od, s, flags=re.I)

    def f_g(m):
        t = 'G' + m.group(1)
        if not usato["attacco"]:
            usato["attacco"] = True
            st.metti("attacco", t, _pollici(m.group(1)), '"')
            st.metti("filettatura", "G")
        return st.segna(t)
    s = re.sub(r'\bG(%s)' % POLL, f_g, s)

    def f_dmm(m):
        v = numero(m.group(1))
        st.metti("diametro", it(v) + " mm", v, "mm")
        return st.segna("Ø%s mm" % it(v))
    s = re.sub(r"Ø\s?(\d+(?:,\d+)?)(?:\s?mm)?(?![\d\"/.,])", f_dmm, s, flags=re.I)

    # --- DN (solo misure DN normali), PN ---------------------------------------------------------------------------------
    def f_dn(m):
        n = int(m.group(1))
        if n not in DN_NORMALI:
            return st.segna("DN" + m.group(1))
        st.metti("dn", "DN%d" % n, float(n), "DN")
        return st.segna("DN%d" % n)
    s = re.sub(r"\bdn\s?(\d+)\b(?![\"./])", f_dn, s, flags=re.I)
    s = re.sub(r'\bdn\s?(\d+(?:\.\d+/\d+|/\d+)?")(?:÷(\d+(?:\.\d+/\d+|/\d+)?"))?',
               lambda m: st.segna("DN" + m.group(1) + ("÷" + m.group(2) if m.group(2) else "")), s, flags=re.I)

    def f_pn(m):
        t = "PN" + m.group(1) + (m.group(2) or "")
        st.metti("pn", t, None if m.group(2) else numero(m.group(1)), None if m.group(2) else "PN")
        return st.segna(t)
    s = re.sub(r"\bpn\s?(\d+)((?:/\d+)*)\b", f_pn, s, flags=re.I)

    # --- pressioni: taratura delle valvole di sicurezza, campo delle valvole di sovrapressione; le scale restano nel nome -------
    sicurezza = bool(re.match(r"valvola di sicurezza\b", tipo))
    sovrapressione = bool(re.match(r"valvola sovrapressione\b", tipo))

    def f_press(m):
        a, b, u = m.group(1), m.group(2), m.group(3).lower()
        suff = m.group(4) or ""
        if b is not None:
            t = "%s÷%s %s%s" % (it(numero(a)), it(numero(b)), u, suff)
            if sovrapressione:
                st.metti("campo_regolazione", t)
            return st.segna(t)
        t = "%s %s%s" % (it(numero(a)), u, suff)
        if sicurezza:
            st.metti("taratura", t, numero(a) * (0.001 if u == "mbar" else 1.0), "bar")
        return st.segna(t)
    s = re.sub(r"(?<![\w,.+])(\d+(?:,\d+)?)(?:\s*(?:-|÷|\s)\s*(\d+(?:,\d+)?))?\s*(mbar|bar)(/psi)?\b", f_press, s, flags=re.I)
    s = re.sub(r"(?<![\w,.])(\d+(?:,\d+)?)(?:\s*(?:-|÷|\s)\s*(\d+(?:,\d+)?))?\s*m\s?h2o\b",
               lambda m: st.segna(("%s÷%s m H2O" % (m.group(1), m.group(2))) if m.group(2) else m.group(1) + " m H2O"), s, flags=re.I)

    # --- temperature: campo di regolazione dei gruppi di miscelazione; scale dei termometri nel nome ------------------------
    miscela = bool(re.match(r"gruppo (?:di )?(?:rilancio e )?miscelazione\b", tipo))

    def f_temp(m):
        a, b, c = m.group(1), m.group(2), m.group(3)
        u = "°C" if c else "°"
        t = "%s÷%s %s" % (a, b, u)
        if miscela and c:
            st.metti("campo_regolazione", "%s÷%s °C" % (a, b))
        return st.segna(t)
    s = re.sub(r"(?<![\w,.])(-?\d+)\s*(?:÷|/|-(?=\+?\d)|\s+(?=\+?\d)|(?=\+))\s*(\+?\d+)\s*°\s*(c\b)?", f_temp, s, flags=re.I)

    # --- portata, potenza, Kvs, tensione, frequenza, IP, vie, volume ----------------------------------------------------------
    def f_port(m):
        v = numero(m.group(1))
        st.metti("portata", "%s m³/h" % it(v), v, "m³/h")
        return st.segna("%s m³/h" % it(v))
    s = re.sub(r"(?<![\w,])(\d+(?:,\d+)?)\s*m3/h\b", f_port, s, flags=re.I)

    def f_pot(m):
        v = numero(m.group(1))
        st.metti("potenza", "%s kW" % it(v), v, "kW")
        return st.segna("%s kW" % it(v))
    s = re.sub(r"(?<![\w,])(\d+(?:,\d+)?)\s*kw\b", f_pot, s, flags=re.I)
    s = re.sub(r"(?<![\w,])(\d+(?:,\d+)?)\s*kvs\b|\bkvs\s*(\d+(?:,\d+)?)\b",
               lambda m: st.segna("Kvs " + (m.group(1) or m.group(2))), s, flags=re.I)

    def f_v(m):
        st.metti("tensione", m.group(1) + " V", float(m.group(1)), "V")
        return st.segna(m.group(1) + " V")
    s = re.sub(r"(?<![\w.,/-])(\d+)\s*v\b", f_v, s, flags=re.I)

    def f_mhz(m):
        st.metti("frequenza", m.group(1) + " MHz", float(m.group(1)) * 1e6, "Hz")
        return st.segna(m.group(1) + " MHz")
    s = re.sub(r"(?<![\w,])(\d+)\s*mhz\b", f_mhz, s, flags=re.I)

    def f_ip(m):
        st.metti("grado_ip", "IP" + m.group(1))
        return st.segna("IP" + m.group(1))
    s = re.sub(r"\bip\s?(\d{2})\b", f_ip, s, flags=re.I)

    def f_vie(m):
        st.metti("vie", m.group(1), float(m.group(1)))
        return st.segna(m.group(1) + " vie")
    s = re.sub(r"\b(\d)\s*vie\b", f_vie, s, flags=re.I)

    def f_vol(m):
        v = numero(m.group(1))
        st.metti("volume_acqua", it(v) + " l", v, "l")
        return st.segna(it(v) + " l")
    s = re.sub(r"(?<![\w,])(\d+(?:,\d+)?)\s*lt\b", f_vol, s, flags=re.I)

    # --- capillare, lunghezze, classe di precisione ---------------------------------------------------------------------------
    def f_cap(m):
        v = numero(m.group(1))
        st.metti("lunghezza_cavo", "capillare %s mm" % it(v), v, "mm")
        return "capillare " + st.segna("%s mm" % it(v))
    s = re.sub(r"\bcapillare\s+(?:l\.\s*)?(\d+(?:,\d+)?)(?:\s*mm\b)?", f_cap, s, flags=re.I)

    def f_lung(m):
        v, u = numero(m.group(1)), m.group(2).lower()
        st.metti("lunghezza", "%s %s" % (it(v), u), v * {"mm": 1, "cm": 10, "m": 1000}[u], "mm")
        return "lunghezza " + st.segna("%s %s" % (it(v), u))
    s = re.sub(r"(?<![\w.])l\.\s*(\d+(?:,\d+)?)\s*(mm|cm|m)\b", f_lung, s, flags=re.I)

    def f_cl(m):
        st.metti("accuratezza", "classe " + m.group(1))
        return "classe di precisione " + st.segna(m.group(1))
    s = re.sub(r"\bclasse di precisione\s+(\d+(?:,\d+)?)", f_cl, s, flags=re.I)
    s = re.sub(r"(?<![\w.,÷/])(\d+(?:,\d+)?)\s*÷\s*(\d+(?:,\d+)?)\s*mm\b", lambda m: st.segna("%s÷%s mm" % m.groups()), s, flags=re.I)
    s = re.sub(r"(?<![\w.,÷/])(\d+(?:,\d+)?)\s*(mm)\b", lambda m: st.segna(m.group(1) + " mm"), s, flags=re.I)

    # --- materiale (solo nel testo, non nella sigla del modello; non dopo «per»), finitura, colore -------------------------------
    basso = s.lower()
    materiali = []
    for rx, testo in MATERIALI:
        for mm_ in re.finditer(r"(?<![\w-])(?:%s)(?![\w-])" % rx, basso):
            if re.search(r"\bper\s+(?:\S+\s+){0,2}$", basso[:mm_.start()]):
                continue
            if testo == "acciaio" and re.match(r"acciaio\s+inox", basso[mm_.start():]):
                continue
            if testo not in materiali and not any(testo in x for x in materiali):
                materiali.append(testo)
    if materiali:
        st.metti("materiale", ", ".join(materiali))
    mf = re.search(r"\b(cromo|cromato|zincato)\b", s, re.I)
    if mf:
        st.metti("finitura", mf.group(1).lower())
    mc = re.search(r"(?<![\w-])(%s)(?![\w-])" % "|".join(COLORI), s, re.I)
    if mc:
        st.metti("colore", COLORI[mc.group(1).lower()])

    # --- normativa, fluidi, comando, raccordo, installazione -------------------------------------------------------------------
    norme = [t for rx, t in ((r"inail", "INAIL"), (r"ispesl", "ISPESL")) if re.search(r"(?<![\w+-])%s(?![\w-])" % rx, s, re.I)]
    if norme:
        st.metti("normativa", ", ".join(norme))
    if re.search(r"\bper gas\b", s, re.I):
        st.metti("fluidi", "gas")
    comandi = [c for c in ("riarmo manuale", "blocco manuale") if re.search(r"\b%s\b" % c, s, re.I)]
    if comandi:
        st.metti("comando", ", ".join(comandi))
    mr = re.search(r"\b(flangiato|filettato|a pressare)\b", s, re.I)
    if mr or any(t == "a pressare" for t, _ in qual):
        st.metti("tipo_raccordo", mr.group(1).lower() if mr else "a pressare")
    mi = re.search(r"\b(a muro|a parete|incasso)\b", s, re.I)
    if mi:
        st.metti("installazione", mi.group(1).lower())

    # --- maschio / femmina: parole scritte (fuori da «per …») o lettere dopo il pollice ---------------------------------------
    gen = st.at.pop("_gen", None)
    parole = re.findall(r"\b(maschio|femmina)(?:\s*/\s*(maschio|femmina))?\b", re.sub(r"\bper\b.*$", "", s, flags=re.I), re.I)
    if len(parole) == 1:
        a, b = parole[0]
        st.metti("maschio_femmina", a.lower() + ("/" + b.lower() if b else ""))
    elif not parole and gen is not None:
        st.at["maschio_femmina"] = gen

    # --- gamma e qualifiche dentro il nome: dopo il tipo di prodotto (prima di misure, «con», «per», materiali) -----------------
    for t, dove in qual:
        if dove == "subito":
            s = re.sub(r"^(\S+)", lambda m: m.group(1) + " " + t, s, count=1)
    dopo = [t for t, dove in qual if dove == "dopo" and t != "a pressare"] + gamme
    if any(t == "a pressare" for t, _ in qual):
        s = re.sub(r"^(\S+)", r"\1 a pressare", s, count=1)
    if dopo:
        mt = re.search(r"\s(?=%s|\d|con\b|per\b|senza\b|in\b|ottone|inox|acciaio|rame|radiale|posteriore|compatto|filettato|"
                       r"flangiato|maschio|femmina|$)" % _A, s + " ", re.I)
        pos = mt.start() if mt else len(s)
        s = (s[:pos].rstrip() + " " + " ".join(dopo) + " " + s[pos:].lstrip()).strip()

    nome = _render(s, st.pezzi)

    # --- compatibilita': «per <modello Watts>» (anche con il tipo davanti: «per termometro TB») o un accessorio noto ------------
    mp = re.search(r"\bper\s+([^,]+)", nome)
    if mp:
        parole_p = mp.group(1).split()
        valore = None
        if mp.group(1).lower().startswith("tubi "):
            valore = mp.group(1).strip()
        elif any(mp.group(1).lower().startswith(c) for c in COMPAT_PRODOTTI):
            valore = next(mp.group(1)[:len(c)] for c in COMPAT_PRODOTTI if mp.group(1).lower().startswith(c))
        else:
            for k, w in enumerate(parole_p[:4]):
                pulita = re.sub(r"[^\w.-]", "", w).upper()
                if pulita in MODELLI or (re.search(r"\d", w) and re.search(r"[A-Z]{2}", w) and not re.match(r"DN|Ø", w)):
                    fine = k + 1
                    while fine < len(parole_p) and re.fullmatch(r"[A-Z][A-Z0-9+]{0,4}", parole_p[fine]) \
                            and not re.match(r"DN\d", parole_p[fine]):
                        fine += 1
                    valore = " ".join(parole_p[:fine])
                    break
        if valore:
            st.metti("compatibilita", valore)

    if modello:
        st.metti("tipo_base", "modello " + modello)
        nome = nome.rstrip(" ,") + ", modello " + modello
    return nome, watts_fonti.integra(cod, {k: v for k, v in st.at.items() if not k.startswith("_")})
