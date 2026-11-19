# -*- coding: utf-8 -*-
"""Come la pagina legge la frase scritta da chi cerca (usato da server.py).

Che cosa fa `espandi(q)`:
  1. riscrive i modi di dire con le misure: «mezzo pollice» -> 1/2, «tre quarti» -> 3/4, «½» -> 1/2, «tre vie» -> 3 vie;
  2. unisce le varianti di scrittura: dritto = diritto;
  3. trova nella frase i NOMI ALTERNATIVI delle famiglie (alias_famiglie.json: «clapet» -> Valvola di ritegno): quel pezzo di
     frase cerca le famiglie indicate OPPURE il testo scritto (cosi' le parole gia' presenti nel catalogo continuano a valere);
  4. per le altre parole usa la radice (valvole -> valvol): singolare e plurale trovano lo stesso articolo.
Le parole restano in AND tra loro, come prima. RICERCA_SEMPLICE=1 (variabile d'ambiente) torna alla ricerca di prima
(sottostringa, nessun alias): serve anche per misurare «prima» e «dopo» con prova_ricerca.py.
Gli alias sono un aiuto per TROVARE: non sono attributi, non vanno mai mostrati come dati del prodotto (regola 1 del progetto).
"""
import json
import os
import re
import unicodedata

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE_ALIAS = os.path.join(BASE, "alias_famiglie.json")
ATTIVA = os.environ.get("RICERCA_SEMPLICE", "").strip().lower() not in ("1", "si", "true", "vero")

# parole che non distinguono (si ignorano solo per riconoscere un alias)
STOP = {"a", "ad", "al", "alla", "alle", "con", "da", "dei", "del", "della", "delle", "di", "e", "il", "in", "la", "le", "lo",
        "per", "su", "un", "una", "uno"}
_FRAZIONI = {"½": "1/2", "¼": "1/4", "¾": "3/4", "⅓": "1/3", "⅔": "2/3"}
# modi di dire una misura (filettatura in pollici) come nei cataloghi: Ø1.1/2" = un pollice e mezzo
_MISURE = [
    (re.compile(r"\b(?:un )?pollice e (?:un )?mezzo\b"), "1.1/2"),
    (re.compile(r"\b(?:un )?pollice e (?:un )?quarto\b"), "1.1/4"),
    (re.compile(r"\bmezzo pollice\b"), "1/2"),
    (re.compile(r"\btre quarti(?: di pollice)?\b"), "3/4"),
    (re.compile(r"\bun quarto di pollice\b"), "1/4"),
]
_VIE = re.compile(r"\b(due|tre|quattro) vie\b")
_CIFRA = {"due": "2", "tre": "3", "quattro": "4"}


def senza_accenti(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c))


def radice(parola):
    """Toglie l'ultima vocale a una parola fatta di sole lettere (valvole -> valvol, sfera -> sfer): cosi' singolare e
    plurale si trovano a vicenda. Le parole corte (tee, tubo, gas) e quelle con cifre restano come sono."""
    if parola.isalpha():
        if len(parola) >= 5 and parola[-1] in "aeiou":
            return parola[:-1]
        if len(parola) == 4 and parola[-1] == "i":
            return parola[:-1]
    return parola


def riscrivi(q):
    """La frase in minuscolo con i modi di dire sulle misure e le varianti di scrittura riportati alla forma del catalogo."""
    q = (q or "").lower()
    for k, v in _FRAZIONI.items():
        q = q.replace(k, " " + v + " ")
    q = re.sub(r"\bdritt", "diritt", q)
    for rx, v in _MISURE:
        q = rx.sub(v, q)
    return _VIE.sub(lambda m: _CIFRA[m.group(1)] + " vie", q)


_ALIAS = {"mt": None, "voci": [], "per_famiglia": {}}


def _chiave(testo):
    """Un alias come sequenza di radici, senza le parole che non distinguono: «valvola per termosifone» = («valvol», «termosifon»)."""
    return tuple(radice(w) for w in senza_accenti(testo.lower()).split() if w not in STOP)


def alias():
    """{'voci': [(chiave, [nomi famiglia])] dal piu' lungo, 'per_famiglia': {nome: [alias]}} da alias_famiglie.json
    (si rilegge quando il file cambia). Si usano solo gli «alias», non i «da_confermare»."""
    try:
        mt = os.path.getmtime(FILE_ALIAS)
    except OSError:
        return {"voci": [], "per_famiglia": {}}
    if _ALIAS["mt"] != mt:
        try:
            with open(FILE_ALIAS, encoding="utf-8") as f:
                fam = json.load(f).get("famiglie", {})
        except (OSError, ValueError):
            fam = {}
        voci, per = {}, {}
        for nome, d in fam.items():
            lista = [a.strip() for a in d.get("alias", []) if a.strip()]
            if lista:
                per[nome] = lista
            for a in lista:
                k = _chiave(a)
                if k:
                    voci.setdefault(k, set()).add(nome)
        _ALIAS.update(mt=mt, per_famiglia=per, voci=sorted(((k, sorted(v)) for k, v in voci.items()), key=lambda x: -len(x[0])))
    return _ALIAS


def alias_per_famiglia():
    return alias()["per_famiglia"]


def espandi(q):
    """-> (parole, gruppi). parole = le parole della frase che restano da cercare nel testo (gia' riscritte, minuscole);
    gruppi = [(parole del gruppo, [nomi di famiglia])] per ogni nome alternativo riconosciuto (il gruppo vale: famiglia
    indicata OPPURE testo scritto)."""
    toks = riscrivi(q).split()[:8]
    sem = [(i, radice(senza_accenti(t))) for i, t in enumerate(toks) if senza_accenti(t) not in STOP]
    usati, gruppi = set(), []
    for chiave, nomi in alias()["voci"]:
        n = len(chiave)
        for k in range(len(sem) - n + 1):
            if all(sem[k + j][1] == chiave[j] for j in range(n)):
                i0, i1 = sem[k][0], sem[k + n - 1][0]
                if any(i in usati for i in range(i0, i1 + 1)):
                    continue
                usati.update(range(i0, i1 + 1))
                gruppi.append((toks[i0:i1 + 1], nomi))
    return [t for i, t in enumerate(toks) if i not in usati], gruppi
