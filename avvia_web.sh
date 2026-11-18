#!/usr/bin/env bash
# Avvia la pagina di consultazione su Linux/Mac (anche su una VPS).
# Le impostazioni (database, WEB_HOST, WEB_PORTA, WEB_UTENTE, WEB_PASSWORD) si leggono dal file .env: vedi .env.example.
# Uso:  bash avvia_web.sh            (in primo piano; per farlo partire da solo con il server: deploy/db-serio-web.service)
cd "$(dirname "$0")" || exit 1

PY=""
for c in .venv/bin/python python3.15 python3; do                 # prima l'ambiente virtuale del progetto, se c'e'
  if command -v "$c" >/dev/null 2>&1; then
    PY="$c"
    break
  fi
done
if [ -z "$PY" ]; then
  echo "Python non trovato: installalo (es. sudo apt install python3 python3-pip) e poi: python3 -m pip install -r requirements.txt"
  exit 1
fi
if ! "$PY" -c "import psycopg2" >/dev/null 2>&1; then
  echo "Manca la libreria psycopg2: $PY -m pip install -r requirements.txt"
  exit 1
fi

exec "$PY" web/server.py "$@"
