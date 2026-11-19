# -*- coding: utf-8 -*-
"""Famiglie COMUNI e TIPI: il tipo di prodotto che due cataloghi (o due righe dello stesso catalogo) chiamano in modo diverso
ma e' la stessa cosa (il «Tee» di Aquatechnik e il «Raccordo tee» di Air Control; le 83 famiglie «valvola» in 16 tipi). Lista
controllata e condivisa: si allunga a mano, una voce alla volta, solo quando i prodotti sono davvero dello stesso tipo.

Ogni voce: (nome della famiglia, regex sul nomeV2 in minuscolo [, regex sul nomeV1 in minuscolo] [, INCERTO | ANCHE(...)]).
La prima che combacia vince. Si applica a TUTTI gli articoli con nomeV2 (anche a quelli senza famiglia): e' la prima parola/le
prime parole del nomeV2 a dire che tipo di prodotto e'. Le varianti (ridotto, intermedio, 45°, 90°, con girello, chiuso,
aperto, modello PSF/DLF/LAF..., gamma Solar/Autoflow/Legiomix...) NON sono famiglie: restano nel nomeV2 e negli attributi.
  * regex sul nomeV1: quando il tipo e' scritto nella descrizione ma e' un attributo e quindi non e' piu' nel nomeV2 («bicono»,
    «a pressare», «per gas», «per diffusori»).
  * INCERTO: l'articolo va nel tipo piu' vicino ma non e' sicuro che sia quello (nella pagina: in giallo nel riquadro «Famiglie
    raggruppate in questo tipo»).
  * ANCHE("Tipo B", ...): indecisi tra due o piu' tipi -> l'articolo sta nel primo (famiglia_id) e ANCHE negli altri
    (tabella tipo_incerto); in giallo in tutti.

Si applica con  py -3.15 unisci_famiglie.py  (dopo proponi_famiglie.py --assegna, ripetibile quando si vuole).

Dubbi / non unite (di proposito)
  * «Collare»: in Aquatechnik sono collari dei sistemi a saldare/a pressare, in Air Control collari di fissaggio dei canali:
    due tipi diversi («Collare» e «Collare di fissaggio»).
  * «Valvola» generica: la valvola a sfera (acqua) non e' la valvola di mandata/ripresa (aria): le valvole sono unite solo per
    TIPO, mai per la sola parola «valvola». Le «Valvola mandata/ripresa con collarino» di Air Control restano come sono.
  * «Attacco a sella» (tubo dell'acqua) e «Stacco a sella» (canale dell'aria): stessa funzione, pezzi diversi.
  * «Kit», «Coppia», «Ricambio», «Gruppo»: parole generiche, non sono tipi; si guarda cosa viene dopo (Coppia collettori =
    Collettore, Coppia bocchettoni = Bocchettone, Ricambio cartuccia = Cartuccia...).
  * «Bocchettone» (raccordo a tre pezzi dell'acqua) e «Bocchetta» (diffusore dell'aria): falsi amici, mai insieme.
  * Caleffi: «Tee di bypass» (con ugello, per valvole di zona), «Tee Dirtmag», «Tee sdoppiatore» sono componenti, non
    raccordi a T; «Giunto antivibrante» e «Giunto estensibile» (per gas) non sono giunti di raccordo.
  * Air Control «Raccordo dritto piatto» (canale VMC tondo/piatto): pezzo dei canali dell'aria, non un raccordo idraulico.
Poco sicure ma unite (da confermare): Giunto (giunto filettato dell'acqua / giunto dei tubi rigidi isolati), Collettore (collettore
dell'acqua / collettore del plenum VMC), Curva e gomito (sono sinonimi: curva per i canali, gomito per i tubi).
"""
import re

INCERTO = {"incerto": True}


def ANCHE(*tipi):
    """Indecisi: l'articolo sta nel tipo della voce e ANCHE in questi."""
    return {"incerto": True, "anche": tipi}


COMUNI = [
    # ---- Watts (2026-11-19). Vanno prima delle altre: alcune parole («giunto», «guaina») qui vogliono dire un altro pezzo.
    # (A) nei tipi che c'erano, con le parole di Watts
    ("Giunto antivibrante", r"^giunto$", r"\bepdm\b", INCERTO),         # ZKB/ZKT in EPDM con DN/PN: non e' scritto «antivibrante»
    ("Pozzetto", r"^guaina\b(?!\s+(?:isolante|corrugata))", INCERTO),   # guaina per termometro/sonda = pozzetto (non la guaina isolante)
    ("Pozzetto", r"^kit pozzetto\b", INCERTO),
    ("Valvola di sicurezza", r"^scarico di sicurezza termico\b", INCERTO),   # STS.S: «valvola» non e' scritto (lo STS si')
    ("Gruppo di riempimento / caricamento", r"^valvola automatica di riempimento\b", INCERTO),
    ("Separatore d'aria", r"^separatore d'aria\b"),
    ("Attuatore", r"^attuatore elettronico\b"),
    ("Termostato", r"^termostato\b(?!\s+attuatore)"),                  # «termostato attuatore» Caleffi: non si sa che cos'e'
    ("Termostato", r"^(?:bitermostato|microtermostato)\b", INCERTO),
    # (C) tipi nuovi che raccolgono anche articoli di Caleffi rimasti senza famiglia (una scala diversa = un nomeV2 diverso)
    ("Manometro", r"^manometro\b"),
    ("Manometro", r"^idrometro\b", INCERTO),                           # manometro con la scala in metri d'acqua
    ("Termomanometro", r"^termomanometro\b"),
    ("Termometro", r"^termometro\b"),
    ("Cronotermostato", r"^cronotermostato\b"),
    ("Pressostato", r"^pressostato\b"),
    ("Flussostato", r"^flussostato\b"),
    ("Sonda", r"^sonda\b"),
    ("Imbuto di scarico", r"^imbuto (?:di )?scarico\b"),
    ("Ammortizzatore colpo d'ariete", r"^ammortizzatore colpo (?:d')?ariete\b"),
    ("Ricciolo / serpentina", r"^ricciolo\b"),
    ("Ricciolo / serpentina", r"^serpentina\b", INCERTO),             # SRX: stessa funzione del ricciolo (sifone per manometro)?
    ("Alimentatore", r"^alimentatore\b"),
    ("Sensore perdite acqua", r"^sensore (?:rilevamento )?perdite\b"),
    # (B) tipi nuovi dentro famiglie/categorie che c'erano (da unire poi con gli altri tipi della categoria)
    ("Valvola di sovrapressione", r"^valvola (?:di )?sovrapressione\b"),
    ("Valvola di intercettazione combinata", r"^valvola di intercettazione combinata\b"),
    ("Valvola di intercettazione per vaso di espansione", r"^valvola per intercettazione vaso di espansione\b"),
    ("Gruppo di rilancio e miscelazione", r"^gruppo (?:compatto )?rilancio(?:/| e )miscelazione\b"),
    ("Gruppo di rilancio e miscelazione", r"^gruppo rilancio punto fisso\b|^gruppo di miscelazione e ricircolo\b", INCERTO),
    ("Gruppo di rilancio", r"^gruppo (?:compatto )?rilancio\b"),
    ("Guscio isolante", r"^guscio isolante\b"),
    ("Modulo di collegamento termostati", r"^modulo collegamento\b"),
    ("Kit tirante", r"^kit tirante\b"),
    ("Tubo di collegamento", r"^coppia tubi collegamento\b"),

    # ---- famiglie comuni a piu' cataloghi (2026-11-18) --------------------------------------------------------------------
    ("Tee", r"^(?:fires\s+)?tee\b(?!\s+(?:di\s+by-?pass|dirtmag|sdoppiatore))|^raccordo (?:a )?tee\b"),
    ("Tee", r"^raccordo derivazione\b", INCERTO),                       # Safety-Plus Ø26x1/2"Fx26: e' una derivazione a T
    ("Curva / Gomito", r"^(?:fires\s+)?(?:gomito|curva)\b|^raccordo gomito\b"),
    ("Riduzione", r"^(?:fires\s+)?riduzione\b"),
    ("Riduzione", r"^raccordo per valvola di sfogo aria\b", INCERTO),   # Ø3/4"Mx3/8"F: maschio grande, femmina piccola
    ("Tappo", r"^tappo\b"),
    ("Manicotto", r"^(?:fires\s+)?manicotto\b"),
    ("Giunto", r"^(?:fires\s+)?giunto\b(?!\s+(?:antivibrante|estensibile))"),
    ("Tubo", r"^tubo\b|^isoline(?:-plus)?\s+tubo\b"),
    ("Collettore", r"^collettore\b|^coppia collettori\b"),
    ("Collettore", r"^gruppo collettore\b", INCERTO),                   # collettore premontato con valvole / senza cassetta

    # ---- Valvole (2026-11-19): il TIPO di valvola e' la famiglia; gamma (Solar, Dynamical, Ballstop...), forma (diritta,
    # squadra), foratura, Kv, lunghezza restano nel nomeV2 / negli attributi. Vanno prima le piu' specifiche.
    ("Valvola di intercettazione combustibile", r"^valvola di intercettazione combustibile\b"),
    ("Valvola di sicurezza", r"^valvola (?:di sicurezza|scarico termico|scarico sicurezza termica)\b"),
    ("Valvola di zona", r"^valvola di zona\b"),                        # «a sfera» qui e' l'otturatore, non il tipo
    ("Valvola deviatrice", r"^valvola (?:a )?sfera deviatrice\b|^valvola deviatrice\b"),
    ("Valvola a sfera", r"^valvola (?:a )?sfera\b|^valvola di intercettazione a sfera\b|^coppia valvole (?:a )?sfera\b"
                        r"|^rubinetto d'intercettazione a sfera\b"),
    ("Valvola a sfera", r"^rubinetto a sfera\b", ANCHE("Rubinetto di scarico")),   # con portagomma e antigelo
    ("Valvola a farfalla", r"^valvola a farfalla\b"),
    ("Valvola miscelatrice", r"^valvola miscelatrice\b"),
    ("Valvola miscelatrice", r"^gruppo valvola miscelatrice\b|^valvola flangiata\b", INCERTO),   # «3 vie flangiata per 600008» (Legiomix)
    ("Valvola termostatica / termostatizzabile", r"^valvola (?:(?:doppia )?squadra |diritta )?termostat(?:ica|izzabile)\b"),
    ("Valvola di bilanciamento", r"^valvola di bilanciamento\b"),
    ("Valvola di bilanciamento", r"^valvola di intercettazione/preregolazione\b", INCERTO),
    ("Valvola di bilanciamento", r"^valvola flowmatic\b", ANCHE("Valvola di regolazione")),
    ("Valvola di sfogo aria", r"^valvola (?:di )?(?:sfogo|sfoga) aria\b|^valvola (?:manuale|automatica igroscopica) sfogo aria\b"),
    ("Valvola di sfogo aria", r"^valvola antiaspirazione per valvola di sfogo aria\b", INCERTO),
    ("Valvola di ritegno", r"^valvola (?:di ritegno|doppio ritegno)\b"),
    ("Valvola di regolazione", r"^valvola di regolazione\b"),
    ("Valvola di regolazione", r"^valvola (?:bypass differenziale|modulante)\b", INCERTO),
    ("Valvola anticondensa / antigelo / antitermosifone", r"^valvola (?:anticondensa|antigelo|antitermosifone)\b"),
    ("Valvola anticondensa / antigelo / antitermosifone", r"^valvola scarico fluido\b", INCERTO),   # serie 108 (cartuccia antigelo per 108-109)
    ("Valvola manuale", r"^valvola manuale (?:diritta|a squadra|squadra)\b"),
    ("Valvola monotubo / bitubo", r"^valvola (?:monotubo|bitubo)\b"),
    ("Valvola motorizzata", r"^valvola motorizzata\b", INCERTO),       # «3 vie motorizzata»: deviatrice o miscelatrice non e' scritto

    # ---- Raccordi (2026-11-19). «bicono» e «a pressare» sono attributi (tipo_raccordo): si leggono nel nomeV1. Il raccordo
    # bocchettone va in Bocchettone (come tee e gomito in Tee e Curva / Gomito).
    ("Raccordo a pressare", r"^raccordo\b", r"^raccordo a pressare\b"),
    ("Raccordo bicono", r"^raccordo\b", r"\bbicono\b"),
    ("Bocchettone", r"^raccordo bocchettone\b"),
    ("Raccordo diritto", r"^raccordo diritto\b", r"\ba bocchettone\b", ANCHE("Bocchettone")),   # Solar 3 pezzi a bocchettone
    ("Raccordo diritto", r"^raccordo (?:diritto|ridotto diritto)\b"),   # «ridotto» = filetto piu' piccolo del tubo, non una riduzione
    ("Raccordo adattatore", r"^raccordo adattatore\b"),
    ("Raccordo adattatore", r"^raccordo eurocono\b|^adattatore darcal\b", INCERTO),
    ("Raccordo meccanico", r"^raccordo meccanico\b", r"\bdarcal\b", ANCHE("Raccordo adattatore")),   # stessa serie 680 degli adattatori
    ("Raccordo meccanico", r"^raccordo meccanico\b"),
    ("Raccordo di testa", r"^raccordo (?:di testa|per derivazione di testa)\b"),
    ("Raccordo con attacco radiale", r"^raccordo (?:doppio attacco radiale|con attacco radiale)\b"),
    ("Raccordo con attacco radiale", r"^raccordo portatermometro\b", INCERTO),
    ("Raccordo monoblocco", r"^raccordo monoblocco\b"),
    ("Raccordo di collegamento", r"^raccordo collegamento\b"),
    ("Raccordo di collegamento", r"^raccordo\b", r"\bserie 383\b", INCERTO),         # stessa serie dei raccordi di collegamento
    ("Riduzione", r"^raccordo$", r"^raccordo ø[0-9./]+\"f\s*x\s*[0-9./]+\"m\b", INCERTO),   # femmina x maschio di misure diverse
    ("Raccordo a croce", r"^raccordo a croce\b"),
    ("Corpo raccordo", r"^corpo raccordo\b"),

    # ---- Altri tipi dell'acqua (2026-11-19) --------------------------------------------------------------------------------
    ("Bocchettone", r"^bocchettone\b|^coppia bocchettoni\b"),
    ("Detentore", r"^detentore\b"),
    ("Coppia valvola e detentore", r"^coppia valvol[ae]\b.*\bdetentore\b"),
    ("Kit valvola + detentore + testa termostatica", r"^kit valvola \+ detentore\b"),
    ("Kit valvola + detentore + testa termostatica", r"^valvola \+ detentore\b", INCERTO),   # stessa cosa senza la parola «kit»
    ("Riduttore di pressione", r"^riduttore di pressione\b"),
    ("Miscelatore termostatico", r"^miscelatore termostatico\b"),
    ("Miscelatore antilegionella", r"^miscelatore (?:elettronico )?(?:legiomix )?antilegionella\b|^miscelatore elettronico legiomix\b"),
    ("Stabilizzatore di portata", r"^stabilizzatore\b"),
    ("Defangatore", r"^defangatore\b"),
    ("Defangatore", r"^filtro defangatore\b", INCERTO),
    ("Defangatore", r"^separatore con filtro magnetico\b", ANCHE("Separatore idraulico")),
    ("Separatore idraulico", r"^separatore idraulico\b"),
    ("Separatore idraulico", r"^separatore esterno\b", INCERTO),      # Sepcoll
    ("Disaeratore", r"^disaeratore\b"),
    ("Disconnettore", r"^disconnettore\b"),
    ("Disconnettore", r"^gruppo disconnettore\b", INCERTO),           # disconnettore con filtro e valvole
    ("Filtro a Y", r"^filtro a y\b"),
    ("Filtro per gas", r"^filtro regolatore\b", r"\bper gas\b", INCERTO),   # filtro + regolatore insieme
    ("Filtro per gas", r"^filtro\b", r"\bper gas\b"),
    ("Filtro ispezionabile", r"^filtro ispezionabile\b"),
    ("Vaso di espansione", r"^vaso di espansione\b"),
    ("Coibentazione", r"^coibentazione\b"),
    ("Kit coibentazione", r"^kit coibentazione\b", ANCHE("Coibentazione")),
    ("Pozzetto", r"^pozzetto\b"),
    ("Contatore volumetrico", r"^contatore volumetrico\b"),
    ("Contatore volumetrico", r"^contatore con valvola\b", INCERTO),   # «contatore acqua calda sanitaria con valvola»
    ("Contatore di calore", r"^contatore conteca\b", INCERTO),         # Conteca: «di calore» non e' scritto (pozzetti mandata/ritorno)
    ("Integratore", r"^integratore\b"),
    ("Modulo d'utenza", r"^modulo utenza\b"),
    ("Modulo d'utenza", r"^modulo (?:conteca|idrico plurimod|plurimod)\b", INCERTO),
    ("Satellite", r"^satellite\b"),
    ("Gruppo di regolazione", r"^gruppo di regolazione\b"),
    ("Gruppo di distribuzione", r"^gruppo di distribuzione\b"),
    ("Gruppo di commutazione/distribuzione", r"^gruppo di commutazione\b", ANCHE("Gruppo di distribuzione")),
    ("Gruppo di circolazione", r"^gruppo di circolazione\b"),
    ("Gruppo di riempimento / caricamento", r"^gruppo (?:di riempimento|caricamento|compatto caricamento)\b"),
    ("Gruppo di collegamento", r"^gruppo di collegamento\b"),
    ("Gruppo di sicurezza", r"^gruppo (?:di )?sicurezza\b"),
    ("Gruppo controllo temperatura", r"^gruppo controllo temperatura\b"),
    ("Gruppo di testa", r"^gruppo di testa\b"),
    ("Regolatore di pressione differenziale", r"^regolatore di pressione differenziale\b"),
    ("Regolatore climatico", r"^regolatore climatico\b"),
    ("Regolatore digitale", r"^regolatore digitale modulante\b", ANCHE("Gruppo di regolazione")),   # Ø3/4" con pompa
    ("Regolatore digitale", r"^regolatore digitale\b"),
    ("Rubinetto di arresto", r"^rubinetto arresto\b"),
    ("Rubinetto di scarico", r"^rubinetto scarico\b"),
    ("Rubinetto di intercettazione", r"^rubinetto (?:intercettazione|automatico)\b"),
    ("Rubinetto portamanometro", r"^rubinetto (?:porta)?manometro\b"),
    ("Giunto estensibile", r"^giunto estensibile\b"),
    ("Collare di fissaggio", r"^collare fissaggio\b"),
    ("Collare", r"^collare$"),
    ("Collare", r"^collare con (?:protezione|flangia|calotta)\b", INCERTO),
    ("Codolo", r"^codolo\b"),
    ("Innesto diretto", r"^innesto diretto\b"),
    ("Sorpasso", r"^sorpasso\b"),
    ("Attacco a sella", r"^attacco a sella\b"),
    ("O-ring", r"^(?:anello )?o-ring\b"),
    ("Bobina", r"^bobina\b"),
    ("Cartuccia", r"^(?:ricambio )?cartuccia\b"),
    ("Vitone", r"^(?:ricambio )?vitone\b"),
    ("Espansore", r"^espansore\b"),
    ("Estrattore per espansore", r"^estrattore per espansore\b"),
    ("Kit centrale termica", r"^kit centrale termica\b"),
    ("Kit di fissaggio", r"^kit (?:di )?fissaggio\b"),
    ("Kit eccentrico", r"^kit eccentrico\b"),
    ("Kit mix con by-pass antilegionella", r"^kit mix\b"),
    ("Kit termostato di sicurezza", r"^kit termostato (?:di )?sicurezza\b"),

    # ---- Tipi dell'aria (Air Control, 2026-11-19): il modello (PSF, DLF, LAF, MDF...), chiuso/aperto, M-m, VMC, L..., per
    # muro/cartongesso restano nel nome. La macchina («per Daikin ...») e' compatibilita'.
    # «Plenum bocchetta per Daikin ..., profondita' 30 cm» (codici PLMB-): plenum di mandata della macchina con bocchetta
    ("Plenum di mandata", r"^plenum bocchetta,? profondit", ANCHE("Plenum per bocchetta")),
    ("Plenum per bocchetta", r"^plenum bocchetta\b"),
    ("Plenum per diffusore", r"^plenum\b", r"^plenum (?:m-m vmc )?per diffusori\b"),
    ("Plenum per diffusore", r"^plenum con diffusore\b"),
    ("Plenum per griglia", r"^plenum\b", r"^plenum (?:\S+ )?per griglia\b"),
    ("Plenum cablato", r"^plenum cablato\b"),
    ("Plenum di mandata", r"^plenum (?:di )?mandata\b"),
    ("Plenum di ripresa", r"^plenum di ripresa\b"),
    ("Plenum di mandata", r"^plenum (?:universale )?chiuso\b", ANCHE("Plenum di ripresa")),   # non dice se mandata o ripresa
    ("Portabocchetta", r"^portabocchetta\b"),
    ("Diffusore lineare", r"^diffusore lineare\b"),
    ("Diffusore circolare", r"^diffusore circolare\b"),
    ("Diffusore ad alette curve", r"^diffusore (?:con )?alette curve\b"),
    ("Griglia di ripresa", r"^griglia (?:di )?ripresa\b"),
    ("Griglia di transito", r"^griglia di transito\b"),
    ("Griglia circolare", r"^griglia circolare\b"),
    ("Griglia circolare", r"^griglia \+ rete\b", INCERTO),             # «Griglia + rete + deviax. flusso Ø125»
    ("Griglia pedonabile", r"^griglia pedonabile\b"),
    ("Serranda tagliafuoco", r"^serranda tagliafuoco\b"),
    ("Serranda tagliafuoco", r"^serranda circolare btt\d", INCERTO),   # stesso modello BTT25 delle tagliafuoco
    ("Serranda di taratura", r"^serranda (?:di )?taratura\b"),
    ("Serranda di regolazione", r"^serranda di regolazione\b"),
    ("Serranda di taratura", r"^serranda circolare con perno\b", ANCHE("Serranda di regolazione")),
    ("Serranda motorizzata", r"^serranda motorizzata\b"),
    ("Serranda di bypass", r"^serranda by-?pass\b"),
    ("Serranda captatrice", r"^serranda captatrice\b"),
    ("Bocchetta a barre fisse", r"^bocchetta barre fisse\b"),
    ("Bocchetta di mandata", r"^bocchetta di mandata\b"),
    ("Bocchetta per canali circolari", r"^bocchetta per canali circolari\b"),
    ("Silenziatore circolare", r"^silenziatore circolare\b"),
    ("Silenziatore flessibile", r"^silenziatore flessibile\b"),
    ("Silenziatore flessibile", r"^silenziatore isolato\b", INCERTO),
    ("Controtelaio", r"^controtelaio\b"),
    ("Regolatore di portata", r"^regolatore (?:di )?portata\b"),
    ("Canale microforato", r"^canale microforato\b"),
    ("Kit di distribuzione", r"^kit distribuzione\b"),
    ("Kit comandi", r"^kit comandi\b"),
    ("Kit cablaggio serrande", r"^kit cablaggio\b"),
    ("Kit di continuità", r"^kit (?:di )?continuit"),
    ("Tee di bypass", r"^tee di by-?pass\b"),
]


def _voce(v):
    rx1 = next((x for x in v[2:] if isinstance(x, str)), None)
    opz = next((x for x in v[2:] if isinstance(x, dict)), {})
    return (v[0], re.compile(v[1]), re.compile(rx1) if rx1 else None, bool(opz.get("incerto")), tuple(opz.get("anche", ())))


_REGOLE = [_voce(v) for v in COMUNI]
TIPI = list(dict.fromkeys([r[0] for r in _REGOLE] + [t for r in _REGOLE for t in r[4]]))   # tutti i nomi di tipo


def classifica(nomev2, nomev1=""):
    """-> (tipo, incerto, (altri tipi in cui sta ANCHE)) per questo articolo, oppure None."""
    n = (nomev2 or "").strip().lower()
    n1 = (nomev1 or "").strip().lower()
    for nome, rx, rx1, incerto, anche in _REGOLE:
        if rx.search(n) and (rx1 is None or rx1.search(n1)):
            return nome, incerto, anche
    return None


def famiglia_comune(nomev2, nomev1=""):
    """-> nome della famiglia comune per questo nomeV2 (e, se la voce lo chiede, anche il nomeV1), oppure None."""
    c = classifica(nomev2, nomev1)
    return c[0] if c else None
