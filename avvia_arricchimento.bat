@echo off
rem Ricalcola nomeV1 e attributi di tutti gli articoli di db_serio_finale (descrizione + codice + schede del produttore + web).
rem Da usare dopo aver modificato arricchimento\*.py. Opzione: py -3.15 arricchisci.py --prova (solo statistiche, non scrive).
cd /d "%~dp0"
py -3.15 arricchisci.py
pause
