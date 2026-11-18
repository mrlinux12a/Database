# db_serio_finale

Database PostgreSQL `db_serio_finale` con gli articoli dei cataloghi fornitori. Per ogni **codice fornitore** contiene la
descrizione originale, un **nomeV1** (il nome più semplice e completo) e gli **attributi** trovati; una pagina li mostra
(solo gli attributi che hanno un valore).

## Uso

| Cosa | Come |
|---|---|
| Aprire la pagina | doppio clic su `avvia_web.bat` → http://localhost:8001 |
| (Ri)caricare gli articoli **e** ricalcolare nomeV1/attributi | doppio clic su `avvia_import.bat` |
| Solo ricalcolare nomeV1/attributi | doppio clic su `avvia_arricchimento.bat` |
| Vedere le statistiche senza scrivere nel DB | `py -3.13 arricchisci.py --prova` |
| Vedere cosa entrerebbe dall'import senza toccare il DB | `py -3.13 import_catalogo.py --prova` |

Requisiti: PostgreSQL attivo, Python 3.13 con `psycopg2-binary` e `openpyxl`. Connessione di default: `localhost`, utente
`postgres`, senza password, database `db_serio_finale` (variabili `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`).

La pagina permette di: cercare (nel codice, nel nome, nella descrizione e nei valori degli attributi), filtrare per attributo
(«con Colore», «senza nessun attributo»…) e per origine del dato, ordinare per codice o per nome, mostrare anche la
descrizione originale, e vedere in «Copertura degli attributi» quanti articoli hanno un valore per ciascun attributo.

## Quali articoli entrano

Gli articoli vengono da `app2/db/cataloghi/Air Control SRL.csv` (15 colonne, `;`) e da `app2/db/Flash_Delivery_Linee_per_Brand.xlsx`.
Nell'Excel, nel blocco **AIR CONTROL**, la colonna «Tenere?» dice per ogni linea (le «serie» dell'Excel = colonna `Linea` del CSV):
**Sì** = entra · **No** = fuori · **vuota** = fuori.

| Linea | Articoli | Tenere? |
|---|---|---|
| Distribuzione Aeraulica | 4.600 | Sì |
| Regolazione E Zonificazione | 373 | Sì |
| Accessori | 40 | Sì |
| Sanificazione, Vmc, Generica | 153 | No |

Risultato: **5.013 articoli** nella tabella `materiale`. L'import è rilanciabile: rifà da zero solo le righe di quel catalogo
(una transazione). **Cancella anche nomeV1 e attributi**, per questo `avvia_import.bat` lancia subito dopo `arricchisci.py`.
Per un altro fornitore: `py -3.13 import_catalogo.py --csv "…\Altro.csv" --brand "NOME NELL'EXCEL"`.

## nomeV1 e attributi

* `materiale.nomev1`: la descrizione del catalogo ripulita (abbreviazioni sciolte, refusi corretti, maiuscole, modelli in
  maiuscolo) e completata con quello che dicono codice e scheda del produttore. Es. `Plenum bocchetta PSF 1000x30 mm,
  1 attacco Ø150 posteriore, per cartongesso`.
* `attributo`: l'elenco dei 50 attributi possibili, nell'ordine della lista data (47 dalla lista, con ★ quelli nuovi, più
  3 extra dove l'informazione era importante e senza posto: *Installazione* (cartongesso/muro), *Coppia* (attuatori),
  *Feritoie* (diffusori lineari)). Il codice è in `arricchimento/attributi.py`.
* `materiale_attributo`: **una riga per ogni valore trovato** (`codice`, `chiave`, `valore`, `valore_num`, `unita`, `origine`, `fonte`).
  Se un valore non c'è, la riga non esiste: nessun NULL e nessun valore inventato.

Ogni valore dice da dove arriva (`origine`):

| origine | significato | righe | articoli |
|---|---|---|---|
| `descrizione` | scritto nel testo del catalogo (dimensioni, Ø, attacchi, colore, tensione…) | 18.759 | 4.954 |
| `sito` | scheda del produttore su aircontrolclima.it (materiale, normative, IP, finitura…) — vale per la **famiglia** di prodotto; `fonte` = pagina | 14.495 | 4.735 |
| `codice` | ricavato da lettere/cifre del codice (es. `…A` finale = alluminio anodizzato, `CB` = cartongesso) | 237 | 209 |
| `web` | scheda/pagina di un costruttore terzo (Belimo, deumidificatori UDE); `fonte` = indirizzo | 119 | 41 |

In totale **33.610 valori** su **4.983 articoli** (in media 6,7 per articolo, al massimo 11); 30 articoli non hanno nessun
attributo (kit cablaggio 2Z–6Z, elettroniche NH-ELE-DOMO e NH-UAM, filtri/kit VMC generici, ISOLINA, KIT-DLF/DLN, ME-40,
GMA 60-SMF, AC-CNV-UDE, GRIGLIA-UDE-LE-23, AIR10036/37/78-A/78-B, COPERCHIO-VMC).

### Come sono stati cercati

* **Produttore (Air Control).** 174 pagine di prodotto di aircontrolclima.it sono state lette (scraping educato, 0,6 s tra le richieste)
  e salvate in `fonti/aircontrolclima_it/pagine.json`; ogni articolo è collegato alla sua pagina (`arricchimento/famiglie.py`):
  113 pagine coprono 4.735 articoli. I fatti delle pagine sono in `arricchimento/sito.py`. La ricerca è **per famiglia**: ogni codice
  riceve ciò che la scheda dice della sua famiglia, senza farne un valore del singolo codice (es. la finitura «bianco RAL 9016»
  solo dove il sito dice che senza «A» finale la griglia è standard).
* **Descrizione e codice.** `arricchimento/parse.py` legge dimensioni, Ø, attacchi (lettere A = Ø150, B = Ø200, D = Ø75…),
  numero di attacchi, lunghezza × feritoie, colore, installazione, tensione, comando, compatibilità con marca/modello (Mitsubishi,
  Daikin, Samsung…), confezioni, ecc.
* **Componenti di terzi (senza scheda sul sito).** Per gli attuatori Belimo (LM, NM, SM, GM, CM, LF, TF, NF, SF), i posizionatori
  SGA24/SGF24, i motori BFL/BFN per serrande tagliafuoco, BKS24-1B, LMV-D3-MP e i deumidificatori UDE sono stati cercati sul web
  le schede dei costruttori: `arricchimento/web.py` (IP, classe di isolamento, peso, assorbimento, temperatura ambiente, cavo,
  sgancio termico 72 °C…). Regole: il valore specifico di un modello (peso, assorbimento) solo se letto per quel modello; l'IP, che è
  della serie, esteso alle varianti; **dove le schede danno valori diversi (versioni UE/USA, revisioni) il valore non è stato messo**;
  mai sovrascritto un valore già presente nella descrizione.
* **Nessun PDF scaricato**: i valori vengono da pagine HTML e dai testi delle schede letti dai risultati di ricerca. I cataloghi
  PDF del produttore (listino/catalogo e schede prodotto) potrebbero dare altri dati (EAN, pesi, portate…) ma vanno scaricati.

### Copertura (articoli con un valore, su 5.013)

| Attributo | Articoli | Attributo | Articoli | Attributo | Articoli |
|---|---|---|---|---|---|
| Pressione | 12 | Temperatura | 117 | Tensione | 76 |
| Frequenza | 6 | Potenza | 20 | Portata | 22 |
| Materiale | 4.395 | Finitura | 1.171 | Dimensioni | 2.538 |
| Altezza | 2.547 | Lunghezza | 2.848 | Spessore | 50 |
| Ø | 2.843 | DN | 3 | PN | 0 |
| SDR | 0 | Vie | 5 | Peso | 52 |
| Confezione | 82 | Attacco | 2.003 | Filettatura ★ | 1 |
| Maschio/femmina ★ | 41 | Interasse ★ | 0 | Derivazioni ★ | 1.961 |
| Colore ★ | 2.065 | Scarico ★ | 0 | Guarnizione ★ | 135 |
| Fluidi ★ | 0 | Normativa ★ | 171 | Reazione al fuoco ★ | 94 |
| Grado IP ★ | 41 | Classe isolamento ★ | 28 | Corrente ★ | 7 |
| Prevalenza ★ | 0 | Taratura ★ | 119 | Campo regolazione ★ | 23 |
| Accuratezza ★ | 0 | Uso ★ | 0 | Raccordo ★ | 28 |
| Compatibilità ★ | 1.518 | Validità ricambio ★ | 0 | EAN ★ | 0 |
| Comando ★ | 141 | Volume acqua ★ | 0 | Cavo ★ | 5 |
| Coibentazione ★ | 99 | Gamma ★ | 4.735 | Installazione | 3.293 |
| Coppia | 38 | Feritoie | 277 | | |

Zero articoli per PN, SDR, Interasse, Scarico, Fluidi, Prevalenza, Accuratezza, Uso, Validità ricambio, EAN, Volume acqua: sono
attributi da tubi/valvole/pompe/caldaie, che nel catalogo Air Control (canalizzazione, griglie, serrande, regolazione) non esistono
o non sono pubblicati. Restano nell'elenco: se arriveranno altri cataloghi si riempiono senza cambiare nulla.

### Scelte e limiti da conoscere

* Lasciato **come scritto** ciò che è ambiguo: `M-m` nei plenum/portabocchetta, «20-30c» (inclinazione del tetto), numeri finali dei
  collettori VMC (125/160), «24 el.», «Co» (descrizione troncata); non sono diventati attributi.
* La descrizione del catalogo a volte è troncata (`All` = Alluminio, `Bco` = Bianco): sciolti dove inequivocabili.
* Torque attuatori **TF** (Belimo): il catalogo dice 2 Nm, la scheda attuale Belimo dice 2,5 Nm (e IP42); in DB c'è 2 Nm (descrizione)
  e IP42 (web): da verificare con il fornitore.
* **UDE**: la sigla «230mc/300mc» è letta come portata d'aria in m³/h (confermato per UDE 30 H: 300 m³/h a 150 Pa, 18,9 l/24 h; per UDE 23 V
  non c'è scheda). I dati UDE vengono dal costruttore dell'unità (Elettroclima/Sabiana): da verificare che sia lo stesso modello.
* Dopo `import_catalogo.py` bisogna rilanciare `arricchisci.py` (lo fa già `avvia_import.bat`).

### Aggiungere dati

* Altro dato di una famiglia Air Control → `arricchimento/sito.py` (`FAM`).
* Altro dato di un componente di terzi → `arricchimento/web.py` (`DATI` per codice, `SERIE` per tutta una serie).
* Un nuovo modo di scrivere una descrizione → `arricchimento/parse.py`; poi `py -3.13 arricchisci.py --prova` per vedere l'effetto.

## Tabella `materiale`

Una riga per articolo, tutte le colonne del CSV: `codice` (chiave), `descrizione`, `sigla`, `marca`, `cod_fornitore`, `linea`, `serie`,
`um`, `listino`, `sc1`–`sc4`, `netto`, `vecchio_codice`, più `catalogo` (nome del file CSV) e `nomev1`. I testi sono quelli originali;
le celle vuote diventano NULL (anche `serie`, che in Air Control è sempre vuota); i numeri con la virgola diventano numerici.
