#!/usr/bin/env bash
# Prepara il progetto su Mac/Linux: controlla Python, installa le librerie, crea .env e il database.
# Richiede Python 3.15 e PostgreSQL gia' installati e accesi.   Uso:  bash installa.sh
cd "$(dirname "$0")" || exit 1

PY=""
for c in python3.15 python3; do
  if command -v "$c" >/dev/null 2>&1; then
    PY="$c"
    break
  fi
done
if [ -z "$PY" ]; then
  echo "Python non trovato. Scaricalo da https://www.python.org/downloads/ oppure: brew install python@3.15"
  exit 1
fi
VER=$("$PY" -c 'import sys; print("%d.%d" % sys.version_info[:2])')
if [ "$VER" != "3.15" ]; then
  echo "ATTENZIONE: trovato Python $VER, il progetto e' pensato per la 3.15 (installala con: brew install python@3.15)."
  echo "Continuo con la versione trovata; se qualcosa non funziona, installa la 3.15."
fi

echo "Installo le librerie..."
"$PY" -m pip install -r requirements.txt || { echo "Installazione delle librerie non riuscita: leggi l'errore qui sopra."; exit 1; }

"$PY" installa.py || { echo "Preparazione non completata: leggi il messaggio qui sopra."; exit 1; }
