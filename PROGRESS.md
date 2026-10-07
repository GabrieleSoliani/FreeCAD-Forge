# PROGRESS — FreeCAD Forge

Leggere questo file per primo a ogni ripresa. Prompt completo del progetto: `FORGE_PROMPT.md`.
Si lavora **solo in locale** sul PC Windows (niente cloud, vedi `DECISIONS.md` 2026-10-07).

## Stato attuale (2026-10-07)

- **Fase 0 — Setup: completata.** Build locale funzionante, baseline dei test registrata.
- **Fase 1 — Analisi del divario: completata.** `GAP_ANALYSIS.md`; ordine milestone in `DECISIONS.md`.
- **M1 — Interfaccia unificata: in corso.**
  - [x] M1.1 Modulo `src/Mod/Forge` (solo Python) registrato nella build; workbench "Forge" con command
        manager a schede (Schizzo, Feature, Superfici, Valuta, Assieme, Tavola) e cambio scheda
        automatico in base al contesto (tavola attiva, schizzo in modifica, assieme attivo).
  - [x] M1.2 Modifica dello schizzo restando in Forge (patch in `ViewProviderSketch`, vedi
        `CORE_PATCHES.md`); in modifica la scheda Schizzo mostra le toolbar "Disegno" e "Vincoli".
  - [ ] M1.3 Preference pack "Forge" (navigazione SolidWorks, scorciatoie, colori).
  - [ ] M1.4 Barra heads-up nella vista.
  - [ ] M1.5 Rollback bar nell'albero (pilotando `Body.Tip`), cartelle, riordino con controllo dipendenze.
  - [ ] M1.6 Menu radiale contestuale / mouse gestures.

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

M1.3: preference pack "Forge" (navigazione SolidWorks, scorciatoie stile SolidWorks, colori).

## Problemi noti

- **Abort intermittente nei test GUI di Forge**: `FreeCAD.exe -t ForgeTests.TestForgeGui` termina circa
  1 volta su 10–15 con `Abnormal program termination... Break signal occurred` (SIGABRT) e senza output
  su stdout. Con lo stesso binario `-t TestPartDesignGui` di upstream: 0 su 15. Con `faulthandler` o con
  marcatori su file il problema non si è riprodotto (0/30): dipende dai tempi. Ipotesi da verificare:
  distruzione degli oggetti PySide (QToolBar/QTimer del command manager) all'uscita, oppure import dei
  comandi Assembly/TechDrawTools fuori dal loro workbench. Quando si ripresenta nell'uso reale, annotare qui
  in che momento.
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
