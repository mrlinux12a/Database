# -*- coding: utf-8 -*-
"""Catalogo "Giacomini" (Giacomini SpA: collettori, valvole a sfera, valvole e detentori per radiatori, teste termostatiche
ed elettrotermiche, raccordi a pressare / a compressione / adattatori, tubi multistrato e PE-RT/PEX, sistemi radianti a
pavimento e a soffitto, termoregolazione). 1.758 articoli. I valori vengono dal TESTO della descrizione (origine
`descrizione`), dalla colonna Serie del CSV (solo «a compressione», vedi sotto) e dalle pagine del produttore in
`giacomini_fonti.py` (origine `sito`).

Come si legge la descrizione: «<modello Giacomini> <tipo di prodotto> <specifiche>», in Title Case.
  R553fk Collettore Premontato …   la prima parola con cifre e lettere (R553fk, Rm154-g, P12adb, 315) e' il MODELLO Giacomini
                                   (il codice fornitore comincia con le stesse lettere/cifre) -> tipo_base «modello R553FK»,
                                   scritto in fondo al nomeV1 («…, modello R553FK») e tolto dal nomeV2. Anche Kepp, Kext-ag, Kad
                                   (il codice comincia con quelle lettere). 93 descrizioni non hanno modello.
  Ø3/4"  Ø1"ff  Ø3/4"mf  Ø3/4"m/m  attacco in pollici; m = maschio, f = femmina (-> maschio_femmina, come le parole «Maschio
                                   Femmina», «Femmina Femmina»)
  Ø3/4"e  Ø3/4"ex18                «e» = eurocono (attacco 3/4" eurocono, tipo_raccordo «eurocono»); nel nome «Ø3/4"E»
  Ø1/2"fx20/2  Ø16/2x12  Ø26/3      tubo multistrato «diametro/spessore»: diametro = il primo numero in mm (16/2 -> Ø16 mm)
  Ø16x2mm  Ø12x1,5  (solo TUBI)    diametro x spessore della parete (anche «Tubo 20x2 …» senza Ø dei tubi R977i)
  Ø1"sxx16 / Ø1"dxx16              sx/dx = sinistra/destra (scritto nel nome)
  Tre Derivazioni, 5derivazioni    n_derivazioni (numeri in lettere -> cifre); il Ø dopo «derivazioni» e' l'attacco delle
                                   derivazioni: non diventa attributo (il primo Ø e' l'attacco del collettore)
  Interasse 50                     interasse 50 mm (come Caleffi: «interasse» con il numero e' sempre in mm)
  Sp.13mm (tubi isolati)           coibentazione «isolato, spessore 13 mm»; «Isolato» da solo -> «isolato»
  100m, 50mt, Rotolo 100m          confezione (rotolo di tubo); «Barra 5m», «Barre 4m» -> lunghezza
  Testa elettrotermica … L.1m       lunghezza_cavo (Cavo L.1m; anche «L.1,5m» e «Con Microinterruttore 1m» delle teste)
  Cig Uni 7129                     normativa «CIG, UNI 7129»
  Pressare / A Saldare / Rapido    tipo_raccordo «a pressare» / «a saldare» / «rapido»; Serie «Raccordi A Compressione …» ->
                                   «a compressione» (la descrizione non lo scrive; e' la colonna Serie del catalogo)
  Leva Rossa, Farfalla Verde       comando (leva, farfalla, maniglia, manopola) e colore
  Attacco Rame / Attacco Ferro     compatibilita' «tubo rame» / «tubo ferro» (anche «… Ø1/2"x18 Rame» delle valvole)
  Per Multistrato, Per Tubo Rame   compatibilita' (a quale tubo); «Per R553f», «Per Collettore R551» -> compatibilita' (modello)
Casi lasciati nel nome (ambigui):
  altezze dei pannelli isolanti «H.42», «T50-h42», «H30-eps150» (senza unita': sono mm? altezza totale o dell'isolante?),
  «T50/T100» (passo?), «Eps150/Eps200» (classe dell'EPS), superfici «(17,92 m²)»; «Spessore Alluminio 0,2» dei tubi R999
  (senza unita'); «L.450» e «L.2000» senza unita'; «Base 18» dei rosoni; «Dn13/Dn16» dei kit collegamento (DN non normali);
  «Rs12/Rs16»; «tf» dei kit R460pf; «2mix/1mix», «F-30»; scale dei misuratori di portata («0÷5 l/min») e della sonda
  («-40/150 °C»); i Ø degli accessori (set isolante, kit coibentazione, supporti, cassette, chiavi: e' la misura del collettore
  a cui vanno, non un attacco); «230v-12vdc» dell'alimentatore (entrata/uscita); «12VIE» del collettore R553FP012
  (descrizione troncata); «Ø11"» del set isolante R553w (refuso?).
Correzioni: «Totaleø» -> «totale Ø», «Termofortato/Termofor.» -> termoformato, «Untensile» -> utensile, «Unidici» -> undici,
  «Ø326/3x1"fx32/3» -> «Ø32/3x1"fx32/3» (tee con estremita' uguali, come R569am Ø16/2x1/2"fx16/2), «Pan./Pann.» -> pannello,
  «isol.» -> isolante, «pref.» -> preformato, «lisc.» -> liscio, «gra» -> grafite (R981G come R882G «grafite»), «bugn.» ->
  bugnato, «Rot.» -> in rotolo, «C/» -> con, «P/PAN» -> per pannelli, «Fil.f.» -> filettato femmina, «Ext.» -> esterna,
  «Antivol.» -> antivolatile, «Topmet.» -> Topmeter, «Pert» -> PE-RT, «mt» -> m; code troncate («GIA C», «1200 X 60»)
  tolte.
"""
import re

from ..comuni import F, it, numero
from . import giacomini_fonti

VUOLE_RIGA = True

NUMERI = {"una": 1, "uno": 1, "due": 2, "tre": 3, "quattro": 4, "cinque": 5, "sei": 6, "sette": 7, "otto": 8, "nove": 9,
          "dieci": 10, "undici": 11, "dodici": 12, "tredici": 13, "quattordici": 14}
SIGLE = {"ntc", "usb", "evoh", "eps", "cig", "uni", "rj45", "ptfe", "epdm", "erp", "vmc", "ce", "dc", "ac", "led", "lcd",
         "sx", "dx", "tf", "hdb", "en", "db", "pp-r", "pe-rt", "pex-b", "pex-al-pex", "pex", "abs"}
GRAFIE = {"pe-rt": "PE-RT", "pex-b": "PEX-b", "pex-al-pex": "PEX-AL-PEX", "pp-r": "PP-R", "wi-fi": "Wi-Fi", "erp": "ErP",
          "modbus": "Modbus", "wm-bus": "wM-Bus", "konnex": "Konnex", "walk-by": "walk-by", "o-ring": "O-ring",
          "giacotech": "Giacotech", "giacogreen": "Giacogreen", "klimabus": "KLIMAbus", "klimadomotic": "KLIMAdomotic",
          "honeywell": "Honeywell", "spider": "Spider", "slim": "Slim", "basic": "Basic", "evo": "Evo", "uniflott": "Uniflott",
          "topmeter": "Topmeter", "hydro": "Hydro", "active": "Active", "low": "Low", "high": "High", "flow": "Flow",
          "super": "Super", "classic": "Classic", "cam": "CAM", "multigas": "Multigas"}
NON_MODELLI = {"PROMO", "TUBO", "PANNELLO", "COLLETTORE", "MODULO", "KIT"}
DN_NORMALI = {6, 8, 10, 15, 20, 25, 32, 40, 50, 65, 80, 100, 125, 150, 160, 200, 250, 300}
COLORI = {"bianco": "bianco", "bianca": "bianco", "nero": "nero", "nera": "nero", "rosso": "rosso", "rossa": "rosso",
          "verde": "verde", "blu": "blu", "grigio": "grigio", "grigia": "grigio", "giallo": "giallo", "gialla": "giallo"}
MATERIALI = [  # (regex sul testo minuscolo, testo)
    (r"acciaio\s+inox|inox", "acciaio inox"), (r"acciaio(?!\s+inox)", "acciaio"), (r"ottone", "ottone"), (r"polipropilene\s+random|pp-r", "polipropilene random"),
    (r"tecnopolimero", "tecnopolimero"), (r"pex-al-pex", "PEX-AL-PEX"), (r"pe-rt", "PE-RT"), (r"pex-b", "PEX-b"),
    (r"polietilene", "polietilene"), (r"poliuretanico", "poliuretano"), (r"rame", "rame"), (r"plastica", "plastica"),
    (r"metallic[oa]", "metallo"), (r"eps", "EPS"), (r"cartongesso", "cartongesso")]
TUBI = r"(?:tubo\s+|tubi\s+)?(?:rame|multistrato|plastica|polibutilene|pex|ferro)"
ACCESSORI = r"(?:set isolante|kit coibentazione|coibentazione|coppia coibentazione|supporto|cassetta|chiave|coperchio|guscio|telaio|separatore flusso|cesoia|binario|rosone|vitone|calibratore|molla)"

CORREZIONI = [
    (r"ø", "Ø"), (r"(?<=[a-zà-ù])Ø", " Ø"), (r"''", '"'), (r"\s+(?:GIA C|GIAC)\s*$", ""),
    (r"\buntensile\b", "utensile"), (r"\bunidici\b", "undici"), (r"Ø326/3x", "Ø32/3x"),
    (r"\btermofortato\b", "termoformato"), (r"\btermofor\.\s*", "termoformato "),
    (r"\bpann?\.\s*", "pannello "), (r"\bpann\b", "pannello"), (r"\bisol\.\s*", "isolante "), (r"\bpref\.\s*", "preformato "),
    (r"\blisc\.\s*gra\b", "liscio grafite"), (r"\blisc\.\s*", "liscio "), (r"\bbugn\.\s*", "bugnato "),
    (r"\brot\.\s*", "in rotolo "), (r"\bc/\s*", "con "), (r"\bp/pan\b", "per pannelli"), (r"\bfluss\b", "flussimetro"),
    (r"\bcollet\b", "collettore"), (r"\bfil\.\s*f\.\s*(\d+)x(\d+)\"(\d/\d)", r'filettato femmina Ø\1x\2.\3"'),
    (r"\bfil\.\s*f\.\s*(\d+)x", r"filettato femmina Ø\1x"), (r"\bext\.", "esterna"), (r"\bantivol\.", "antivolatile"),
    (r"\btopmet\.", "Topmeter"), (r"\bpert\b", "pe-rt"), (r"\b(\d+)\s*mt\b", r"\1m"), (r"\bsp\.\s*(?=\d)", "sp."),
    (r"\bumidita'?(?!\w)", "umidità"), (r"\ben\s?(\d{3,5})\b", r"EN \1"), (r'"([mf])xcal(?:otta|\.)\s*', r'"\1 x calotta '),
    (r"(\d)uscita\b", r"\1 uscita"), (r"(?<![\w.,])(\d+(?:,\d+)?)m\b(?=\s+(?:con|per)\b|$)", r"\1 m"), (r"(\d)\s*der\.", r"\1 derivazioni"),
    (r'(Ø\d+/\d+")(\d+)\b', r"\1x\2"), (r"Ø(\d+)-l\.(\d+)", r"Ø\1 L.\2"), (r"\bfugenf\.", "Fugenfüller"),
    (r"(\d)(raccordi|derivazioni|derivazione|zone|uscite|circuiti|termostati|mix)\b", r"\1 \2"),
    (r'(Ø\d+(?:\.\d+/\d+|/\d+)?")(sx|dx)x(\d+)', lambda m: m.group(1) + "x" + m.group(3) + " " +
     {"sx": "sinistra", "dx": "destra"}[m.group(2).lower()]),
    (r'(\d")tf\b', r"\1 TF"), (r"\bmaschio\s+femmina\b", "maschio/femmina"), (r"\bfemmina\s+femmina\b", "femmina/femmina"),
    (r"\bmaschio\s+maschio\b", "maschio/maschio"),
    (r"\b(valvola|valvole|rubinetto) sfera\b", r"\1 a sfera"), (r"\b(valvola|valvole) a sfera squadra\b", r"\1 a sfera a squadra"),
    (r"(?<!\ba )\bpressare\b", "a pressare"), (r"(?<!\ba )\bsaldare\b", "a saldare"),
    (r"\bvalvola (?=sfogo|intercettazione)", "valvola di "), (r"\btubo (\d+(?:,\d+)?x\d)", r"tubo Ø\1"),
    (r"\btubo di ricambio (\d+x\d)", r"tubo di ricambio Ø\1"),
    (r"(?<=\d)m2(?=\d{3})", "m2) "),
]
_CORREZIONI = [(re.compile(a, re.I), b) for a, b in CORREZIONI]

_A, _B, _BASE = "", "", 0xE100
_RX_SEGNA = re.compile(_A + "(.)" + _B)
POLL = r'\d+(?:\.\d+/\d+|/\d+)?"'
GEN = r"(?:m/m|f/f|m/f|f/m|mf|fm|ff|mm|m|f|e)"
MMP = r"\d+(?:,\d+)?(?:/\d+(?:,\d+)?)?"
PARTE = r'(?:%s%s?|%s)' % (POLL, GEN, MMP)
_GEN_TESTO = {"": "", "m": "M", "f": "F", "e": "E", "mf": "M/F", "fm": "F/M", "ff": "F/F", "mm": "M/M", "m/m": "M/M",
              "f/f": "F/F", "m/f": "M/F", "f/m": "F/M"}
_GENERI = {"m": "maschio", "f": "femmina"}
MODELLI = set()                       # modelli del catalogo (da prepara): nel testo restano in maiuscolo


def _pollici(t):
    t = t.rstrip('"')
    if "/" in t:
        intero, fraz = t.split(".", 1) if "." in t else ("0", t)
        a, b = fraz.split("/")
        return float(intero) + float(a) / float(b)
    return float(t)


def _correggi(descr):
    s = " ".join(descr.split())
    s = re.sub(r"\s*\d{3,4}\s*X\s*\d{2,3}\s*$", "", s)          # coda troncata «1200 X 60» (X maiuscola) dei pannelli R981
    for rx, sost in _CORREZIONI:
        s = rx.sub(sost, s)
    return " ".join(s.split())


def _modello(cod, s):
    """-> (modello in maiuscolo o "", resto della descrizione)"""
    m = re.match(r"(\S+)\s+(.*)$", s)
    if not m:
        return "", s
    tok = m.group(1)
    lettere = re.sub(r"[^A-Za-z0-9]", "", tok).upper()
    if tok.upper() in NON_MODELLI or "Ø" in tok or '"' in tok:
        return "", s
    if re.search(r"\d", tok) and re.match(r"[A-Za-z]{0,4}\d", tok):
        return tok.upper(), m.group(2)
    if re.fullmatch(r"[A-Za-z]{3,4}(?:-[A-Za-z]{1,2})?", tok) and cod.upper().startswith(lettere[:4]):
        return tok.upper(), m.group(2)
    return "", s


def prepara(righe):
    MODELLI.clear()
    for cod, descr in righe:
        mod = _modello(cod, _correggi(descr))[0]
        if mod:
            MODELLI.add(mod)
            MODELLI.add(re.sub(r"-.*$", "", mod))


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
        base = re.sub(r"[^\w+-]", "", w).lower()
        if _A in w or not w:
            parole.append(w)
        elif base in GRAFIE:
            parole.append(w.lower().replace(base, GRAFIE[base]))
        elif base in SIGLE or re.sub(r"[^\w./-]", "", w).upper() in MODELLI:
            parole.append(w.upper())
        elif re.search(r"\d", w) and re.search(r"[A-Za-z]", w):
            parole.append(w.upper())
        else:
            parole.append(w.lower())
    s = " ".join(parole)
    s = _RX_SEGNA.sub(lambda m: pezzi[ord(m.group(1)) - _BASE], s)
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s[:1].upper() + s[1:]


def analizza(cod, descr, riga=None):
    st = _Stato()
    modello, s = _modello(cod, _correggi(descr))
    s = re.sub(r"\b(%s)\s+(?=derivazion|valvol|zone|batteri|termostat|stacch|raccordi)" % "|".join(NUMERI),
               lambda m: str(NUMERI[m.group(1).lower()]) + " ", s, flags=re.I)
    tipo = s.lower()
    tubo = bool(re.match(r"tubo\b", tipo)) and not re.match(r"tubo (?:collegamento|maschio)", tipo)
    accessorio = bool(re.match(ACCESSORI, tipo))

    # --- gruppi Ø: il primo (fuori da «per …», non dopo «derivazioni», non negli accessori) da' attacco / diametro ------------
    usato = {"fatto": False}

    def f_od(m):
        gruppo = m.group(0)
        mm_finale = bool(m.group(2))
        corpo = gruppo[1:].strip()
        if mm_finale:
            corpo = re.sub(r"\s?mm$", "", corpo)
        intervallo = "÷" in corpo
        parti = [p for p in re.split(r"\s?[x÷-]\s?Ø?", corpo, flags=re.I) if p]
        sep = [x.lower() for x in re.findall(r"\s?([x÷-])\s?Ø?", corpo, flags=re.I)]
        testi, attacchi, numeri, lettere = [], [], [], []
        for p in parti:
            mp = re.fullmatch(r'(%s)(%s)?' % (POLL, GEN), p, re.I)
            if mp:
                g = (mp.group(2) or "").lower()
                testi.append(mp.group(1) + _GEN_TESTO[g])
                attacchi.append((mp.group(1), g))
                lettere += [c for c in g if c in "mf"]
            else:
                testi.append(p)
                numeri.append(p)
        testo = "Ø" + "".join(t + (sep[i] if i < len(sep) else "") for i, t in enumerate(testi)) + (" mm" if mm_finale else "")
        prima = s_corr[:m.start()]
        fuori = (re.search(r"\b(?:derivazion[ei]|stacch?[oi]|base)\s*$", prima, re.I)
                 or re.search(r"\bper\s+(?:(?!(?:tubo|tubi|multistrato|rame|plastica)\b)\S+\s+){1,3}$", prima, re.I))
        if usato["fatto"] or intervallo or fuori or accessorio:
            return st.segna(testo)
        usato["fatto"] = True
        if attacchi:
            st.metti("attacco", " x ".join(p + {"": "", "e": " eurocono"}.get(g, " " + _GEN_TESTO[g]) for p, g in attacchi),
                     _pollici(attacchi[0][0]), '"')
            if any(g == "e" for _p, g in attacchi):
                st.at["_eurocono"] = True
            if lettere:
                st.at["_gen"] = F("/".join(_GENERI[c] for c in lettere) if len(lettere) > 1 else _GENERI[lettere[0]])
        if numeri:
            d = numeri[0].split("/")
            v = numero(d[0])
            if v > 0:
                st.metti("diametro", it(v) + " mm", v, "mm")
                if tubo:
                    sp = numero(d[1]) if len(d) > 1 else (numero(numeri[1]) if len(numeri) > 1 and not attacchi else None)
                    if sp and v / sp > 3:
                        st.metti("spessore", it(sp) + " mm", sp, "mm")
        return st.segna(testo)
    rx_od = re.compile(r'Ø\s?(%s(?:\s?[x÷-]\s?Ø?%s)*)(\s?mm)?(?![\w"/])' % (PARTE, PARTE), re.I)
    out, pos = [], 0
    s_corr = s
    for m in rx_od.finditer(s):
        out.append(s[pos:m.start()])
        out.append(f_od(m))
        pos = m.end()
    out.append(s[pos:])
    s = "".join(out)

    # --- DN, PN ------------------------------------------------------------------------------------------------------------
    def f_dn(m):
        n = int(m.group(1))
        if n in DN_NORMALI:
            st.metti("dn", "DN%d" % n, float(n), "DN")
        return st.segna("DN%d" % n)
    s = re.sub(r"\bdn\s?(\d+)\b", f_dn, s, flags=re.I)

    # --- derivazioni, interasse ------------------------------------------------------------------------------------------------
    def f_der(m):
        n = int(m.group(1))
        st.metti("n_derivazioni", str(n), float(n))
        return st.segna("%d derivazion%s" % (n, "e" if n == 1 else "i"))
    s = re.sub(r"\b(\d+)\s*derivazion[ei]\b", f_der, s, flags=re.I)

    def f_int(m):
        v = numero(m.group(1))
        st.metti("interasse", it(v) + " mm", v, "mm")
        return "interasse " + st.segna(it(v) + " mm")
    s = re.sub(r"\binterasse\s+(\d+(?:,\d+)?)(?:\s*mm)?\b", f_int, s, flags=re.I)

    # --- tensione, frequenza ----------------------------------------------------------------------------------------------------
    def f_v(m):
        v = numero(m.group(1))
        st.metti("tensione", it(v) + " V", v, "V")
        return st.segna(it(v) + " V")
    s = re.sub(r"(?<![\w.,/-])(\d+(?:,\d+)?)\s*v\b(?!-)", f_v, s, flags=re.I)

    def f_mhz(m):
        st.metti("frequenza", m.group(1) + " MHz", float(m.group(1)) * 1e6, "Hz")
        return st.segna(m.group(1) + " MHz")
    s = re.sub(r"(?<![\w,])(\d+)\s*mhz\b", f_mhz, s, flags=re.I)

    # --- coibentazione dei tubi isolati («Sp.13mm»), cavo delle teste, lunghezze, rotoli, barre ------------------------------------
    isolato = bool(re.search(r"\bisolat[oa]\b", s, re.I)) and tubo

    def f_sp(m):
        v = numero(m.group(1))
        if tubo:
            st.metti("coibentazione", "isolato, spessore %s mm" % it(v))
            return "spessore isolante " + st.segna(it(v) + " mm")
        st.metti("spessore", it(v) + " mm", v, "mm")
        return "spessore " + st.segna(it(v) + " mm")
    s = re.sub(r"\bsp\.(\d+(?:,\d+)?)\s*mm\b", f_sp, s, flags=re.I)
    if isolato or (tubo and "coibentazione" in st.at):
        st.metti("coibentazione", "isolato")

    testa_el = bool(re.match(r"testa elettrotermica", tipo))

    def f_cavo(m):
        v = numero(m.group(1))
        st.metti("lunghezza_cavo", "%s m" % it(v), v * 1000, "mm")
        return "cavo " + st.segna(it(v) + " m")
    if testa_el:
        s = re.sub(r"\b(?:cavo\s+)?(?:l\.\s*)?(\d+(?:,\d+)?)\s*m\b", f_cavo, s, flags=re.I)

    def f_lung(m):
        v, u = numero(m.group(1)), m.group(2).lower()
        st.metti("lunghezza", "%s %s" % (it(v), u), v * {"mm": 1, "cm": 10, "m": 1000}[u], "mm")
        return "lunghezza " + st.segna("%s %s" % (it(v), u))
    s = re.sub(r"(?<![\w.])l\.\s*(\d+(?:,\d+)?)\s*(mm|cm|m)\b", f_lung, s, flags=re.I)

    def f_barra(m):
        v = numero(m.group(1))
        st.metti("lunghezza", "%s m" % it(v), v * 1000, "mm")
        return st.segna("barra da %s m" % it(v))
    s = re.sub(r"\bbarr[ae]\s+(?:da\s+)?(\d+(?:,\d+)?)\s*m\b", f_barra, s, flags=re.I)

    def f_rotolo(m):
        t = "rotolo da %s m" % m.group(1)
        st.metti("confezione", t, numero(m.group(1)), "m")
        return st.segna(t)
    s = re.sub(r"\brotolo\s+(?:da\s+)?(\d+)\s*m\b", f_rotolo, s, flags=re.I)
    if tubo:
        def f_rot2(m):
            t = "%s m" % m.group(1)
            st.metti("confezione", t, numero(m.group(1)), "m")
            return st.segna(t)
        s = re.sub(r"(?<![\w.,÷/-])(\d{2,3})\s*m\b", f_rot2, s, flags=re.I)

    # --- dimensioni, superfici, volumi, peso -----------------------------------------------------------------------------------------
    def f_dim(m):
        nums = [g for g in m.groups()[:3] if g]
        u = m.group(4).lower()
        t = " x ".join(it(numero(g)) for g in nums) + " " + u
        st.metti("dimensioni", t)
        return st.segna(t)
    def f_dimr(m):
        t = "%s x %s x %s÷%s mm" % m.groups()
        st.metti("dimensioni", t)
        return st.segna(t)
    s = re.sub(r"(?<![\w.,/Ø])(\d+)\s*x\s*(\d+)\s*x\s*(\d+)\s*÷\s*(\d+)\s*mm\b", f_dimr, s, flags=re.I)
    s = re.sub(r"(?<![\w.,/Ø])(\d+(?:[.,]\d+)?)\s*x\s*(\d+(?:[.,]\d+)?)(?:\s*x\s*(\d+(?:[.,]\d+)?))?\s*(mm|cm|m)\b", f_dim, s,
               flags=re.I)
    s = re.sub(r"(?<![\w.,/])(\d+(?:[.,]\d+)?)\s*(?:mq|m2)\b", lambda m: st.segna(m.group(1).replace(".", ",") + " m²"), s,
               flags=re.I)

    def f_lt(m):
        v = numero(m.group(1))
        st.metti("confezione", "%s l" % it(v), v, "l")
        return st.segna("%s l" % it(v))
    s = re.sub(r"(?<![\w,÷/-])(\d+(?:,\d+)?)\s*lt\b(?!/)", f_lt, s, flags=re.I)
    s = re.sub(r"(?<![\w,])(\d+(?:,\d+)?)\s*(?:÷|-)\s*(\d+(?:,\d+)?)\s*lt/min\b",
               lambda m: st.segna("%s÷%s l/min" % (m.group(1), m.group(2))), s, flags=re.I)

    def f_kg(m):
        v = numero(m.group(1))
        st.metti("peso", it(v) + " kg", v, "kg")
        return st.segna(it(v) + " kg")
    s = re.sub(r"(?<![\w,])(\d+(?:,\d+)?)\s*kg\b", f_kg, s, flags=re.I)
    s = re.sub(r"(?<![\w.,/÷-])(\d+(?:,\d+)?)\s*(mm|cm)\b", lambda m: st.segna(m.group(1) + " " + m.group(2).lower()), s,
               flags=re.I)
    s = re.sub(r"(-?\d+)/(\d+)\s*°\s*c\b", lambda m: st.segna("%s/%s °C" % m.groups()), s, flags=re.I)
    s = re.sub(r"(?<=\d)°", lambda m: st.segna("°"), s)

    # --- materiale (non dopo «per», «attacco», non il comando «farfalla plastica»), finitura, colore -------------------------------
    basso = s.lower()
    materiali = []
    for rx, testo in MATERIALI:
        for mm_ in re.finditer(r"(?<![\w-])(?:%s)(?![\w-])" % rx, basso):
            prima = basso[:mm_.start()]
            if re.search(r"\b(?:per|attacco)\s+(?:\S+\s+){0,3}$", prima) or re.search(r"\b(?:leva|farfalla|manopola|maniglia)\s+$", prima):
                continue
            if testo == "rame" and not tubo and re.search(r"\b(?:valvola|detentore|gruppo|kit|confezione)\b", tipo):
                continue               # «Ø1/2"x18 Rame» delle valvole = attacco per tubo rame (vedi compatibilita')
            if testo == "metallo" and re.search(r"\bogiva\s+$", prima):
                continue               # «con ogiva metallica»: materiale dell'ogiva, non del raccordo
            if testo == "cartongesso" and not re.match(r"pannello", tipo):
                continue
            if testo not in materiali:
                materiali.append(testo)
    if materiali:
        st.metti("materiale", ", ".join(materiali))
    mf = re.search(r"\b(cromato lucido|cromo lucido|cromo|cromata|cromato|nichelat[oa])\b", s, re.I)
    if mf:
        st.metti("finitura", {"cromata": "cromato", "nichelata": "nichelato"}.get(mf.group(1).lower(), mf.group(1).lower()))
    mc = re.search(r"(?<![\w-])(%s)(?![\w-])" % "|".join(COLORI), s, re.I)
    if mc:
        st.metti("colore", COLORI[mc.group(1).lower()])

    # --- comando, normativa, tipo di raccordo, installazione --------------------------------------------------------------------------
    comandi = []
    if re.match(r"(?:valvola|rubinetto|saracinesca|coppia valvole)", tipo):
        mco = re.search(r"\b(maniglia a (?:farfalla|leva)|leva|farfalla|maniglia|manopola|volantino)\b(?!\s+(?:di|per)\b)", s, re.I)
        if mco:
            comandi.append(mco.group(1).lower())
        if re.search(r"\btaglio a cacciavite\b", s, re.I):
            comandi.append("taglio a cacciavite")
    mn = re.search(r"\bnormalmente\s+(chiusa|aperta)\b", s, re.I)
    if mn:
        comandi.append("normalmente " + mn.group(1).lower())
    if comandi:
        st.metti("comando", ", ".join(comandi))
    norme = []
    if re.search(r"\bcig\b", s, re.I):
        norme.append("CIG")
    mu = re.search(r"\buni\s+(\d{3,5})\b", s, re.I)
    if mu:
        norme.append("UNI " + mu.group(1))
    men = re.search(r"\bEN (\d{3,5})\b", s)
    if men:
        norme.append("EN " + men.group(1))
    if norme:
        st.metti("normativa", ", ".join(norme))
    serie = (riga or {}).get("serie") or ""
    raccordo = bool(re.match(r"(?:\d+ )?(?:raccord|tee|gomito|curva|manicotto|riduzione|tappo)", tipo))
    mr = re.search(r"\b(a pressare|a saldare|rapido)\b", re.sub(r"\bper\b.*$", "", s, flags=re.I), re.I)
    if mr:
        st.metti("tipo_raccordo", mr.group(1).lower())
    elif st.at.get("_eurocono"):
        st.metti("tipo_raccordo", "eurocono")
    elif re.search(r"raccordi a compressione", serie, re.I):
        st.metti("tipo_raccordo", "a compressione")
    elif re.search(r"raccordi a pressare|a pressare per gas", serie, re.I) and raccordo:
        st.metti("tipo_raccordo", "a pressare")
    if re.search(r"a pressare per gas", serie, re.I) and raccordo:
        st.metti("fluidi", "gas")
    mi = re.search(r"\b(incasso filo muro|incasso|filo muro)\b", s, re.I)
    if mi:
        st.metti("installazione", mi.group(1).lower())

    # --- maschio / femmina: parole scritte (fuori da «per …») o lettere dopo il pollice --------------------------------------------
    gen = st.at.pop("_gen", None)
    st.at.pop("_eurocono", None)
    parole = re.findall(r"\b(maschio|femmina)(?:\s*/\s*(maschio|femmina))?\b(?!/filetto)",
                        re.sub(r"\bper\b.*$", "", s, flags=re.I), re.I)
    if re.search(r"/filetto", s, re.I):
        parole = []
    if len(parole) == 1:
        a, b = parole[0]
        st.metti("maschio_femmina", a.lower() + ("/" + b.lower() if b else ""))
    elif not parole and gen is not None and not re.search(r"/filetto", s, re.I):
        st.at["maschio_femmina"] = gen

    nome = _render(s, st.pezzi)

    # --- compatibilita': tubo («per multistrato», «attacco rame») oppure modello Giacomini («per R553f», «per collettore R551») ---
    mtubo = re.search(r"\bper\s+(%s)\b" % TUBI, nome, re.I)
    if mtubo:
        st.metti("compatibilita", mtubo.group(1).lower())
    else:
        ma = re.search(r"\battacco\s+(rame|ferro)\b", nome, re.I) or (
            re.match(r"(?:valvola|detentore)", tipo) and re.search(r"\b(rame|ferro)\b", nome, re.I))
        if ma:
            st.metti("compatibilita", "tubo " + ma.group(1).lower())
    mp = re.search(r"\bper\s+([^,(]+)", nome)
    if mp and "compatibilita" not in st.at:
        parole_p = mp.group(1).split()
        for k, w in enumerate(parole_p[:4]):
            pulita = re.sub(r"[^\w./-]", "", w).upper()
            if pulita in MODELLI or re.sub(r"-.*$", "", pulita) in MODELLI or re.fullmatch(r"[A-Z]{1,3}\d{2,4}[A-Z0-9/-]*", pulita):
                fine = k + 1
                while fine < len(parole_p) and re.fullmatch(r"[A-Z]{1,3}\d[\w/-]*", parole_p[fine]):
                    fine += 1
                st.metti("compatibilita", " ".join(parole_p[:fine]))
                break

    if modello:
        st.metti("tipo_base", "modello " + modello)
        nome = nome.rstrip(" ,") + ", modello " + modello
    return nome, giacomini_fonti.integra(cod, {k: v for k, v in st.at.items() if not k.startswith("_")})
