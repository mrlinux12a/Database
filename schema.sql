-- Schema di db_serio_finale. Si puo' rieseguire senza danni (CREATE ... IF NOT EXISTS).
-- Stessi nomi di colonna della tabella `materiale` del database catalogo_finale (progetto app2/db),
-- piu' `catalogo` (il file CSV di provenienza) per poter aggiungere altri fornitori.

CREATE TABLE IF NOT EXISTS materiale (
    codice          text PRIMARY KEY,           -- "Codice"          (codice interno, univoco)
    descrizione     text NOT NULL,              -- "Descrizione"     (testo originale del catalogo)
    sigla           text,                       -- "Sigla"
    marca           text,                       -- "Marca"
    cod_fornitore   text NOT NULL,              -- "Cod. Fornitore"
    linea           text,                       -- "Linea"           (es. "001 Distribuzione Aeraulica")
    serie           text,                       -- "Serie"           (vuota nei cataloghi Air Control)
    um              text,                       -- "U.M."
    listino         numeric(14,5),              -- "Listino"
    sc1             numeric(7,2),               -- "Sc1" ... "Sc4"   (sconti in %)
    sc2             numeric(7,2),
    sc3             numeric(7,2),
    sc4             numeric(7,2),
    netto           numeric(14,5),              -- "Netto"
    vecchio_codice  text,                       -- "Vecchio Codice"
    catalogo        text NOT NULL               -- nome del file CSV, senza ".csv"
);

CREATE INDEX IF NOT EXISTS materiale_catalogo_idx ON materiale (catalogo);
CREATE INDEX IF NOT EXISTS materiale_linea_idx    ON materiale (linea);

-- ---- arricchimento (nome + attributi), riempito da arricchisci.py ------------------------------------------------
-- nomev1: il nome piu' semplice e completo (descrizione ripulita + informazioni delle schede del produttore).
ALTER TABLE materiale ADD COLUMN IF NOT EXISTS nomev1 text;
-- nomev2: nomev1 senza le informazioni che l'articolo ha gia' come attributo (arricchimento/v2.py).
ALTER TABLE materiale ADD COLUMN IF NOT EXISTS nomev2 text;

-- elenco degli attributi possibili (la lista indicata dall'utente; `nuovo` = quelli segnati con la stella)
CREATE TABLE IF NOT EXISTS attributo (
    chiave      text PRIMARY KEY,
    etichetta   text    NOT NULL,
    gruppo      text    NOT NULL,
    nuovo       boolean NOT NULL DEFAULT false,
    ordine      integer NOT NULL
);
ALTER TABLE attributo ADD COLUMN IF NOT EXISTS breve text;     -- etichetta corta per la pagina (es. "Grado IP")

-- un attributo per riga, SOLO se il valore e' stato trovato (niente NULL: se non c'e', non c'e' la riga)
CREATE TABLE IF NOT EXISTS materiale_attributo (
    codice      text NOT NULL REFERENCES materiale(codice) ON DELETE CASCADE,
    chiave      text NOT NULL REFERENCES attributo(chiave),
    valore      text NOT NULL,                  -- valore da mostrare (es. "600 x 400 mm", "alluminio")
    valore_num  numeric,                        -- numero, quando ha senso (per filtrare/ordinare)
    unita       text,                           -- unita' di valore_num (mm, V, m3/h ...)
    origine     text NOT NULL,                  -- da dove arriva: descrizione | codice | sito | web
                                                --   descrizione = testo del catalogo; codice = lettere/cifre del codice;
                                                --   sito = scheda del produttore (aircontrolclima.it), valida per la famiglia;
                                                --   web = scheda/pagina di un costruttore terzo (es. Belimo)
    fonte       text,                           -- indirizzo web della pagina/documento (origine sito o web)
    PRIMARY KEY (codice, chiave)
);
CREATE INDEX IF NOT EXISTS materiale_attributo_chiave_idx ON materiale_attributo (chiave, valore);
