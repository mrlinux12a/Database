"""Elenco degli attributi (nell'ordine in cui li ha indicati l'utente). `nuovo` = quelli segnati ★ nella lista.

chiave       = nome nel database (tabella attributo / materiale_attributo)
etichetta    = come si vede nella pagina
gruppo       = raggruppamento per la visualizzazione
Gli ultimi (EXTRA) non sono nella lista dell'utente: servono solo dove l'informazione e' importante e non ha un posto
(installazione: cartongesso/muro...; coppia: attuatori; feritoie: diffusori lineari).
"""

# (chiave, etichetta, gruppo, nuovo)
ATTRIBUTI = [
    ("pressione", "Pressione (max di esercizio)", "Prestazioni", False),
    ("temperatura", "Temperatura (esercizio / ambiente / fluido)", "Prestazioni", False),
    ("tensione", "Tensione", "Elettrico", False),
    ("frequenza", "Frequenza", "Elettrico", False),
    ("potenza", "Potenza", "Elettrico", False),
    ("portata", "Portata", "Prestazioni", False),
    ("materiale", "Materiale", "Materiali e finiture", False),
    ("finitura", "Finitura", "Materiali e finiture", False),
    ("dimensioni", "Dimensioni", "Dimensioni", False),
    ("altezza", "Altezza", "Dimensioni", False),
    ("lunghezza", "Lunghezza", "Dimensioni", False),
    ("spessore", "Spessore", "Dimensioni", False),
    ("diametro", "Ø (diametro)", "Dimensioni", False),
    ("dn", "DN", "Dimensioni", False),
    ("pn", "PN", "Dimensioni", False),
    ("sdr", "SDR", "Dimensioni", False),
    ("vie", "Vie", "Dimensioni", False),
    ("peso", "Peso", "Confezione", False),
    ("confezione", "Quantità in confezione", "Confezione", False),
    ("attacco", "Attacco", "Attacchi", False),
    ("filettatura", "Tipo di filettatura / norma filetto", "Attacchi", True),
    ("maschio_femmina", "Maschio / femmina (per lato)", "Attacchi", True),
    ("interasse", "Interasse", "Dimensioni", True),
    ("n_derivazioni", "Numero di derivazioni / stacchi", "Attacchi", True),
    ("colore", "Colore", "Materiali e finiture", True),
    ("scarico", "Scarico (con/senza, dimensione)", "Attacchi", True),
    ("guarnizione", "Guarnizione / O-ring (materiale e colore)", "Materiali e finiture", True),
    ("fluidi", "Fluidi / gas compatibili", "Prestazioni", True),
    ("normativa", "Normativa / certificazione", "Normative", True),
    ("reazione_fuoco", "Classe di reazione al fuoco", "Normative", True),
    ("grado_ip", "Grado di protezione IP", "Elettrico", True),
    ("classe_isolamento", "Classe di isolamento elettrico", "Elettrico", True),
    ("corrente", "Corrente nominale", "Elettrico", True),
    ("prevalenza", "Prevalenza massima", "Prestazioni", True),
    ("taratura", "Taratura / set point", "Regolazione", True),
    ("campo_regolazione", "Campo di regolazione", "Regolazione", True),
    ("accuratezza", "Accuratezza", "Regolazione", True),
    ("uso", "Uso interno / esterno", "Uso", True),
    ("tipo_raccordo", "Tipo di raccordo / giunzione", "Attacchi", True),
    ("compatibilita", "Compatibilità (serie o modello)", "Uso", True),
    ("validita_ricambio", "Periodo di validità del ricambio", "Uso", True),
    ("ean", "EAN / GTIN", "Codici", True),
    ("comando", "Tipo di comando / corsa", "Regolazione", True),
    ("volume_acqua", "Volume d'acqua", "Prestazioni", True),
    ("lunghezza_cavo", "Lunghezza cavo o guaina", "Dimensioni", True),
    ("coibentazione", "Coibentazione", "Materiali e finiture", True),
    ("tipo_base", "Prodotto di base / gamma", "Uso", True),
    ("installazione", "Installazione", "Uso", False),   # extra
    ("coppia", "Coppia", "Regolazione", False),          # extra (attuatori)
    ("feritoie", "Numero di feritoie", "Dimensioni", False),   # extra (diffusori lineari)
]
EXTRA = {"installazione", "coppia", "feritoie"}

# etichette corte per la pagina (la lunga resta nel suggerimento e nell'elenco di copertura)
BREVE = {
    "pressione": "Pressione", "temperatura": "Temperatura", "tensione": "Tensione", "frequenza": "Frequenza",
    "potenza": "Potenza", "portata": "Portata", "materiale": "Materiale", "finitura": "Finitura",
    "dimensioni": "Dimensioni", "altezza": "Altezza", "lunghezza": "Lunghezza", "spessore": "Spessore",
    "diametro": "Ø", "dn": "DN", "pn": "PN", "sdr": "SDR", "vie": "Vie", "peso": "Peso",
    "confezione": "Confezione", "attacco": "Attacco", "filettatura": "Filettatura",
    "maschio_femmina": "Maschio/femmina", "interasse": "Interasse", "n_derivazioni": "Derivazioni",
    "colore": "Colore", "scarico": "Scarico", "guarnizione": "Guarnizione", "fluidi": "Fluidi",
    "normativa": "Normativa", "reazione_fuoco": "Reazione al fuoco", "grado_ip": "Grado IP",
    "classe_isolamento": "Classe isolamento", "corrente": "Corrente", "prevalenza": "Prevalenza",
    "taratura": "Taratura", "campo_regolazione": "Campo regolazione", "accuratezza": "Accuratezza",
    "uso": "Uso", "tipo_raccordo": "Raccordo", "compatibilita": "Compatibilità",
    "validita_ricambio": "Validità ricambio", "ean": "EAN", "comando": "Comando",
    "volume_acqua": "Volume acqua", "lunghezza_cavo": "Cavo", "coibentazione": "Coibentazione",
    "tipo_base": "Gamma", "installazione": "Installazione", "coppia": "Coppia", "feritoie": "Feritoie",
}
assert set(BREVE) == {a[0] for a in ATTRIBUTI}
CHIAVI = [a[0] for a in ATTRIBUTI]
