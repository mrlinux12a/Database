# -*- coding: utf-8 -*-
"""Catalogo "Aquatechnik" (Aquatechnik Group SpA: Fusio-Technik PP-R, Safety-Plus PPSU, Multi-Calor, Multi-Gas, attrezzature).

Tutti i valori di questo modulo vengono dal TESTO della descrizione (origine `descrizione`): niente schede del sito qui
(vedi `aquatechnik_fonti.py` per i dati di famiglia presi dal sito del produttore).

Come si legge la descrizione (formati del catalogo):
  Ø63mm  Ø16  Ø63-75mm  Ø14÷32mm            diametro (mm; senza unita' = mm, come nelle descrizioni "sorelle" dello stesso catalogo)
  Ø26x18x26mm  Ø20x16x20mm                   diametri delle estremita' (raccordi ridotti, collettori)
  Ø1/2"mx16mm  Ø26x3"fx26mm  Ø3/4"f          filetto in pollici (m = maschio, f = femmina) e diametro del tubo in mm
  Ø25/3,5mm  Ø25x4,2mm  (solo nei TUBI)      diametro / spessore parete; coerenza controllata con l'SDR (SDR = Ø / spessore)
  Per Tubo Ø63-75mm                          compatibilita' (a quale tubo si applica), NON diametro dell'articolo
  Sdr7,4  Sdr 11  Pn10/16                    SDR, PN
  Rotolo 50m / Barra 4m                      confezione / lunghezza
Casi ambigui lasciati come scritti (nessun attributo): `Lega` (di cosa?), `Per Esterno`, `H.77` e `L.370xh.280mm` senza unita'
chiara, `D.90`, `M10`, `18v/2a`, `230v-18v`, doppie indicazioni maschio/femmina che si contraddicono.
"""
import re

from ..comuni import F, it, numero
from . import aquatechnik_fonti

# --- nomi di linee/prodotti da scrivere con la maiuscola ---------------------------------------------------------------
LINEE = ["Fusio-Technik", "Fusio Technik", "Safety-Plus", "Multi-Calor", "Multi-Gas", "Isoline-Plus", "Isoline", "Multirapid",
         "Rain-Water", "Fiber-Light", "Fiber-Cond", "Fiber-T", "Faser", "Fires", "Uvres", "Jolly", "Safety", "Switch", "Prisma",
         "Plus"]
GAMME = {"fusio-technik": "Fusio-Technik", "fusio technik": "Fusio-Technik", "safety-plus": "Safety-Plus",
         "multi-calor": "Multi-Calor", "multi-gas": "Multi-Gas"}
# sigle/modelli degli attrezzi (in maiuscolo) usati nel catalogo
MODELLI = {"bmm", "bst", "bbs", "bcb", "hts", "bbr", "pae", "ctr", "cps", "mc", "ras", "tr", "el", "ctm", "pr", "cm"}
MATERIALI = [  # (regex, testo)
    (r"pp-rct", "PP-RCT"), (r"pp-r", "PP-R"), (r"ppsu", "PPSU"), (r"pps", "PPS"), (r"pp", "PP"), (r"abs", "ABS"),
    (r"epdm", "EPDM"), (r"polipropilene", "polipropilene"), (r"ottone", "ottone"), (r"alluminio", "alluminio"),
    (r"elastomero", "elastomero"), (r"bronzo", "bronzo"), (r"acciaio\s+zincato", "acciaio zincato"), (r"acciaio", "acciaio"),
    (r"plastica", "plastica"), (r"metallo", "metallo")]
COLORI = {"bianco": "bianco", "giallo": "giallo", "verde": "verde", "blu": "blu", "rosso": "rosso", "rossa": "rosso",
          "azzurro": "azzurro", "nero": "nero", "grigio": "grigio"}
ARTICOLI_COMANDO = r"(?:valvola|rubinetto)"
TOKEN_COMPAT = re.compile(r"[A-Za-z0-9/\-÷]+")                     # una parola o un codice: "Bmm", "094", "21350/22336", "32-bst"
PAROLE_STOP = set(COLORI) | {"con", "senza", "da", "di", "e", "in", "a", "cromato", "saldare"}   # qui finisce la compatibilita'

# --- private-use: segnaposto per i pezzi gia' riconosciuti --------------------------------------------------------------
_A, _B, _BASE = "", "", 0xE100
_RX_SEGNA = re.compile(_A + "(.)" + _B)

N = r"\d+(?:[.,]\d+)?"
PART = r'\d+(?:\.\d+/\d+|/\d+)?"?[mfMF]?|\d+(?:[.,]\d+)?(?:/\d+(?:[.,]\d+)?)?'
RX_OD = re.compile(r"Ø\s*(?P<body>[^\s+]+)(?P<extra>\+\w+)?", re.I)
RX_PARTE_POLLICI = re.compile(r'^(\d+(?:\.\d+/\d+|/\d+)?)"(m/f|[mf])?$', re.I)
RX_PARTE_NUM = re.compile(r"^\d+(?:[.,]\d+)?$")
RX_PARTE_RANGE = re.compile(r"^\d+(?:[.,]\d+)?(?:[-÷]\d+(?:[.,]\d+)?)+$")
RX_PARTE_SLASH = re.compile(r"^(\d+(?:[.,]\d+)?)/(\d+(?:[.,]\d+)?)$")


def _pollici(t):
    """'1.1/4' -> 1.25 ; '3/4' -> 0.75 ; '3' -> 3.0"""
    t = t.replace(",", ".")
    if "/" in t:
        intero, frazione = (t.rsplit(".", 1) if "." in t.split("/")[0] else ("0", t))
        a, b = frazione.split("/")
        return float(intero) + float(a) / float(b)
    return float(t)


class _Stato:
    def __init__(self):
        self.pezzi = []
        self.at = {}

    def segna(self, testo):
        self.pezzi.append(testo)
        return _A + chr(_BASE + len(self.pezzi) - 1) + _B

    def metti(self, chiave, valore, num=None, unita=None):
        self.at.setdefault(chiave, F(valore, "descrizione", num, unita))


def _render(testo, pezzi):
    """minuscolo (tranne i pezzi riconosciuti), modelli/sigle in maiuscolo, linee con la maiuscola, segnaposto sciolti."""
    parole = []
    for w in testo.split(" "):
        if _A in w:
            parole.append(w)
            continue
        base = re.sub(r"[^\w]", "", w)
        if re.search(r"\d", w) and re.search(r"[A-Za-z]", w):
            parole.append(w.upper())                                  # modelli e sigle con cifre (BST32, M10, D.90)
        else:
            parole.append(w.lower())
    s = " ".join(parole)
    s = re.sub(r"\b(%s)\b" % "|".join(sorted(MODELLI)), lambda m: m.group(1).upper(), s)
    for linea in LINEE:
        s = re.sub(r"(?<![\w-])%s(?![\w-])" % re.escape(linea.lower()), linea, s)
    s = s[:1].upper() + s[1:] if s and s[0] != _A else s
    s = _RX_SEGNA.sub(lambda m: pezzi[ord(m.group(1)) - _BASE], s)
    return s[:1].upper() + s[1:]


def _gruppo_od(st, s, m, tubo, sdr):
    """Legge un gruppo `Ø...` e restituisce (testo segnaposto, ruolo). Ruoli: diametro | compat | uscita | None (non capito)."""
    body = m.group("body")
    extra = m.group("extra")
    unita_mm = False
    corpo = body
    if re.search(r"mm$", corpo, re.I):
        corpo, unita_mm = corpo[:-2], True
    elif re.search(r"\d$", corpo):
        unita_mm = False                                              # senza unita': si legge come mm (vedi docstring)
    parti = re.split(r"x", corpo, flags=re.I)
    letti = []                                                        # (tipo, testo, valore)
    for p in parti:
        mp = RX_PARTE_POLLICI.match(p)
        if mp:
            letti.append(("pollici", mp.group(1), mp.group(2)))
        elif RX_PARTE_NUM.match(p):
            letti.append(("mm", p, None))
        elif RX_PARTE_RANGE.match(p):
            letti.append(("range", p, None))
        elif RX_PARTE_SLASH.match(p):
            letti.append(("slash", p, None))
        else:
            return None
    # testo del gruppo come lo scriviamo nel nome
    pezzi_txt = []
    for tipo, t, g in letti:
        pezzi_txt.append('%s"%s' % (t, g.upper() if g else "") if tipo == "pollici" else t)
    mm_presente = any(t != "pollici" for t, _, _ in letti)
    testo = "Ø" + "x".join(pezzi_txt) + (" mm" if (unita_mm or mm_presente) and mm_presente else "")
    return letti, testo, extra


VUOLE_RIGA = True                      # riceve anche Linea/Serie del CSV (la gamma e' nella Linea: "060 Fusio-Technik")
LINEA_GAMMA = [("fusio-technik", "Fusio-Technik"), ("safety plus", "Safety-Plus"), ("safety-plus", "Safety-Plus"),
               ("multi-calor", "Multi-Calor"), ("multi-gas", "Multi-Gas"), ("safety", "Safety")]


def analizza(cod, descr, riga=None):
    st = _Stato()
    s = " ".join(descr.split())
    # --- refusi e abbreviazioni del catalogo ---------------------------------------------------------------------
    s = re.sub(r"\bacciao\b", "acciaio", s, flags=re.I)
    s = re.sub(r"\bfemimna\b", "femmina", s, flags=re.I)
    s = re.sub(r"\bflang\.", "flangiata", s, flags=re.I)
    s = re.sub(r"\bfusio technik\b", "Fusio-Technik", s, flags=re.I)

    tubo = bool(re.match(r"^(?:\S+\s+){0,3}tubo\b", s, re.I)) and not re.search(r"\bper tubo", s[:s.lower().find("tubo") + 5], re.I)

    # --- SDR e PN ---------------------------------------------------------------------------------------------------
    sdr = None

    def f_sdr(m):
        nonlocal sdr
        v = numero(m.group(1).replace(".", ",") if "." in m.group(1) and "," not in m.group(1) else m.group(1))
        sdr = v
        t = "SDR " + it(v)
        st.metti("sdr", t, v, "SDR")
        return st.segna(t)
    s = re.sub(r"\bsdr\s*(\d+(?:[.,]\d+)?)", f_sdr, s, flags=re.I)

    def f_pn(m):
        t = "PN" + m.group(1) + ("/" + m.group(2) if m.group(2) else "")
        st.metti("pn", t, None if m.group(2) else float(m.group(1)), None if m.group(2) else "PN")
        return st.segna(t)
    s = re.sub(r"\bpn\s*(\d+)(?:/(\d+))?\b", f_pn, s, flags=re.I)

    # --- tubi Faser "Fires40 - 5.5" / "63 - 8,6": diametro e spessore, accettati solo se coerenti con l'SDR ------------
    if tubo and sdr:
        def f_fires(m):
            d, e = numero(m.group(1)), numero(m.group(2).replace(".", ","))
            if e > 0 and abs(d / e - sdr) / sdr <= 0.05:
                st.metti("diametro", it(d) + " mm", d, "mm")
                st.metti("spessore", it(e) + " mm", e, "mm")
                return st.segna("Ø%s/%s mm" % (it(d), it(e)))
            return st.segna(m.group(0))
        s = re.sub(r"(?<![\w/.])(\d+)\s*-\s*(\d+[.,]\d+)\s*$", f_fires, s)

    # --- gruppi Ø ------------------------------------------------------------------------------------------------------
    usati = {"diametro": False, "uscita": False}

    def f_od(m):
        prima = s_corrente[0][:m.start()].lower()
        letto = _gruppo_od(st, s_corrente[0], m, tubo, sdr)
        if letto is None:
            return st.segna(m.group(0))
        parti, testo, extra = letto
        if re.search(r"\bper tubo(?: multistrato)?\s*$", prima):               # a quale tubo si applica
            multi = " multistrato" if re.search(r"multistrato\s*$", prima) else ""
            st.metti("compatibilita", "tubo%s %s" % (multi, testo), None, None)
            return st.segna(testo) + (" con " + m.group("extra")[1:] if extra else "")
        if re.search(r"\d\s*uscit[ae](?:\s+a\s+(?:destra|sinistra))?\s*$", prima) and usati["diametro"]:
            mm = [t for k, t, _ in parti if k == "mm"]
            if mm:
                st.metti("attacco", "uscite Ø%s mm" % mm[0], numero(mm[0]), "mm")
            return st.segna(testo)
        if usati["diametro"]:
            return st.segna(m.group(0))                                                       # secondo Ø non previsto: resta com'e'
        # diametro / pollici / spessore
        numerici = [(k, t) for k, t, _ in parti if k in ("mm", "range", "slash")]
        pollici = [(t, g) for k, t, g in parti if k == "pollici"]
        if numerici and numerici[0][0] == "slash":
            if not tubo:
                return st.segna(m.group(0))
            d, e = [numero(x) for x in numerici[0][1].split("/")]
            if sdr and abs(d / e - sdr) / sdr > 0.08:                               # incoerente con l'SDR: non lo metto
                return st.segna(m.group(0))
            st.metti("diametro", it(d) + " mm", d, "mm")
            st.metti("spessore", it(e) + " mm", e, "mm")
        elif (tubo and len(parti) == 2 and parti[0][0] == "mm" and parti[1][0] == "mm"
              and numero(parti[0][1]) / numero(parti[1][1]) > 3):               # tubo "Ø25x4,2": diametro x spessore
            d, e = numero(parti[0][1]), numero(parti[1][1])
            if sdr and abs(d / e - sdr) / sdr > 0.08:
                return st.segna(m.group(0))
            st.metti("diametro", it(d) + " mm", d, "mm")
            st.metti("spessore", it(e) + " mm", e, "mm")
        elif numerici:
            if len(numerici) == 1 and numerici[0][0] == "mm":
                st.metti("diametro", it(numero(numerici[0][1])) + " mm", numero(numerici[0][1]), "mm")
            elif numerici[0][0] == "range":
                st.metti("diametro", numerici[0][1] + " mm", None, "mm")
            else:
                st.metti("diametro", " x ".join(it(numero(t)) for _, t in numerici) + " mm", numero(numerici[0][1]), "mm")
        if pollici:
            testi, visti = [], set()
            for t, g in pollici:
                voce = '%s" %s' % (t, g.upper()) if g else '%s"' % t
                if voce not in visti:
                    visti.add(voce)
                    testi.append(voce)
            st.metti("attacco", " / ".join(testi), _pollici(pollici[0][0]), '"')
            generi = []
            for _, g in pollici:
                if g and g.lower() not in generi:
                    generi.append(g.lower())
            if generi:
                nomi_gen = {"m": "maschio", "f": "femmina", "m/f": "maschio/femmina"}
                st.at.setdefault("_gen_filetto", F("/".join(nomi_gen[g] for g in generi)))
        usati["diametro"] = True
        return st.segna(testo) + (" con " + extra[1:] if extra else "")

    s_corrente = [s]
    # la funzione f_od legge `s_corrente` (testo completo) per sapere cosa precede il gruppo
    out, ultimo = [], 0
    for m in RX_OD.finditer(s):
        out.append(s[ultimo:m.start()])
        s_corrente[0] = "".join(out)                                                # testo gia' elaborato prima del gruppo
        out.append(f_od(_Spostato(m, len(s_corrente[0]))))
        ultimo = m.end()
    out.append(s[ultimo:])
    s = "".join(out)

    # --- materiale ---------------------------------------------------------------------------------------------------
    m_esc = re.search(r"\bper\s+(?:collare|tubi|valvole)\b", s, re.I)
    fine_ok = m_esc.start() if m_esc else len(s)
    sigillante = bool(re.search(r"\bsigillante\b", s, re.I))
    materiali = []
    for rx, testo in MATERIALI:
        def f_mat(m, testo=testo):
            if m.start() < fine_ok and not sigillante and not re.search(r"cassetta\s+(?:in\s+)?$", s[:m.start()], re.I):
                if testo not in materiali:
                    materiali.append(testo)
            return st.segna(testo)
        s = re.sub(r"(?<![\w-])%s(?![\w-])" % rx, f_mat, s, flags=re.I)
    if materiali:
        st.metti("materiale", ", ".join(materiali))

    # --- finitura e colore -------------------------------------------------------------------------------------------
    def f_cromato(m):
        if not re.search(r"rosone\s*$", s_prima(m)):
            st.metti("finitura", "cromato")
        return m.group(0)

    def s_prima(m):
        return m.string[:m.start()]
    re.sub(r"\bcromato\b", f_cromato, s, flags=re.I)

    def f_colore(m):
        st.metti("colore", COLORI[m.group(1).lower()])
        return m.group(0)
    re.sub(r"(?<![\w-])(%s)(?![\w-])" % "|".join(COLORI), f_colore, s, flags=re.I)

    # --- comando (valvole e rubinetti: con leva / maniglia / volantino / farfalla / cappuccio) --------------------------
    if re.search(r"\b%s\b" % ARTICOLI_COMANDO, s, re.I):
        mc = re.search(r"(?:\bcon\b|\+)\s*(leva|maniglia|volantino|farfalla|cappuccio)\b", s, re.I)
        if mc:
            st.metti("comando", mc.group(1).lower())

    # --- modo di giunzione: a saldare ----------------------------------------------------------------------------------
    if not re.search(r"\bmatric[ei]\b", s, re.I):
        ms = re.search(r"\bsaldare(\s+testa/testa)?", s, re.I)
        if ms:
            st.metti("tipo_raccordo", "a saldare testa/testa" if ms.group(1) else "a saldare")
    s = re.sub(r"(?<!\ba )(?<!\bper )(?<!\bmatrice )(?<!\bda )\bsaldare\b", "a saldare", s, flags=re.I)

    # --- uscite, attacchi, installazione --------------------------------------------------------------------------------
    def f_uscite(m):
        n = int(m.group(1))
        st.metti("n_derivazioni", "%d uscite" % n, float(n), "uscite")
        return st.segna("%d uscite" % n)
    s = re.sub(r"\b(\d+)\s*uscite\b", f_uscite, s, flags=re.I)

    def f_attacchi(m):
        st.metti("n_derivazioni", "%s attacchi" % m.group(1), None, "attacchi")
        return st.segna("%s attacchi" % m.group(1))
    s = re.sub(r"\b(\d+-\d+)\s+attacchi\b", f_attacchi, s, flags=re.I)
    for parola in ("incasso", "sottomuro"):
        if re.search(r"\b%s\b" % parola, s, re.I):
            st.metti("installazione", parola)

    # --- lunghezze, dimensioni, contenuti ------------------------------------------------------------------------------
    def f_rotolo(m):
        t = "rotolo da %s m" % m.group(1)
        st.metti("confezione", t, numero(m.group(1)), "m")
        return st.segna(t)
    s = re.sub(r"\brotolo\s+(?:da\s+)?(\d+(?:[.,]\d+)?)\s*m\b", f_rotolo, s, flags=re.I)

    def f_barra(m):
        v = numero(m.group(1))
        st.metti("lunghezza", "%s m" % it(v), v * 1000, "mm")
        return st.segna("barra da %s m" % it(v))
    s = re.sub(r"\bbarra\s+(?:da\s+)?(\d+(?:[.,]\d+)?)\s*m\b", f_barra, s, flags=re.I)

    def f_lung(m):
        if m.group(2):
            st.metti("lunghezza", m.group(1) + m.group(2)[0:0] + "÷" + m.group(2) + " mm", None, "mm")
            return st.segna("lunghezza %s÷%s mm" % (m.group(1), m.group(2)))
        v = numero(m.group(1))
        st.metti("lunghezza", it(v) + " mm", v, "mm")
        return st.segna("lunghezza %s mm" % it(v))
    s = re.sub(r"(?<![\w.])L\.(\d+(?:[.,]\d+)?)(?:÷(\d+(?:[.,]\d+)?))?\s*mm\b(?!\s*[xX])", f_lung, s)

    def f_dim(m):
        v = [numero(g) for g in m.groups() if g]
        t = " x ".join(it(x) for x in v) + " mm"
        st.metti("dimensioni", t)
        return st.segna("x".join(it(x) for x in v) + " mm")
    s = re.sub(r"(?<![\w.])(%s)\s*[xX]\s*(%s)(?:\s*[xX]\s*(%s))?\s*mm\b" % (N, N, N), f_dim, s)
    # misure con sigla ma senza unita' sicura: restano come scritte (spaziate)
    s = re.sub(r"\bL\.(\d+)xh\.(\d+)mm\b", lambda m: st.segna("L.%sxh.%s mm" % (m.group(1), m.group(2))), s)
    s = re.sub(r"\bH\.(\d+)xl\.(\d+)xs\.(\d+)\b", lambda m: st.segna("H.%s x l.%s x s.%s" % m.groups()), s)

    def f_cont(m):
        v = numero(m.group(1))
        u = {"ml": "ml", "lt": "l", "l": "l", "g": "g", "gr": "g", "kg": "kg"}[m.group(2).lower()]
        t = "%s %s" % (it(v), u)
        st.metti("confezione", t, v, u)
        return st.segna(t)
    s = re.sub(r"(?<![\w.,/])(\d+(?:[.,]\d+)?)\s*(ml|lt|gr|kg|g|l)\b(?![\w/])", f_cont, s, flags=re.I)

    def f_tens(m):
        st.metti("tensione", m.group(1) + " V", float(m.group(1)), "V")
        return st.segna(m.group(1) + " V")
    s = re.sub(r"(?<![\w.,/-])(\d+)\s*v\b(?![/-]\d)", f_tens, s, flags=re.I)

    # --- compatibilita': "per <codici / modelli>" ------------------------------------------------------------------------
    ultimo_per = None
    for mper in re.finditer(r"\bper\s+", s, re.I):
        ultimo_per = mper
    if ultimo_per and "compatibilita" not in st.at:
        coda = s[ultimo_per.end():]
        token, fine = [], 0
        for tk in re.finditer(r"\S+", coda):
            if _A in tk.group(0) or not TOKEN_COMPAT.fullmatch(tk.group(0)) or tk.group(0).lower() in PAROLE_STOP:
                break
            token.append(tk.group(0))
            fine = tk.end()
        testo = coda[:fine]
        if token and re.search(r"\d{2,}", testo):
            st.metti("compatibilita", _render(testo, st.pezzi))

    # --- maschio / femmina ---------------------------------------------------------------------------------------------
    def _parole_genere(t):
        return re.findall(r"\b(maschio|femmina)(?:\s*/\s*(maschio|femmina))?\b", t, re.I)
    corpo_gen = re.sub(r"\bper\b.*$", "", s, flags=re.I)
    trovate = _parole_genere(corpo_gen)
    gen_filetto = st.at.pop("_gen_filetto", None)
    if len(trovate) == 1:
        a, b = trovate[0]
        parola = a.lower() + ("/" + b.lower() if b else "")
        if gen_filetto is None or gen_filetto["valore"] == parola:
            st.metti("maschio_femmina", parola)
        # se la parola e il filetto non coincidono: ambiguo, nessun valore
    elif not trovate and gen_filetto is not None:
        st.at["maschio_femmina"] = gen_filetto

    # --- gamma (linea di prodotto scritta nella descrizione) ---------------------------------------------------------------
    mg = re.search(r"(?<![\w-])(fusio-technik|safety-plus|multi-calor|multi-gas)(?![\w-])", s, re.I)
    if mg:
        st.metti("tipo_base", GAMME[mg.group(1).lower()])
    elif re.match(r"safety\b", s, re.I):
        st.metti("tipo_base", "Safety")
    if "tipo_base" not in st.at and riga and riga.get("linea"):          # gamma dalla colonna Linea del catalogo
        linea = riga["linea"].lower()
        for chiave, gamma in LINEA_GAMMA:
            if chiave in linea:
                st.metti("tipo_base", gamma)
                break

    # --- ultimi ritocchi al testo ---------------------------------------------------------------------------------------
    s = re.sub(r"\s*\+\s*", " con ", s)
    nome = _render(s, st.pezzi)
    return aquatechnik_fonti.integra(cod, descr, nome, {k: v for k, v in st.at.items() if not k.startswith("_")})


class _Spostato:
    """Un Match con le posizioni riferite al testo gia' elaborato (serve a f_od per leggere cosa precede il gruppo)."""
    def __init__(self, m, inizio):
        self._m, self._inizio = m, inizio

    def group(self, k=0):
        return self._m.group(k)

    def start(self):
        return self._inizio
