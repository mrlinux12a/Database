# -*- coding: utf-8 -*-
"""Catalogo "Caleffi" (Caleffi SpA: valvole, collettori, miscelatori, stabilizzatori Autoflow, raccordi, componenti gas, solare...).

Tutti i valori di questo modulo vengono dal TESTO della descrizione (origine `descrizione`); i dati di famiglia presi dal sito
del produttore sono in `caleffi_fonti.py`.

Come si legge la descrizione (formati del catalogo):
  127 Stabilizzatore ...           il numero iniziale e' la SERIE Caleffi (3245 articoli su 3255 hanno il codice che comincia
                                   con lo stesso numero; il catalogo stesso scrive "Per Serie 7200", "Per Collettori Serie 349-350")
                                   -> tipo_base "serie 127" (anche con suffisso: 120l, 391s1, 5350..h, 6443-3by)
  Ø3/4"  Ø1"f  Ø1/2"mf  Ø1"ff      attacco filettato in pollici (Caleffi scrive Ø anche per i filetti); m = maschio, f = femmina
  Ø1/2"fx3/4"f  Ø3/4"mx22          attacchi delle due estremita' (pollici x pollici, pollici x Ø tubo in mm)
  Ø23/1,5  23P1,5  Ø28 P.1,5        attacco metrico "23 p.1,5" (filetto dei collettori e dei raccordi Caleffi)
  Ø18  Ø40mm  Ø16x2,25             diametro in mm (tubo o pezzo)
  Dn50  Dn20x1"m  Dn32-ø1''        DN (e attacco)
  2derivazioni  4+2derivazioni      derivazioni del collettore (n_derivazioni); "Ø..." dopo le derivazioni = attacco delle derivazioni
  Interasse 125 / Int.125          interasse in mm (il catalogo scrive anche "Interasse 125mm")
Pressioni e temperature: il valore entra solo dove il tipo di articolo dice che cosa e':
  valvola (di) sicurezza "3bar"                         -> taratura
  "Pressione Max 2bar"                                  -> pressione
  pressostato / bypass differenziale / regolatore pressione differenziale "1÷5bar" "5-25mca" "250÷600mbar"
                                                        -> campo_regolazione
  miscelatore / comando termostatico / termostato "30÷65°c"  -> campo_regolazione
  termostato / valvola combustibile / scarico termico / anticondensa "98°c" "55°"  -> taratura
Casi ambigui lasciati come scritti (nessun attributo):
  scale di manometri, termometri, idrometri ("0÷10bar", "0÷120°c"), campo di lavoro Autoflow "22÷210kpa", "Kv3,2",
  "5m"/"10m" delle valvole di intercettazione combustibile (non dice che cosa misura), "200÷800" senza unita',
  "500x1000x110÷150" senza unita', "Ø50"..."Ø150" dei Discaldirt (diametro o DN?), "Sfogo aria ... 5bar" e "Separatore aria
  ... 3bar" (pressione massima o di scarico? non si sa), "L.120/210" senza unita', materiale della maglia dei filtri.
"""
import re

from ..comuni import F, it, numero
from . import caleffi_fonti

VUOLE_RIGA = True

# --- nomi di gamma (Caleffi) con la grafia giusta: se aprono la descrizione vanno dopo il tipo di prodotto ----------------
GAMME = ["Solarincal-T", "Solarincal", "Solarnocal", "Solar", "Ballstop", "Dynamical", "Legiomix Evo", "Legiomix",
         "Legioflow", "Darcal", "Discaldirt", "Discalair", "Discal Slim", "Discal", "Dirtmagplus", "Dirtmagclean", "Dirtmag Slim",
         "Dirtmag",
         "Dirtcal", "Minical", "Aercal", "Robocal", "Valcal", "Wical", "Sepcoll", "Istop", "Filterstop", "Plurimod Easy",
         "Plurimod", "Conteca Easy Ultra", "Conteca Easy", "Conteca", "Geo", "XF", "Autoflow", "Flowmatic", "Aquastop",
         "Discaslim", "Hed"]
_GAMME_RX = re.compile(r"^(%s)\s+" % "|".join(re.escape(g) for g in GAMME), re.I)
_GAMMA_GRAFIA = {g.lower(): g for g in GAMME}
# sigle che restano in maiuscolo
SIGLE = {"ptfe", "epdm", "aisi", "gpl", "usb", "pwm", "ispesl", "inail", "icim", "ce", "ral", "ba", "cb", "nhs", "rs485",
         "rsp", "upml", "xf", "pt1000", "ntc", "led", "gsm", "lcd", "na", "nc", "rm", "eu", "ca", "hed", "uni"}
MATERIALI = [  # (regex sul testo minuscolo, testo)
    (r"acciaio\s+inox|inox", "acciaio inox"), (r"aisi\s*304", "acciaio inox AISI 304"), (r"ottone", "ottone"),
    (r"ghisa", "ghisa"), (r"bronzo", "bronzo"), (r"tecnopolimero", "tecnopolimero"), (r"acciaio", "acciaio"),
    (r"alluminio", "alluminio"), (r"rame", "rame"), (r"plastica", "plastica"), (r"polipropilene", "polipropilene"), (r"epdm", "EPDM")]
COLORI = {"bianco": "bianco", "bianca": "bianco", "nero": "nero", "nera": "nero", "giallo": "giallo", "gialla": "giallo",
          "rosso": "rosso", "rossa": "rosso", "blu": "blu", "verde": "verde", "grigio": "grigio", "grigia": "grigio",
          "azzurro": "azzurro", "lilla": "lilla"}
TUBI = r"(?:tubo\s+|tubi\s+(?:in\s+)?)?(?:rame|ferro|multistrato|polietilene)"

# --- correzioni del testo: refusi, abbreviazioni, descrizioni troncate in maiuscolo (regex, sostituzione) ---------------------
CORREZIONI = [
    (r"Ý", "Ø"), (r"ø", "Ø"), (r'(?<![\d./Ø])(\d)"(\d/\d)\b', r'Ø\1.\2"'), (r"''", '"'), (r'\\"', '"'), (r"\b2 4V\b", "24V"), (r"\bTESTA 2 00\b", "TESTA 200"),
    (r"\bcolletore\b", "collettore"), (r"\badatatore\b", "adattatore"), (r"\btremperatura\b", "temperatura"),
    (r"\bcodulo\b", "codolo"), (r"\bportata(?=\d)", "portata "), (r"\bdir\b(?!\.)", "diritto"), (r"°ccon\b", "°c con"), (r"pressione(\d)", r"pressione \1"), (r"\bvalvolasfera\b", "valvola a sfera"),
    (r"\bvalvolaantiaspirazione\b", "valvola antiaspirazione"), (r"cassettaØ", "cassetta Ø"), (r"\bautoflow(\d)", r"autoflow \1"),
    (r"\bsquadraferro\b", "squadra ferro"), (r"\bferroprereg\.", "ferro prereg."),
    # abbreviazioni (anche delle descrizioni in maiuscolo)
    (r"\bstabiliz\.\s*port\.", "stabilizzatore di portata"), (r"\bstabiliz\.\s*autom\.", "stabilizzatore automatico"),
    (r"\bstabilizz\.\s*automatico\b", "stabilizzatore automatico"), (r"\bacc\.\s*inox\b", "acciaio inox"),
    (r"\bderiv\.", "derivazioni"), (r"\bbocchett\.", "bocchettone"), (r"\bguarniz\.", "guarnizione"),
    (r"\bcoll\.\s*geot\.", "collettore geotermico"), (r"\bcollett\.", "collettore"), (r"\bcoll\.", "collettore"),
    (r"\breg\.\s*dig\.", "regolatore digitale"), (r"\bdig\.", "digitale"), (r"\brisc\.", "riscaldamento"),
    (r"\braffr\.", "raffrescamento"), (r"\brubin\.\s*sfera\b", "rubinetto a sfera"), (r"\binterc\.", "intercettazione"),
    (r"\bacqua san\.", "acqua sanitaria"), (r"\busc\.\s*imp\.", "uscita impulsiva"), (r"\bricam\.", "ricambio "),
    (r"\bric\.", "ricambio"), (r"\+\s*or\b", " con O-ring"), (r"\bmc/h\b", "m3/h"),
    (r"\bvalv\.\s*term\.\s*dx\s*\+\s*det\.\s*sx\b", "valvola termostatizzabile destra + detentore sinistro"),
    (r"\bvalv?\.\s*det\.\s*test\.\s*", "valvola + detentore + testa termostatica "),
    (r"\bvalv\s*\+\s*det\s*\+\s*testa term\.\s*", "valvola + detentore + testa termostatica "),
    (r"\bvalv\s*\+\s*det\b", "valvola + detentore"), (r"\bsq\.", "squadra "), (r"\bdir\.", "diritto "),
    (r"\bc/\s*preregol\b", "con preregolazione"), (r"\bprereg\.", "con preregolazione"), (r"\bram\b", "rame"),
    (r"\bgr\.\s*term\.", "gruppo di regolazione termostatica"), (r"\bgr\.\s*reg\.", "gruppo di regolazione"),
    (r"\bracc\.\s*pressare\b", "raccordo a pressare"), (r"\brid\.\s*press\.", "riduttore di pressione"),
    (r"\bincl\.\s*\+\s*att\.\s*manom\.", "inclinato con attacco manometro"), (r"\bcoib\.", "coibentato"),
    (r"\bscentr\.", "scentrato"), (r"\bcr$", "cromato"), (r"\bisp\.\s*c/int\.ne\b", "ispezionabile con intercettazione"),
    (r"\bvalv\.\s*int\.ne\s*sf\.", "valvola di intercettazione a sfera"), (r"\bflang\.\s*(?=\d)", "flangiato "),
    (r"\belettroterm\.", "elettrotermico"), (r"\bmod\.\s*ut\.", "modulo utenza"), (r"\bs/cont\.", "senza contatore"),
    (r"\bsat\.$", "satellite"), (r"\bs/bocch\b", "senza bocchettoni"), (r"\bc/sc\.", "con scarico"),
    (r"\bc/", "con "), (r"\bs/", "senza "), (r"\bvalv\.", "valvola "), (r"\bna/rm\b", "normalmente aperta riarmo manuale"),
    (r"(\d)\s*p\.?(1,5)\b", r"\1/\2"), (r"(\d)(punti)\b", r"\1 \2"), (r"\bart\.\s*(?=\d)", "art. "),
    (r"(\d+(?:,\d+)?)\s*kv\b", r"Kv \1"), (r"\bkv\s*(?=\d)", "Kv "),
    (r'(Ø\d+(?:\.\d+/\d+|/\d+)?")-(?=\d+(?:,\d+)?[÷x])', r"\1 - "), (r"(Ø\d+/1,5)-(?=\d)", r"\1 - "),
    (r"(?<=\d)(?=[a-z]{5,}\b)", " "),                                     # 3punti, 1stadio, 4ispezioni (r"\bx(\d+)\s*sp\.\s*(1,5)\b", r"x\1/\2"),
    # forme brevi -> forma piena (servono anche a mettere insieme le famiglie)
    (r"\bvalvola (?=sicurezza|zona|ritegno|bilanciamento|intercettazione|regolazione|sfogo)", "valvola di "),
    (r"\bvalvola (?=sfera|settore|farfalla|pistone|globo)", "valvola a "),
    (r"\brubinetto (?=sfera)", "rubinetto a "), (r"\briduttore (?=pressione)", "riduttore di "),
    (r"\bregolatore (?=pressione|flusso)", "regolatore di "), (r"\bvaso (?=espansione)", "vaso di "),
    (r"\bgruppo (?=riempimento|regolazione|collegamento|circolazione|distribuzione|commutazione)", "gruppo di "),
    (r"\bfiltro y\b", "filtro a Y"), (r"\bseparatore aria\b", "separatore d'aria"),
    (r"\bvalvola di sicurezza temperatura/pressione\b", "valvola di sicurezza temperatura e pressione"),
]
_CORREZIONI = [(re.compile(a, re.I), b) for a, b in CORREZIONI]

# --- segnaposto (caratteri privati) per i pezzi gia' riconosciuti: non vengono toccati dal resto delle regole -------------------
_A, _B, _BASE = "", "", 0xE100
_RX_SEGNA = re.compile(_A + "(.)" + _B)
N = r"\d+(?:[.,]\d+)?"
POLLICI = r'\d+(?:\.\d+/\d+|/\d+)?"'
_RX_POLL = re.compile(r'^(\d+(?:\.\d+/\d+|/\d+)?)"(mf|fm|ff|mm|m|f)?$', re.I)
_RX_FILM = re.compile(r"^(\d+)/(1,5)(m|f)?$", re.I)                         # 23/1,5 = attacco 23 p.1,5
_RX_MM = re.compile(r"^(\d+(?:,\d+)?)(?:/(\d+(?:,\d+)?))?(mm)?$", re.I)    # 18 · 20/2,5 · 40mm
_RX_RANGE = re.compile(r"^\d+(?:,\d+)?÷\d+(?:,\d+)?$")
_GENERI = {"m": "maschio", "f": "femmina"}


def _pollici(t):
    """'1.1/4' -> 1.25 ; '3/4' -> 0.75 ; '3' -> 3.0"""
    if "/" in t:
        intero, fraz = t.split(".", 1) if "." in t else ("0", t)
        a, b = fraz.split("/")
        return float(intero) + float(a) / float(b)
    return float(t)


class _Stato:
    def __init__(self):
        self.pezzi, self.at = [], {}

    def segna(self, testo):
        self.pezzi.append(testo)
        return _A + chr(_BASE + len(self.pezzi) - 1) + _B

    def metti(self, chiave, valore, num=None, unita=None):
        self.at.setdefault(chiave, F(valore, "descrizione", num, unita))


def _render(testo, pezzi):
    """minuscolo (tranne i pezzi riconosciuti), modelli/sigle in maiuscolo, gamme con la loro grafia, segnaposto sciolti."""
    parole = []
    for w in testo.split(" "):
        if _A in w:
            parole.append(w)
            continue
        base = re.sub(r"[^\w]", "", w).lower()
        if re.fullmatch(r"[\d,.÷]+(?:x[\d,.÷]+)+", w, re.I):                 # 500x600x110÷140: misure, x minuscola
            parole.append(w.lower())
        elif base == "kv":
            parole.append("Kv")
        elif re.search(r"\d", w) and re.search(r"[A-Za-z]", w):
            parole.append(w.upper())
        elif base in SIGLE:
            parole.append(w.upper())
        else:
            parole.append(w.lower())
    s = " ".join(parole)
    for g in sorted(GAMME, key=len, reverse=True):
        s = re.sub(r"(?<![\w-])%s(?![\w-])" % re.escape(g.lower()), g, s)
    s = re.sub(r"\bm bus\b", "M-Bus", s)
    s = re.sub(r"\bo-ring\b", "O-ring", s)
    s = re.sub(r"\b(pompa (?:alta efficienza )?)(yonos|para|stratos|wilo)\b", lambda m: m.group(1) + m.group(2).capitalize(), s)
    s = re.sub(r"\b(a|ad|foratura) ([tly])\b", lambda m: m.group(1) + " " + m.group(2).upper(), s)
    s = _RX_SEGNA.sub(lambda m: pezzi[ord(m.group(1)) - _BASE], s)
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s[:1].upper() + s[1:]


def _leggi_od(corpo):
    """Legge il corpo di un gruppo Ø (senza la Ø).  -> lista di parti (tipo, testo, genere) oppure None se non si capisce."""
    corpo = re.sub(r"(?i)xØ", "x", corpo)
    parti = []
    for p in re.split(r"(?i)x(?=[\dmf])", corpo):
        if not p:
            return None
        mp = _RX_POLL.match(p)
        if mp:
            parti.append(("pollici", mp.group(1), (mp.group(2) or "").lower()))
            continue
        if p.lower() in ("m", "f"):                                    # Ø3/4"fxm: stessa misura, altro genere
            parti.append(("genere", "", p.lower()))
            continue
        mf = _RX_FILM.match(p)
        if mf:
            parti.append(("metrico", "%s p.%s" % mf.groups()[:2], (mf.group(3) or "").lower()))
            continue
        mm = _RX_MM.match(p)
        if mm:
            parti.append(("mm", mm.group(1) + ("/" + mm.group(2) if mm.group(2) else ""), ""))
            continue
        if _RX_RANGE.match(p):
            parti.append(("range", p, ""))
            continue
        # misure alternative: 1/2"-3/4" · 3/4"÷2" · 1"-dn20 · 1.1/2"-2"-dn50 · 3/4"-10,5÷11
        alt = re.split(r"[-÷]", p)
        if len(alt) > 1 and all(re.fullmatch(r'\d+(?:\.\d+/\d+|/\d+)?"|dn\d+', a, re.I) for a in alt):
            parti.append(("alternative", p, ""))
            continue
        return None
    return parti


def _testo_od(parti):
    """Il gruppo come si scrive nel nome (senza spazi dentro, cosi' v2.pulisci lo riconosce)."""
    out = []
    for tipo, t, g in parti:
        if tipo == "pollici":
            out.append(t + '"' + {"": "", "m": "M", "f": "F", "mf": "M/F", "fm": "F/M", "ff": "F/F", "mm": "M/M"}[g])
        elif tipo == "genere":
            out.append(g.upper())
        elif tipo == "metrico":
            out.append(t.replace(" p.", "/") + g.upper())
        elif tipo == "alternative":
            out.append(re.sub(r"(?i)dn(\d+)", r"DN\1", t))
        else:
            out.append(t)
    s = "Ø" + "x".join(out)
    if (any(tp in ("mm", "range") for tp, _, _ in parti) and not s.lower().endswith("mm")
            and not any(tp in ("pollici", "metrico") for tp, _, _ in parti)):
        s += " mm"
    return s.replace("mm mm", "mm")


def _genere(parti):
    lettere = []
    for tipo, _, g in parti:
        if tipo in ("pollici", "genere", "metrico") and g:
            lettere.extend(list(g))
    if not lettere:
        return None
    if len(lettere) == 1:
        return _GENERI[lettere[0]]
    return "/".join(_GENERI[x] for x in lettere)


def analizza(cod, descr, riga=None):
    st = _Stato()
    s = " ".join(descr.split())
    tutto_maiuscolo = s == s.upper()
    # codice ripetuto nella descrizione ("F0007669 RICAM.TAPPO ...", "... 145664 1H8")
    for c in sorted({cod, cod.split()[0]}, key=len, reverse=True):
        if c and len(c) >= 5:
            s = re.sub(r"(?:^|\s)%s(?=\s|$)" % re.escape(c), " ", s, flags=re.I).strip()
    s = re.sub(r"\s+CAL$", "", s)
    for rx, sost in _CORREZIONI:
        s = rx.sub(sost, s)
    s = " ".join(s.split())
    if tutto_maiuscolo:                                    # descrizioni troncate: misure in pollici scritte senza "
        s = re.sub(r"(?<![\w/.\"Ø])(1?1/[248]|3/[48])(f)?(?![\w/\"])", lambda m: 'Ø%s"%s' % (
            m.group(1).replace("11/", "1.1/"), (m.group(2) or "").lower()), s, flags=re.I)
        s = re.sub(r'(Ø[\d./]+"f) X F\b', r"\1xf", s)                       # 11/4F X F
        s = re.sub(r'(?<![\w/.Ø"])(\d)"', r'Ø\1"', s)                          # AUTOFLOW 1"
        s = re.sub(r"\b[xX]\s+(?=[A-Za-z]{2,}|\d{3,})", "per ", s)          # "X GEO", "X 536" = per
    s = re.sub(r"Ø\s+(?=\d)", "Ø", s)
    s = re.sub(r'(?<![\w/.Ø"-])(\d(?:\.\d)?/\d+)"', r'Ø\1"', s)                # TEST.3/8" -> Ø3/8"
    s = re.sub(r"\bnp t\b", "NPT", s, flags=re.I)

    # --- serie (numero iniziale) ---------------------------------------------------------------------------------------------
    serie = None
    ms = re.match(r"^(\d{3,5})((?:\.\.\.?|-\d)?[a-z]{0,3}\d?)\s+(?=\D)", s, re.I)
    if ms:
        cifre = re.sub(r"^[A-Z]+", "", cod.upper())
        if cifre.startswith(ms.group(1)) or len(ms.group(1)) <= 4:
            serie = ms.group(1) + ms.group(2).upper()
            s = s[ms.end():]
    # --- gamma in testa: dopo il tipo di prodotto -------------------------------------------------------------------------
    mg = _GAMME_RX.match(s)
    if mg and not re.match(r"^(?:kit|ricambio)\b", s[mg.end():], re.I):
        gamma, resto = mg.group(1), s[mg.end():]
        mt = re.search(r"\s(?=Ø|dn\s?\d|\d|con\b|per\b|senza\b|ottone|ghisa|bronzo|inox|acciaio|tecnopolimero|"
                       r"cromo|cromato|coibentat|\(|$)", " " + resto, re.I)
        pos = max(mt.start() - 1, 0) if mt else len(resto)
        if pos == 0:
            s = resto + " " + gamma if resto else gamma
        else:
            s = resto[:pos].rstrip() + " " + gamma + " " + resto[pos:].lstrip()
        s = s.strip()
    # valvole e kit "... Ø3/8" Ferro", "SQUADRA RAME": attacco per tubo ferro / rame (le serie sorelle scrivono "Per Ferro")
    if re.match(r"(?:kit\s+)?(?:valvola|detentore|coppia valvole)", s, re.I):
        s = re.sub(r"(?<!per )\b(ferro|rame)\b", r"per \1", s, flags=re.I)
    # spazio dopo il genere del filetto attaccato a una parola: Ø3/8"sinistra
    s = re.sub(r'(\d")([mf]{0,2})([a-z]{3,})', r"\1\2 \3", s, flags=re.I)

    # --- DN (anche DN + attacco: Dn20x1"m, Dn50xø2.3/4"m, Dn32-ø1") --------------------------------------------------------
    s = re.sub(r"\b(dn\s*\d+)\s*[x-]\s*Ø?(?=\d+(?:\.\d+/\d+|/\d+)?\")", r"\1 Ø", s, flags=re.I)

    def f_dn(m):
        a, b = m.group(1), m.group(2)
        if b:
            t = "DN%s÷DN%s" % (a, b) if m.group(0).count("÷") else "DN%s-%s" % (a, b)
            st.metti("dn", t)
        else:
            t = "DN" + a
            st.metti("dn", t, float(a), "DN")
        return st.segna(t)
    s = re.sub(r"\bdn\s*(\d+)(?:\s*(?:/|-|÷)\s*(?:dn)?\s*(\d+))?\b", f_dn, s, flags=re.I)

    # --- PN ----------------------------------------------------------------------------------------------------------------
    def f_pn(m):
        t = "PN" + m.group(1) + (m.group(2) or "")
        if m.group(2):
            st.metti("pn", t)
        else:
            st.metti("pn", t, numero(m.group(1)), "PN")
        return st.segna(t)
    s = re.sub(r"\bpn\s*(\d+(?:,\d+)?)((?:[/÷]\d+(?:,\d+)?)*)\b", f_pn, s, flags=re.I)

    # --- gruppi Ø -----------------------------------------------------------------------------------------------------------
    discaldirt = bool(re.search(r"\bdiscaldirt\b", s, re.I))
    usati = {"attacco": False}
    out, ultimo = [], 0
    for m in re.finditer(r"Ø\s?((?:[^\s,()]|,(?=\d))+)", s):
        out.append(s[ultimo:m.start()])
        ultimo = m.end()
        prima = "".join(out).lower()
        parti = _leggi_od(m.group(1))
        if parti is None or (discaldirt and all(t == "mm" for t, _, _ in parti)):
            out.append(st.segna("Ø" + m.group(1)))
            continue
        testo = _testo_od(parti)
        poll = [t + '"' + (" " + {"m": "M", "f": "F", "mf": "M/F", "fm": "F/M", "ff": "F/F", "mm": "M/M"}[g] if g else "")
                for tipo, t, g in parti if tipo == "pollici"]
        metr = [t + (" " + g.upper() if g else "") for tipo, t, g in parti if tipo == "metrico"]
        alt = [t for tipo, t, _ in parti if tipo == "alternative"]
        mm = [t for tipo, t, _ in parti if tipo in ("mm", "range")]
        if usati["attacco"] and re.search(r"(?:derivazioni|attacchi|circuiti|uscite)\W*$", prima):
            if poll or metr:                                                  # attacco delle derivazioni
                v = st.at.get("attacco")
                if v and "derivazioni" not in v["valore"]:
                    v["valore"] += ", derivazioni " + " x ".join(poll + metr)
            out.append(st.segna(testo))
            continue
        if not usati["attacco"] and (poll or metr or alt):
            if alt and not poll and not metr:
                a = alt[0]
                dn = re.findall(r"(?i)dn(\d+)", a)
                a_poll = re.sub(r"(?i)-?dn\d+", "", a)
                if dn:
                    st.metti("dn", "DN" + dn[0], float(dn[0]), "DN")
                if a_poll:
                    prime = re.match(r'(\d+(?:\.\d+/\d+|/\d+)?)"', a_poll)
                    st.metti("attacco", a_poll.replace("-", " - ").replace("÷", " ÷ "),
                             _pollici(prime.group(1)) if prime else None, '"' if prime else None)
            else:
                prime = [t for tipo, t, _ in parti if tipo == "pollici"]
                st.metti("attacco", " x ".join(poll + metr), _pollici(prime[0]) if prime else None, '"' if prime else None)
            g = _genere(parti)
            if g:
                st.at["_gen_filetto"] = F(g)
            usati["attacco"] = True
            if mm and "diametro" not in st.at:
                d = mm[0]
                n0 = re.match(r"\d+(?:,\d+)?", d).group(0)
                st.metti("diametro", d.replace("/", "x") + " mm", numero(n0) if "÷" not in d else None, "mm")
            out.append(st.segna(testo))
            continue
        if mm and "diametro" not in st.at:                                   # solo misure in mm: diametro
            d = mm[0]
            tutte = [t for tipo, t, _ in parti if tipo in ("mm", "range")]
            n0 = re.match(r"\d+(?:,\d+)?", d).group(0)
            valore = "x".join(tutte).replace("/", "x")
            st.metti("diametro", valore + " mm", numero(n0) if "÷" not in d else None, "mm")
            out.append(st.segna(testo))
            continue
        out.append(st.segna(testo))                                          # gruppo capito ma senza ruolo: solo scritto bene
    out.append(s[ultimo:])
    s = "".join(out)

    # --- pressioni ------------------------------------------------------------------------------------------------------------
    sicurezza = bool(re.match(r"(?:ricambio\s+)?valvola di sicurezza\b", s, re.I)) and not re.search(r"\btemperatura\b", s[:40], re.I)
    if re.match(r"(?:ricambio\s+)?valvola di sicurezza (?:temperatura e pressione|combinata)", s, re.I):
        sicurezza = True
    regolatore_p = bool(re.match(r"(?:pressostato|valvola (?:di )?bypass|by-pass|regolatore di pressione differenziale)", s, re.I))
    UNITA_P = {"bar": ("bar", 1.0), "mbar": ("mbar", 0.001), "mca": ("m c.a.", 0.0980665), "kpa": ("kPa", 0.01)}

    def f_press(m):
        a, b, u = m.group(1), m.group(2), m.group(3).lower()
        testo_u, fatt = UNITA_P[u]
        if b:
            t = "%s÷%s %s" % (it(numero(a)), it(numero(b)), testo_u)
            if regolatore_p:
                st.metti("campo_regolazione", t)
                return st.segna(t)
            return st.segna(t)                                                     # scala o campo di lavoro: resta nel nome
        t = "%s %s" % (it(numero(a)), testo_u)
        prima = m.string[:m.start()].lower()
        if re.search(r"pressione max\s*$", prima):
            st.metti("pressione", t, round(numero(a) * fatt, 4), "bar")
        elif sicurezza:
            st.metti("taratura", t, round(numero(a) * fatt, 4), "bar")
        return st.segna(t)
    s = re.sub(r"(?<![\w,])(\d+(?:,\d+)?)(?:\s*[÷-]\s*(\d+(?:,\d+)?))?\s*(mbar|bar|mca|kpa)\b", f_press, s, flags=re.I)

    # --- temperature ----------------------------------------------------------------------------------------------------------
    campo_t = bool(re.match(r"(?:valvola miscelatrice termostatica|miscelatore|comando termostatico|termostato|bitermostato|"
                            r"gruppo di regolazione termostatica|regolatore termostatico)", s, re.I))
    taratura_t = bool(re.match(r"(?:termostato|valvola di intercettazione combustibile|valvola (?:di )?scarico|valvola anticondensa|"
                               r"gruppo ricircolo anticondensa|ricambio valvola di sicurezza)", s, re.I))
    anticondensa = "anticondensa" in s.lower()

    def f_temp(m):
        a, b, c = m.group(1), m.group(2), m.group(3)
        if not c and not anticondensa:
            return m.group(0)
        if b:
            t = "%s÷%s °C" % (a, b)
            if campo_t:
                st.metti("campo_regolazione", t)
            return st.segna(t)
        t = "%s °C" % a
        prima = m.string[:m.start()].lower()
        if taratura_t or re.search(r"taratura\s*$", prima):
            st.metti("taratura", t, float(a), "°C")
        return st.segna(t)
    s = re.sub(r"(?<![\w,])(\d+)°?(?:\s*[÷-]\s*(\d+))?\s*°(c\b)?(?!\s*sh\b)", f_temp, s, flags=re.I)

    # --- portata ----------------------------------------------------------------------------------------------------------------
    def f_port(m):
        a, b, u = m.group(1), m.group(2), m.group(3).lower()
        if re.search(r"\bkv\s*$", m.string[:m.start()], re.I):          # "Kv 8,6 m3/h": coefficiente, non portata
            return st.segna("%s m³/h" % it(numero(a)) if u in ("m3/h", "m³/h") else m.group(0))
        if u in ("m3/h", "m³/h"):
            unita, fatt = "m³/h", 1.0
        elif u in ("lt/min", "l/min"):
            unita, fatt = "l/min", 0.06
        else:
            unita, fatt = "l/h", 0.001
        if b:
            t = "%s÷%s %s" % (it(numero(a)), it(numero(b)), unita)
            st.metti("portata", t)
        else:
            t = "%s %s" % (it(numero(a)), unita)
            st.metti("portata", t, round(numero(a) * fatt, 4), "m³/h")
        return st.segna(t)
    s = re.sub(r"(?<![\w,])(\d+(?:,\d+)?)(?:\s*[÷-]\s*(\d+(?:,\d+)?))?\s*(m3/h|m³/h|lt/min|l/min|lt/h|l/h)", f_port, s,
               flags=re.I)

    # --- tensione, potenza --------------------------------------------------------------------------------------------------------
    s = re.sub(r"(?<![\w.,/-])(\d+)\s*[-÷]\s*(\d+)\s*v\b", lambda m: st.segna("%s-%s V" % m.groups()), s, flags=re.I)  # segnale 0-10 V
    tensioni = re.findall(r"(?<![\w.,/÷-])(\d+)\s*v\b(?![/-]\d)", s, re.I)
    if tensioni and len(set(tensioni)) == 1:
        st.metti("tensione", tensioni[0] + " V", float(tensioni[0]), "V")
    s = re.sub(r"(?<![\w.,/÷-])(\d+)\s*v\b(?![/-]\d)", lambda m: st.segna(m.group(1) + " V"), s, flags=re.I)

    def f_pot(m):
        u = {"kw": "kW", "w": "W", "va": "VA"}[m.group(2).lower()]
        t = "%s %s" % (it(numero(m.group(1))), u)
        st.metti("potenza", t, numero(m.group(1)), u)
        return st.segna(t)
    s = re.sub(r"(?<![\w,])(\d+(?:,\d+)?)\s*(kw|va)\b\.?", f_pot, s, flags=re.I)

    def f_hz(m):
        st.metti("frequenza", m.group(1) + " Hz", float(m.group(1)), "Hz")
        return st.segna(m.group(1) + " Hz")
    s = re.sub(r"(?<![\w,])(\d+)\s*hz\b", f_hz, s, flags=re.I)

    # --- vie, derivazioni, interasse -----------------------------------------------------------------------------------------------
    def f_vie(m):
        t = "%s vie" % m.group(1)
        st.metti("vie", m.group(1), float(m.group(1)) if m.group(1).isdigit() else None)
        return st.segna(t)
    s = re.sub(r"(?<![\d-])\b(\d(?:[/-]\d)?)\s*vie\b", f_vie, s, flags=re.I)

    def f_der(m):
        a, b, parola = m.group(1), m.group(2), m.group(3).lower()
        t = "%s%s %s" % (a, "+" + b if b else "", parola)
        if not re.search(r"\bper\b", m.string[:m.start()], re.I):
            st.metti("n_derivazioni", a + ("+" + b if b else ""), None if b else float(a))
        return st.segna(t)
    s = re.sub(r"\b(\d+)(?:\s*\+\s*(\d+))?\s*(derivazioni|attacchi|circuiti|uscite)\b", f_der, s, flags=re.I)

    def f_int(m):
        v = numero(m.group(1))
        st.metti("interasse", it(v) + " mm", v, "mm")
        return st.segna("interasse %s mm" % it(v))
    s = re.sub(r"(?<![\w.])(?:interasse|int\.|i\.)\s*(\d+)(?:\s*mm)?\b", f_int, s, flags=re.I)

    # --- lunghezze, cavo, spessore, volume, dimensioni ---------------------------------------------------------------------------
    def f_cavo(m):
        v = numero(m.group(1))
        t = "%s m" % it(v)
        st.metti("lunghezza_cavo", t, v * 1000, "mm")
        return "cavo " + st.segna(t)
    s = re.sub(r"\bcavo\s+(?:l\.\s*)?(\d+(?:,\d+)?)\s*m\b", f_cavo, s, flags=re.I)

    def f_lung(m):
        v = numero(m.group(1))
        u = m.group(2).lower()
        mm_v = v * 1000 if u == "m" else v
        t = "%s %s" % (it(v), u)
        st.metti("lunghezza", t, mm_v, "mm")
        return "lunghezza " + st.segna(t)
    s = re.sub(r"(?<![\w.])l\.\s*(\d+(?:,\d+)?)\s*(mm|m)\b", f_lung, s, flags=re.I)

    def f_sp(m):
        v = numero(m.group(1))
        st.metti("spessore", it(v) + " mm", v, "mm")
        return "spessore " + st.segna(it(v) + " mm")
    s = re.sub(r"\bsp\.\s*(\d+(?:,\d+)?)(?:\s*mm)?\b", f_sp, s, flags=re.I)

    def f_vol(m):
        v = numero(m.group(1))
        st.metti("volume_acqua", it(v) + " l", v, "l")
        return st.segna(it(v) + " l")
    s = re.sub(r"(?<![\w,])(\d+(?:,\d+)?)\s*lt?\b(?![/.])", f_vol, s, flags=re.I)

    def f_dim(m):
        v = [numero(g) for g in m.groups()[:3] if g]
        t = " x ".join(it(x) for x in v) + " mm"
        st.metti("dimensioni", t)
        return st.segna("x".join(it(x) for x in v) + " mm")
    s = re.sub(r"(?<![\w.,÷])(%s)\s*x\s*(%s)(?:\s*x\s*(%s))?\s*mm\b" % (N, N, N), f_dim, s, flags=re.I)

    def f_mm(m):                                                     # misura singola "900MM", "piastra 88mm", "5m": resta nel nome
        return st.segna(it(numero(m.group(1))) + " " + m.group(2).lower())
    s = re.sub(r"(?<![\w.,÷/])(\d+(?:,\d+)?)\s*(mm|m)\b", f_mm, s, flags=re.I)

    # --- materiale (non quello della maglia dei filtri, non quello del tubo "per rame") ---------------------------------------------
    basso = s.lower()
    materiali = []
    for rx, testo in MATERIALI:
        for mm_ in re.finditer(r"(?<![\w-])(?:%s)(?![\w-])" % rx, basso):
            prima = basso[:mm_.start()]
            if re.search(r"\bmaglia\s*$|\bper\s+(?:\S+\s+){0,2}$", prima):
                continue
            if testo == "acciaio" and re.match(r"acciaio\s+inox", basso[mm_.start():]):
                continue
            if testo == "EPDM" and not re.match(r"(?:ricambio\s+)?(?:guarnizione|o-ring|anello)", basso):
                continue
            if testo not in materiali and not any(testo in x for x in materiali):
                materiali.append(testo)
    if materiali:
        st.metti("materiale", ", ".join(materiali))

    # --- finitura, colore, coibentazione ---------------------------------------------------------------------------------------------
    mf = re.search(r"\b(cromo\s+(?:lucido|satinato)|cromat[oai]|cromo|satinato|verniciat[oa]|nichelat[oa])\b", s, re.I)
    if mf:
        st.metti("finitura", mf.group(1).lower())
    mc = re.search(r"(?<![\w-])(%s)(?![\w-])(\s+ral\s*\d{4})?" % "|".join(COLORI), s, re.I)
    if mc and not re.search(r"\bacqua\s*$", s[:mc.start()], re.I):
        st.metti("colore", COLORI[mc.group(1).lower()] + (" RAL " + re.sub(r"\D", "", mc.group(2)) if mc.group(2) else ""))
    if (re.search(r"\b(?:coibentat[oaie]|con coibentazione)\b", s, re.I)
            and not re.match(r"(?:kit\s+)?(?:coibentazione|gusc[io]|ricambio\s+gusc)", s, re.I)):
        st.metti("coibentazione", "coibentato")

    # --- guarnizione / tenuta ---------------------------------------------------------------------------------------------------------
    mt = re.search(r"\btenuta\s+(o-ring|ptfe|gomma)\b", s, re.I)
    if mt:
        st.metti("guarnizione", {"o-ring": "O-ring", "ptfe": "PTFE", "gomma": "gomma"}[mt.group(1).lower()])
    elif re.search(r"\bcon\s+o-ring\b", s, re.I) and not re.match(r"(?:ricambio\s+)?(?:o-ring|anello)", s, re.I):
        st.metti("guarnizione", "O-ring")

    # --- comando ------------------------------------------------------------------------------------------------------------------------
    comandi = []
    if re.match(r"(?:valvola|rubinetto|coppia valvole)", s, re.I):
        mco = re.search(r"\b(?:con\s+)?(leva|farfalla|volantino|maniglia)\b(?!\s+(?:di|per)\b)", s, re.I)
        if mco and not re.search(r"\ba\s+farfalla\b", s, re.I):
            comandi.append(mco.group(1).lower())
    mn = re.search(r"\bnormalmente\s+(chiusa|aperta|chiuso|aperto)\b", s, re.I)
    if mn:
        comandi.append("normalmente " + mn.group(1).lower())
    if re.search(r"\briarmo\s+manuale\b", s, re.I):
        comandi.append("riarmo manuale")
    if comandi:
        st.metti("comando", ", ".join(comandi))

    # --- normativa, fluidi, raccordo, installazione, scarico ------------------------------------------------------------------------------
    norme = []
    for rx, t in ((r"ispesl", "ISPESL"), (r"inail", "INAIL"), (r"icim", "ICIM"), (r"ce", "CE")):
        if re.search(r"(?<![\w-])%s(?![\w-])" % rx, s, re.I):
            norme.append(t)
    if norme:
        st.metti("normativa", ", ".join(norme))
    fl = re.search(r"\b(?:per\s+)?(gas|gpl|metano)\b", s, re.I)
    if fl:
        st.metti("fluidi", {"gas": "gas", "gpl": "GPL", "metano": "metano"}[fl.group(1).lower()])
    else:
        fa = re.search(r"\bacqua\s+(calda|fredda)\s+sanitaria\b", s, re.I)
        if fa:
            st.metti("fluidi", "acqua %s sanitaria" % fa.group(1).lower())
    mr = re.search(r"\b(bicono|a pressare|a saldare|innesto rapido|flangiat[oa]|con flange|flange)\b", s, re.I)
    if mr:
        st.metti("tipo_raccordo", {"flangiata": "flangiato", "con flange": "flangiato", "flange": "flangiato"}.get(
            mr.group(1).lower(), mr.group(1).lower()))
    if re.search(r"\bincasso\b", s, re.I):
        st.metti("installazione", "incasso")
    msc = re.search(r"\b(con scarico|senza scarico|scarico filettato)\b", s, re.I)
    if msc and not re.match(r"valvola (?:di )?scarico", s, re.I):
        st.metti("scarico", msc.group(1).lower())

    # --- compatibilita': tubo ("per rame") oppure serie/articoli ("per 551", "per serie 7200", "per art. 659044") ----------------------
    mtubo = re.search(r"\bper\s+(%s)\b" % TUBI, s, re.I)
    if mtubo:
        st.metti("compatibilita", mtubo.group(1).lower())
    else:
        mcomp = re.search(r"\bper\s+((?:[a-zà-ù.']+\s+){0,2}"
                          r"\d{3,}[\w./]*(?:\s*[-/]\s*\d[\w./]*)*)", s, re.I)
        if mcomp:
            c = _render(mcomp.group(1), st.pezzi)
            st.metti("compatibilita", c[:1].lower() + c[1:])

    # --- maschio / femmina --------------------------------------------------------------------------------------------------------------
    gen_filetto = st.at.pop("_gen_filetto", None)
    parole = re.findall(r"\b(maschio|femmina)(?:\s*/?\s*(maschio|femmina))?\b", re.sub(r"\bper\b.*$", "", s, flags=re.I), re.I)
    if len(parole) == 1:
        a, b = parole[0]
        parola = a.lower() + ("/" + b.lower() if b else "")
        if gen_filetto is None or gen_filetto["valore"] == parola or gen_filetto["valore"].startswith(parola):
            st.metti("maschio_femmina", gen_filetto["valore"] if gen_filetto else parola)
    elif not parole and gen_filetto is not None:
        st.at["maschio_femmina"] = gen_filetto

    # --- serie ------------------------------------------------------------------------------------------------------------------------------
    if serie:
        st.metti("tipo_base", "serie " + serie)
        s = s.rstrip(" ,") + ", serie " + serie
    s = re.sub(r"\s*\+\s*", " + ", s)
    nome = _render(s, st.pezzi)
    nome = re.sub(r"\bserie (\S+)$", lambda m: "serie " + m.group(1).upper(), nome)
    return caleffi_fonti.integra(cod, descr, nome, {k: v for k, v in st.at.items() if not k.startswith("_")})
