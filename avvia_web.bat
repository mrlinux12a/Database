@echo off
rem Avvia la pagina con descrizione e codice fornitore degli articoli (http://localhost:8001)
rem Richiede PostgreSQL attivo e Python 3.13 con psycopg2 (pip install psycopg2-binary)
cd /d "%~dp0"
py -3.13 web\server.py --apri
if errorlevel 1 (
  echo.
  echo Avvio non riuscito. Controlla che PostgreSQL sia acceso e che l'import sia stato fatto.
  pause
)
