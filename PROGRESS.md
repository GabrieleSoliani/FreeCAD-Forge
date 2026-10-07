# PROGRESS — FreeCAD Forge

Leggere questo file per primo a ogni ripresa. Prompt completo del progetto: `FORGE_PROMPT.md`.
Si lavora **solo in locale** sul PC Windows (niente cloud, vedi `DECISIONS.md` 2026-10-07).

## Stato attuale (2026-10-07)

- **Fase 0 — Setup: completata.** Build locale funzionante, baseline dei test registrata.
- **Fase 1 — Analisi del divario: completata.** `GAP_ANALYSIS.md`; ordine milestone in `DECISIONS.md`.
- **M1 — Interfaccia unificata: completata** (tag `forge-m1`).
- **M3 — Robustezza ed errori: completata** (tag `forge-m3`).
  - [x] M3.1 Patch al core: raccordi/smussi/gusci non validi o senza effetto ora danno errore; sformo con
        messaggio (vedi `CORE_PATCHES.md`, `BENCHMARK.md`, `ForgeTests/TestForgeRobustness.py`).
  - [x] M3.2 Diagnostica in italiano (`forgelib/diagnostics.py`): spiegazioni, suggerimenti con raggio/spessore
        massimo calcolato, feature senza effetto, corpi divisi; comando "Diagnostica feature" (scheda Valuta) e
        avvisi automatici nell'area notifiche dopo ogni ricalcolo in Forge.
  - [x] M3.3 Modelli di riferimento in `forge_examples/` (5 esercizi, volumi verificati) e tempi di ricalcolo in `BENCHMARK.md`.
  - [x] M1.1 Modulo `src/Mod/Forge` (solo Python) registrato nella build; workbench "Forge" con command
        manager a schede (Schizzo, Feature, Superfici, Valuta, Assieme, Tavola) e cambio scheda
        automatico in base al contesto (tavola attiva, schizzo in modifica, assieme attivo).
  - [x] M1.2 Modifica dello schizzo restando in Forge (patch in `ViewProviderSketch`, vedi
        `CORE_PATCHES.md`); in modifica la scheda Schizzo mostra le toolbar "Disegno" e "Vincoli".
  - [x] M1.3 Impostazioni stile SolidWorks (navigazione, Forge all'avvio, scorciatoie F, Ctrl+1..8,
        Ctrl+B) applicabili e annullabili dal menu Forge, proposte alla prima attivazione. Al posto di un
        preference pack (vedi `DECISIONS.md`).
  - [x] M1.4 Barra heads-up sovrapposta alla vista 3D (adatta, zoom finestra, orientamento, stile di
        visualizzazione, sezione, nascondi/mostra, proiezione). Disattivabile con il parametro `ShowHeadsUp`.
  - [x] M1.5 Rollback bar: cursore "Rollback" accanto alle linguette per il corpo attivo e comandi
        indietro/avanti/fine nella scheda Feature (basati su `Body.Tip`, annullabili).
        Limiti: le cartelle dentro un Body non sono supportate da PartDesign (non implementate); il riordino
        resta quello di FreeCAD (`PartDesign_MoveFeature`, trascinamento nell'albero) che già controlla le dipendenze.
  - [x] M1.6 Menu radiale contestuale (comando `Forge_RadialMenu`, tasto S con le impostazioni SolidWorks).
        Le mouse gestures restano quelle dello stile di navigazione "Gesture" di FreeCAD (non replicate).

- **M8 (parte anticipata) — Valutazione: interferenze e sformo, completata.**
  - [x] `forgelib/evaluate.py`: interferenze/contatti/giochi tra coppie di solidi (Link e assiemi in posizione
        globale), analisi di sformo per faccia (positivo, negativo, insufficiente, a cavallo).
  - [x] Comandi "Rileva interferenze" (schede Valuta e Assieme) e "Analisi di sformo" (scheda Valuta).
        Parametri: `Clearance` (gioco minimo, mm), `MinDraftAngle` (gradi).

- **M2 — Schizzo: completata** (tag `forge-m2`; M2.2 rimandata).
  - [x] M2.1 Diagnosi schizzo (`forgelib/sketch_doctor.py`, comando "Diagnosi schizzo" nella scheda Schizzo e nella
        toolbar Vincoli): stato (gradi di libertà, conflitti, ridondanze, malformati) e correzioni verificate una per una
        disattivando temporaneamente ciascun vincolo sospetto; quote proposte per prime; applicazione annullabile.
  - [ ] M2.2 Inferenze più ricche durante il disegno: rimandato (richiede modifiche estese al C++ dello Sketcher su un
        comportamento solo visivo; FreeCAD ha già vincoli automatici e snap). Resta in GAP_ANALYSIS.
  - [x] M2.3 Blocchi di schizzo (`forgelib/sketch_blocks.py`): "Salva blocco" (spigoli selezionati + vincoli interni,
        file JSON in `<dati utente>/Forge/Blocchi`) e "Inserisci blocco" nella toolbar Disegno in modifica.
  - [x] M2.4 Schizzo 3D ridotto (`forgelib/features/sketch3d.py`, comando "Schizzo 3D" nella scheda Schizzo): polilinea
        o spline 3D da punti/vertici selezionati, aperta o chiusa, raccordi agli spigoli; usabile come percorso di sweep.
        Limite: nessun vincolo 3D tra entità (si modificano i punti nelle proprietà, anche con espressioni).

- **M5 — Lamiera e saldature: in corso.**
  - [x] M5.1 Lamiera: addon SheetMetal (LGPL) integrato in `src/Mod/SheetMetal` (vedi `THIRD_PARTY.md`); scheda Forge
        "Lamiera" con tutti i suoi comandi; `forgelib/sheetmetal.py` con tabella di piega (tolleranza/deduzione, fattore K
        dello sviluppo) ed esportazione DXF dello sviluppo; comandi "Tabella di piega" ed "Esporta sviluppo DXF".
  - [ ] M5.2 Profilati strutturali con libreria UNI/EN, rifilatura, distinta di taglio.

## Ambiente e comandi (Windows locale)

Toolchain: pixi 0.81 + MSVC 14.44 (Build Tools 2022), Ninja, ccache, Qt 6.11, Python 3.13, OCCT 8.0.

```
pixi run configure-rel-with-deb-info "-DENABLE_DEVELOPER_TESTS=ON"   # ~3,5 min
pixi run build                                                      # build completa a freddo ~48 min
pixi run cmake --build build/relWithDebInfo --target Forge          # solo il modulo Forge (secondi)
pixi run build/relWithDebInfo/bin/FreeCADCmd.exe -t 0               # test Python headless
pixi run build/relWithDebInfo/bin/FreeCADCmd.exe -t ForgeTests.TestForgeApp
pixi run build/relWithDebInfo/bin/FreeCAD.exe -t ForgeTests.TestForgeGui     # test GUI (apre una finestra)
```

ctest: i test dei moduli richiedono le cartelle `build/relWithDebInfo/Mod/*` nel `PATH`, altrimenti
falliscono con `0xc0000135` (DLL non trovata). Esempio (PowerShell dentro `pixi run`):
`$env:PATH = (Get-ChildItem build/relWithDebInfo/Mod -Directory | % FullName) -join ';' + ';' + $env:PATH; ctest --test-dir build/relWithDebInfo -j 16`

## Baseline (upstream @ 82d3fa0, build del 2026-10-07)

| Voce | Valore |
|---|---|
| Configure | 172 s + 30 s di generazione |
| Build completa a freddo (32 thread) | 2890 s (~48 min), 8212 passi, 0 errori |
| ctest (con `Mod/*` nel PATH) | 23/26 superati in 54 s |
| `FreeCADCmd -t 0` | 3558 test in 676 s: OK (38 saltati, 5 fallimenti attesi) |

Test ctest che falliscono già in partenza, tutti per il **locale italiano** (virgola decimale) del PC:
- `Base_tests_run`: `BaseQuantityLoc.psi_parse_user_str`, `BaseQuantityLoc.psi_parse_safe_user_str` (`"6894,76 Pa"` invece di `"6894.76 Pa"`).
- `QuantitySpinBox_Tests_run`: `test_BareValueUsesCurrentMagnitudeDependentDisplayUnit` (`"20,0 m"` invece di `"20.0 m"`).
- `InputField_Tests_run`: stessa causa (stessa famiglia di test; dettaglio non estratto).

Test GUI Python che falliscono già in partenza per la **lingua italiana** dell'interfaccia:
- `FreeCAD -t TestSketcherGui`: 3 test di `TestCoincidentCommandGui` confrontano i messaggi in inglese
  (`'Vincolo coincidente non aggiunto' != 'Coincident constraint not added'`).

## Prossimo passo

M5.2 profilati strutturali (saldature).

## Problemi noti

- (Risolto 2026-10-07) Abort all'uscita nei test GUI: causato dai wrapper PySide creati per i widget
  delle viste MDI (`QMdiArea.activeSubWindow().widget()`) nel timer di contesto; ora si usa
  `Gui.ActiveDocument.ActiveView`. Regola: **non creare wrapper PySide dei widget delle viste** nel codice
  Forge. Verificato 30/30 esecuzioni senza abort.
- (Risolto) Dopo un cambio di workbench `ToolBarManager` riapplicava in differita la visibilità salvata
  delle toolbar, riaccendendo la toolbar di un'altra scheda: il command manager ora tiene allineati i
  parametri `BaseApp/MainWindow/Toolbars`.
- `Surface_Cut` è disabilitato in upstream (`src/Mod/Surface/Gui/Command.cpp`): non è nel catalogo Forge.

## DA VERIFICARE A VIDEO

### M1.1 — Workbench Forge e command manager a schede
1. Avviare `pixi run build/relWithDebInfo/bin/FreeCAD.exe` e scegliere il workbench **Forge** (icona incudine arancione/grigia).
2. Atteso: sotto le toolbar standard, una riga di linguette *Schizzo | Feature | Superfici | Valuta | Assieme | Tavola*
   e sotto una sola toolbar con i comandi della scheda scelta (all'inizio *Feature*).
3. Cliccare ogni linguetta: deve cambiare la toolbar visibile; nessuna delle altre deve restare aperta.
4. Nuovo documento → scheda *Feature* → *Corpo* → scheda *Schizzo* → "Nuovo schizzo" sul piano XY: il
   workbench deve **restare Forge**; sotto le linguette compaiono due toolbar (*Disegno*: linee, archi,
   rettangoli…; *Vincoli*: quota intelligente, coincidente, orizzontale/verticale…). Disegnare un rettangolo,
   quotarlo, poi "Chiudi schizzo": si torna alla scheda di partenza, ancora in Forge.
4b. Da Part Design (non Forge), modificare lo stesso schizzo: deve passare allo Sketcher come in FreeCAD standard.
5. Scheda *Tavola* → *Nuova pagina*: con la pagina attiva la scheda deve passare da sola a *Tavola*;
   tornando alla vista 3D deve ripristinarsi la scheda precedente.
6. Creare un assieme (scheda *Assieme* → *Crea assieme*): con l'assieme attivo la scheda resta *Assieme*.
7. Passare a un altro workbench (es. Part Design): linguette e toolbar Forge devono sparire; tornando a Forge
   deve riapparire l'ultima scheda **scelta a mano**.
8. Menu **Forge**: deve contenere un sottomenu per ogni scheda con gli stessi comandi.
9. Riferire: layout delle righe di toolbar, eventuali comandi con icona mancante, crash.

Parametri (Strumenti → Modifica parametri → `BaseApp/Preferences/Mod/Forge`): `AutoSwitchTabs` (bool,
default vero), `LastTab` (stringa).

### M1.3 — Impostazioni stile SolidWorks
1. Alla prima attivazione di Forge compare la domanda "Applicare le impostazioni in stile SolidWorks?". Rispondere Sì.
2. Verificare: navigazione (tasto centrale ruota, Ctrl+centrale sposta, rotella zoom sul cursore), `F` adatta la vista,
   `Ctrl+1`…`Ctrl+7` viste standard, `Ctrl+8` normale alla faccia selezionata, `Ctrl+B` ricostruisce.
3. Riavviare FreeCAD: deve aprirsi direttamente in Forge.
4. Menu Forge → "Ripristina impostazioni precedenti": tutto torna come prima (navigazione, scorciatoie, workbench di avvio).

### M1.4 — Barra heads-up
1. In Forge, con un documento aperto e la vista 3D attiva: in alto al centro della vista deve comparire una barra
   semitrasparente con: Adatta, Zoom finestra, Orientamento (menu), Stile di visualizzazione (menu), Vista in sezione,
   Nascondi/mostra, Proiezione (menu).
2. Ridimensionare la finestra: la barra resta centrata. Aprire una pagina TechDraw: la barra sparisce; tornando
   alla vista 3D ricompare. Passando a un altro workbench sparisce.
3. Riferire se copre elementi importanti (es. il cubo di navigazione) o se i colori non si leggono col tema scuro.

### M1.5 — Rollback bar
1. Creare un corpo con almeno tre feature (es. Pad, Pocket, Fillet) e renderlo attivo.
2. Accanto alle linguette compare "Rollback [cursore] 3/3 – Fillet". Trascinare il cursore indietro e rilasciare:
   il modello mostra solo le feature fino alla posizione scelta; l'etichetta riporta "k/3 – <feature>".
3. Scheda Feature: i pulsanti con le frecce (indietro, avanti, fine) spostano la posizione di una feature o fino alla fine.
4. Ctrl+Z annulla l'ultimo spostamento del rollback.
5. Senza corpo attivo il cursore non compare.

### M1.6 — Menu radiale
1. Con un documento aperto premere S (dopo aver applicato le impostazioni SolidWorks) oppure menu Forge → Menu radiale.
2. Attorno al cursore compare un anello con 8 comandi: in una parte schizzo/estrusione/tasca/foro/raccordo/smusso/misura/normale a;
   dentro uno schizzo quota, linea, rettangolo, arco, taglia, costruzione, coincidente, chiudi schizzo; in una tavola i comandi TechDraw.
3. Click su un'icona: il menu si chiude ed esegue il comando. Esc, S o click fuori: si chiude senza fare nulla.

### M3.2 — Diagnostica feature
1. In Forge, blocco 20×10×10, raccordo r=6 su tutti gli spigoli: la feature va in errore e nell'area notifiche
   compare "Forge: Fillet: Il raccordo non si può costruire con questo raggio…".
2. Scheda Valuta → Diagnostica feature: finestra con "Il raggio massimo applicabile è circa 4.95 mm" (o simile);
   gli spigoli del raccordo risultano selezionati nella vista.
3. Una tasca con lo schizzo fuori dal pezzo: avviso "La feature non rimuove materiale…".

### M8 — Interferenze e sformo
1. Due cubi sovrapposti (Part → Cubo, spostarne uno di 8 mm in X). Scheda Valuta → Rileva interferenze: finestra
   "Interferenze: 1" con il volume (200 mm³); nel gruppo "Interferenze" un solido rosso nella zona comune.
2. Selezionando due soli oggetti, il controllo riguarda solo quelli. In un assieme attivo, i suoi componenti.
3. Selezionare un corpo (o una sua faccia piana come direzione) → Analisi di sformo: copia colorata (verde, rosso,
   giallo, blu) e originale nascosto. Rieseguire il comando: l'analisi sparisce e l'originale ricompare.

### M2.1 — Diagnosi schizzo
1. Schizzo rettangolo con orizzontali/verticali, quotare la base 20 e poi la linea opposta 25: lo schizzo va in conflitto.
2. Scheda Schizzo (o toolbar Vincoli in modifica) → Diagnosi schizzo: la finestra elenca i vincoli in conflitto e propone
   "Elimina #… Distanza orizzontale 25 mm (Linea 3) → gradi di libertà: …" e simili.
3. "Applica correzione": il conflitto sparisce; Ctrl+Z ripristina il vincolo.

### M2.3 — Blocchi di schizzo
1. In uno schizzo disegnare e vincolare completamente un'asola (o un rettangolo); selezionarne gli spigoli → toolbar
   Disegno → "Salva blocco", nome "asola".
2. In un altro schizzo → "Inserisci blocco" → scegliere "asola": compare nell'origine con forma e vincoli interni;
   trascinandola si sposta rigidamente.

### M2.4 — Schizzo 3D
1. Scheda Schizzo → Schizzo 3D senza selezione: compare un percorso 3D di esempio (3 punti). Nelle proprietà modificare
   Points, Mode (Polilinea/Spline), Closed, BendRadius e verificare l'aggiornamento.
2. Selezionare 3–4 vertici di un solido in ordine e rieseguire il comando: la polilinea li collega nell'ordine scelto.

### M5.1 — Lamiera
1. Scheda Lamiera: schizzo rettangolo → "Flangia base" (SheetMetal_AddBase) con spessore 2; selezionare uno spigolo → "Flangia"
   (AddWall); selezionare la faccia grande → "Sviluppa" (Unfold).
2. Selezionare lo sviluppo → "Tabella di piega": compare un foglio di calcolo con angolo, raggio, K, tolleranza, deduzione.
3. Selezionare lo sviluppo → "Esporta sviluppo DXF": aprire il file in un visualizzatore DXF (contorno + linee di piega).

