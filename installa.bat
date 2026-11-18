@echo off
rem Prepara il progetto su un PC Windows: controlla Python, installa le librerie, crea .env e il database.
rem Richiede Python 3.15 (con il launcher "py") e PostgreSQL gia' installati e accesi.
cd /d "%~dp0"

set PY=py -3.15
%PY% --version >nul 2>nul
if errorlevel 1 (
  echo.
  echo Python 3.15 non trovato. Scaricalo da https://www.python.org/downloads/windows/ ^(installer a 64 bit, con il launcher "py"^).
  echo Versioni di Python trovate sul PC:
  py -0p
  pause
  exit /b 1
)

echo Installo le librerie...
%PY% -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo Installazione delle librerie non riuscita: leggi l'errore qui sopra.
  pause
  exit /b 1
)

%PY% installa.py
if errorlevel 1 (
  echo.
  echo Preparazione non completata: leggi il messaggio qui sopra.
  pause
  exit /b 1
)
pause
