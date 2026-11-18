# -*- coding: utf-8 -*-
"""Legge il file `.env` nella cartella del progetto (se c'e') e ne mette le variabili nell'ambiente.
Cosi' PGDATABASE, PGHOST, PGUSER, PGPASSWORD, PGPORT si cambiano in un posto solo. Le variabili gia' impostate
nel sistema o nel terminale hanno la precedenza sul file."""
import os


def _carica_env():
    percorso = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if not os.path.isfile(percorso):
        return
    with open(percorso, encoding="utf-8-sig") as f:
        for riga in f:
            riga = riga.strip()
            if not riga or riga.startswith("#") or "=" not in riga:
                continue
            k, v = riga.split("=", 1)
            k, v = k.strip(), v.strip().strip("\"'")
            if k and k not in os.environ:
                os.environ[k] = v


_carica_env()
