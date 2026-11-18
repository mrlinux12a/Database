@echo off
rem Importa in db_serio_finale gli articoli di Air Control SRL.csv delle sole linee con "Si" nell'Excel (Tenere?)
rem e poi ricalcola nomeV1 e attributi (l'import rifa' le righe da zero, quindi nomeV1 e attributi vanno rifatti).
rem Si puo' rilanciare quando si cambia l'Excel.
rem Opzioni: py -3.15 import_catalogo.py --prova   (mostra cosa entrerebbe senza toccare il database)
cd /d "%~dp0"
py -3.15 import_catalogo.py
if errorlevel 1 goto fine
py -3.15 arricchisci.py
:fine
pause
