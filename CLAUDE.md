# CLAUDE.md — come lavorare un catalogo in questo progetto

Questo progetto trasforma i cataloghi dei fornitori (un CSV ciascuno) in dati ordinati in PostgreSQL:
per ogni articolo un **nomeV1**, un **nomeV2** e un insieme di **attributi**. Lo scopo finale è cercare gli articoli
**per famiglia** (prima si sceglie la famiglia, poi si filtra per attributi) fino a trovare l'articolo giusto.
Tu lavori su **un catalogo** e consegni un file; non tocchi il database di nessun altro.
Leggi anche `README.md` (struttura, tabelle, esempio completo con Air Control).

## Che cosa si produce per ogni articolo

| Campo | Cosa è |
|---|---|
| **nomeV1** | Il nome più semplice e completo: descrizione del catalogo ripulita (abbreviazioni sciolte, refusi corretti, maiuscole giuste, modelli in maiuscolo) che **contiene anche le specifiche**. Es. `Plenum bocchetta PSF 1000x30 mm, 1 attacco Ø150 posteriore, per cartongesso`. |
| **attributi** | Una riga in `materiale_attributo` per ogni valore **trovato** (elenco in `arricchimento/attributi.py`, ~50 attributi: pressione, temperatura, tensione, materiale, dimensioni, Ø, DN, PN, colore, normativa, grado IP, compatibilità, EAN, …). |
| **nomeV2** | nomeV1 **senza** le informazioni che l'articolo ha già come attributo (lo calcola `arricchimento/v2.py`, non a mano). Articoli con nomeV2 uguale = stessa famiglia candidata. |
| **famiglia** | Tipo di prodotto (`famiglia`, lista **controllata e condivisa tra cataloghi**: «Griglia di ripresa», «Plenum», …). Si propone da nomeV2 con `proponi_famiglie.py`; la decide una persona. |
| **attributo candidato** | Testo che resta nel nomeV2 e si ripete su molti articoli = possibile nuovo attributo (poi nomeV3). Lo propone `proponi_attributi.py`; lo approva una persona. |

## Regole che non si discutono

1. **Mai inventare.** Un valore entra solo se è scritto nella descrizione, nel codice o in una fonte che hai davvero letto.
   Se non lo trovi: **nessuna riga** (niente NULL, niente «n.d.», niente valori «probabili»). Se due fonti si contraddicono, non inserire il valore e segnalalo.
2. **Ogni valore ha la sua origine** (`comuni.ORIGINI`): `descrizione` (testo del catalogo), `codice` (lettere/cifre del codice),
   `sito` (scheda del produttore, vale per la famiglia), `web` (scheda di un costruttore terzo). Per `sito` e `web` è obbligatoria la `fonte` = indirizzo della pagina in cui hai letto il valore.
3. **Ricerca per famiglia, non per codice.** Cercare online ogni singolo codice rende poco e costa molto. Meglio: leggere bene descrizione e schema dei codici, trovare le pagine/schede di famiglia del produttore (HTML), e collegare i codici alle famiglie.
   Un valore di scheda vale per il codice solo se la scheda lo dice per quella famiglia (es. «senza A finale = bianco standard», non «tutte le griglie sono bianche»).
4. **Non lasciare che un attributo venga inferito dal nome del prodotto** (es. non dedurre il materiale da «tubo flessibile» se non c'è scritto).
5. **Ambiguo = lascialo com'è nel nome** e non farne un attributo (es. «M-m» che può voler dire due cose, numeri finali senza unità).
6. **Nessun download di file senza il permesso dell'utente** (PDF, listini, cataloghi): chiedi prima, dicendo nome, fonte e dimensione. Pagine HTML e ricerche sì. Scraping educato: pausa tra le richieste (≥0,5 s), User-Agent generico, rispetta robots.txt.
7. **Niente dati personali o commerciali nelle richieste esterne** e niente prezzi/sconti nei file che consegni.
8. **Non modificare `arricchimento/attributi.py`** (la lista condivisa degli attributi) né i moduli di altri cataloghi. Un attributo che manca lo proponi (vedi sotto), non lo aggiungi.

## Stato del progetto (aggiornare a ogni catalogo finito)

* Fatto: **Air Control SRL** (modulo di riferimento `cataloghi/air_control_srl.py` + `parse.py`, `sito.py`, `web.py`).
* Fatto: **Aquatechnik** (2026-11-18, 1.408 articoli, 1.407 con almeno un attributo; modulo `cataloghi/aquatechnik.py` + dati di famiglia dal sito in `cataloghi/aquatechnik_fonti.py`). Per i cataloghi i cui nomi non hanno virgole, `proponi_attributi.py --parole` propone parole e coppie di parole (solo quelle che distinguono articoli con lo stesso nome base; rilanciandolo toglie i vecchi candidati ancora «proposto» non più validi). Sulla pagina web il filtro per valore (faccette) permette di restringere per attributo dopo la famiglia. Il modulo riceve anche Linea/Serie del CSV (`VUOLE_RIGA = True`): la gamma (tipo_base) viene dalla Linea.
* Fatto: **Caleffi** (2026-11-18, 3.860 articoli, 3.768 con almeno un attributo, 11.862 valori, 286 famiglie provvisorie; modulo `cataloghi/caleffi.py` + dati dal sito in `cataloghi/caleffi_fonti.py`). Il numero iniziale della descrizione è la serie Caleffi → `tipo_base` «serie 127» (in fondo al nomeV1, tolta dal nomeV2); i nomi di gamma (Solar, Autoflow, Dynamical…) vanno dopo il tipo di prodotto. Le pagine it-it di caleffi.com davano 502: usate le pagine en-int, un fatto vale solo per i codici elencati nella pagina. `v2.py` esteso (DN, bar/mbar, °C e l/min a intervallo, VA, Hz, vie, interasse, litri, coibentato, derivazioni): ha cambiato 15 nomeV2 di Air Control (miglioramenti, applicati il 2026-11-18 con famiglie rifatte: stessi totali, 162 famiglie).
* Gli altri cataloghi si lavorano uno per volta con la procedura sotto; la lista delle famiglie è condivisa tra cataloghi.
* Chi consegna un catalogo aggiorna questa lista (nome, data, n. articoli, copertura) nel messaggio di consegna.

## Come si parte

L'utente ti dà **solo il nome di un file** (es. «Caleffi» o «Caleffi.csv»): è un catalogo **già filtrato**, nella cartella indicata da
`CARTELLA_CATALOGHI` nel file `.env`. Non servono Excel né brand. Non chiedere altro: parti dal punto 1 con
`py -3.15 import_catalogo.py --csv "Nome" --tutto` (su Mac/Linux `python3.15`, e percorsi con `/`) e prosegui fino alla consegna (punto 8).
Chiedi all'utente solo quando una regola qui sotto lo prevede (permesso per scaricare file, valori contraddittori, scelte di famiglia).

## Procedura per un catalogo nuovo

Prerequisiti: PostgreSQL acceso, Python 3.15 con `psycopg2-binary openpyxl requests`.
Il database di lavoro è `db_serio_finale` sul PC locale (o un altro nome con la variabile `PGDATABASE`; vedi README).
Lancia gli script **senza** `-I` (non troverebbe il pacchetto `arricchimento`) e con `PYTHONIOENCODING=utf-8` se stampi testo con Ø, °, ³.

1. **Importa il catalogo** (file già filtrato: `--tutto`; nella versione con Excel, che dice quali linee tenere, si usa `--excel` e `--brand`):
   `py -3.15 import_catalogo.py --csv "…\Nome.csv" --excel "…\Flash_Delivery_Linee_per_Brand.xlsx" --brand "NOME NELL'EXCEL"`
   (`--prova` per vedere cosa entrerebbe). Il nome del catalogo = nome del file CSV senza `.csv`.
2. **Capisci il catalogo**: guarda 200+ descrizioni a campione, le colonne del CSV, lo schema dei codici (prefissi, misure nel codice, suffissi). Elenca abbreviazioni, refusi, unità, tipi di prodotto.
3. **Crea il modulo del catalogo**: copia `arricchimento/cataloghi/_modello.py` in `arricchimento/cataloghi/<nome>.py`
   (nome = catalogo in minuscolo, non alfanumerici → `_`: «Acme SRL» → `acme_srl.py`). Parti da `cataloghi/generico.py` (misure, Ø, DN, PN, V, W, bar, kg, °C, portate) e aggiungi le regole del catalogo.
   Riferimento completo: `cataloghi/air_control_srl.py` + `parse.py` + `sito.py` + `web.py`.
4. **Prova senza scrivere**: `py -3.15 arricchisci.py --catalogo "Nome" --prova` → statistiche per attributo e origine. Poi scrivi: stesso comando senza `--prova`.
5. **Controlla a campione** (almeno 50 articoli di famiglie diverse, più tutti i casi strani): nome sensato? numeri giusti? nessun attributo inventato? Nel database: `select nomev1, nomev2 from materiale where catalogo = '…'` e `materiale_attributo`. Ripeti 3–4 si finché i residui sono pochi.
6. **Ricerca online per famiglia** per i dati che la descrizione non ha (materiale, normative, IP, temperature, pesi, compatibilità…): pagine HTML del produttore e schede di terzi, con la regola 2 (origine + fonte). Metti i fatti nel modulo (come `sito.py` / `web.py`): un fatto per famiglia o per codice, con l'URL.
7. **Proposte**: `py -3.15 proponi_famiglie.py --catalogo "Nome"` (elenca i gruppi; `--assegna` crea le famiglie provvisorie) e `py -3.15 proponi_attributi.py --catalogo "Nome"` (testi ripetuti nel nomeV2). Poi `py -3.15 unisci_famiglie.py --prova` e senza `--prova`: mette nella stessa famiglia i tipi di prodotto che i cataloghi chiamano in modo diverso (Tee, Curva / Gomito, Riduzione, Tappo, Manicotto, Giunto, Tubo, Collettore; regole in `arricchimento/famiglie_comuni.py`, ripetibile). Se nel tuo catalogo c'è un tipo di prodotto che c'è anche in un altro, **aggiungi una voce** a quella lista solo se sono davvero lo stesso prodotto (i falsi amici come «Collare» o «Valvola» sono elencati nel docstring: non unirli). Le famiglie e i candidati finali li approva una persona.
8. **Consegna**: `py -3.15 esporta.py --catalogo "Nome"` → `esportazioni/<nome>.json.gz` (nomi, famiglia, attributi con origine e fonte, candidati; **niente prezzi**) + il file `arricchimento/cataloghi/<nome>.py` e gli eventuali dati di fonte. Scrivi nel messaggio di consegna: statistiche di copertura, scelte fatte, casi ambigui lasciati, valori contraddittori non inseriti.

Chi riceve controlla con `py -3.15 importa_risultati.py esportazioni/<nome>.json.gz --prova` e poi senza `--prova`.

## Come si scrive un buon modulo

* Funzione `analizza(cod_fornitore, descrizione) -> (nomev1, {chiave: valore})` con valore = `comuni.F(testo, origine, num, unita, fonte)`.
  `valore_num`/`unita` servono per filtrare: misure sempre in **mm**, tensioni in **V**, pressioni in **bar**, portate in **m³/h**, potenze in **W/kW**, peso in **kg**.
* Il testo dei valori è italiano, con la virgola decimale (`2,5 kg`) e le unità col simbolo (`150 mm`, `24 V`, `Ø150`).
* Lavora per **regole su testo minuscolo**, con una lista di abbreviazioni/refusi del catalogo; i modelli (lettere+cifre) tornano in maiuscolo.
* Ogni regola nuova: provala su tutto il catalogo (`--prova`), guarda i casi che cambia e i «residui» (parole del nome che non hai capito).
* Il **nomeV2** non lo scrivi tu: si calcola da nomeV1 + attributi (`v2.pulisci`). Se un'informazione resta nel nomeV2 e non dovrebbe, vuol dire che manca l'attributo, o che la regola di `v2.py` non la riconosce (estendila lì, in modo generale).
* Il nomeV1 deve **contenere** le specifiche: sono gli attributi che si tolgono dopo, non prima.

## Trabocchetti già incontrati (Windows)

* In Bash, passare codice Python con regex dentro un heredoc rovina gli escape (`\b`, `\s`): scrivi i file con lo strumento di scrittura/modifica, non con `cat <<EOF` o `python -c`.
* Il terminale può mostrare `�` per Ø, –, °, ³: è solo la visualizzazione; i dati sono UTF-8 corretti (verifica con `PYTHONIOENCODING=utf-8`).
* `import_catalogo.py` cancella e reinserisce le righe del catalogo: dopo ogni import rilancia `arricchisci.py` (nomi, attributi e famiglie dell'import precedente vanno persi; i risultati esportati si rimettono con `importa_risultati.py`).
* Le descrizioni dei cataloghi sono spesso **troncate** (`All` = Alluminio, `Bco` = Bianco): sciogli solo dove inequivocabile.
* Lo stesso numero finale può avere significati diversi (`75` Ø, `75` altezza): decidi con i codici fratelli e, se resta dubbio, lascialo nel nome.
* `sed` mangia le barre rovesciate dei percorsi Windows (`C:\Users\…`): per scrivere o correggere il `.env` usa lo strumento di scrittura. Un `CARTELLA_CATALOGHI` rovinato faceva importare il CSV non filtrato; ora con `--tutto` `import_catalogo.py` cerca **solo** lì e si ferma con un errore se la cartella non esiste. Dopo l'import controlla che il numero di articoli sia quello del CSV filtrato.
* I **moduli e `v2.py` sono condivisi**: una regola nuova in `v2.py` può cambiare i cataloghi già consegnati. Prima e dopo ogni modifica ai file condivisi lancia `py -3.15 controlla_regressione.py` (non scrive nulla; con `--mostra N` stampa le differenze, uscita 1 se ce ne sono). Differenze volute (es. i 29 nomeV2 di Air Control che migliorarono con le regole nuove, applicati il 2026-11-18) si controllano e si applicano rilanciando `arricchisci.py` di proposito; poi si rifanno le famiglie: azzera `famiglia_id` del catalogo, `proponi_famiglie.py --assegna`, `unisci_famiglie.py`.
* Il valore di un attributo trovato **solo in una colonna del CSV** (Linea, Serie) non è nella descrizione: il modulo lo riceve se dichiara `VUOLE_RIGA = True` (`analizza(cod, descr, riga)`). Un suffisso di codice che «sembra» dare un valore (es. `U` = SDR 11) va provato su **tutti** gli articoli prima di usarlo: in Aquatechnik il suffisso→SDR regge sui raccordi ma non sui tubi Fiber-T, quindi non è una regola.
* Le pagine HTML dei produttori si leggono con un riassuntore: **rileggi due volte** i fatti che entrano nel modulo (stessa pagina, prompt diverso, citazione letterale) e annota nel docstring cosa hai letto e cosa no (tabelle grafiche, pagine senza dati). Una negazione («NON IDONEO ad acqua potabile») non va in un attributo di compatibilità: finisce nel docstring.

## File principali

`schema.sql` (tabelle) · `import_catalogo.py` · `arricchisci.py` (nomi + attributi di un catalogo) · `arricchimento/` (`attributi.py` elenco attributi, `comuni.py`, `v2.py`, `cataloghi/` un modulo per catalogo, `parse.py`/`sito.py`/`web.py`/`famiglie.py` = Air Control) ·
`proponi_famiglie.py` · `unisci_famiglie.py` · `proponi_attributi.py` (`--parole`) · `controlla_regressione.py` · `esporta.py` · `importa_risultati.py` · `web/` (pagina di consultazione, `avvia_web.bat`, porta 8001).
