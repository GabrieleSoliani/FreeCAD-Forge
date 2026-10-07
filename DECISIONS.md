# DECISIONS — FreeCAD Forge

| Data | Decisione | Motivo |
|---|---|---|
| 2026-10-06 | Fork su GitHub `GabrieleSoliani/FreeCAD-Forge`, lavoro sul branch `forge`; `upstream` resta FreeCAD/FreeCAD | Serve un remote proprio per push continui dalle sessioni non presidiate e per il rebase periodico da upstream |
| 2026-10-06 | Toolchain di build: pixi (quella ufficiale del repo) sia su Windows sia su Linux | Un solo flusso `pixi run configure/build/install/test` su entrambe le macchine; dipendenze bloccate da `pixi.lock` |
| 2026-10-06 | Nuovo codice in `src/Mod/Forge`, inizialmente puro Python (modello `src/Mod/Tux`); C++ solo dove necessario; patch al core elencate in `CORE_PATCHES.md` | Mantenere il fork facilmente aggiornabile da upstream |
| 2026-10-07 | Niente build/esecuzione cloud: si lavora solo sulla macchina Windows locale | Richiesta esplicita dell'utente. Le regole "Esecuzione non presidiata" restano valide dove applicabili (build in background con log, commit+push a ogni task); i test GUI si eseguono localmente invece che con xvfb-run |
| 2026-10-07 | Ordine milestone: M1 → M3 → M8 parziale (interferenze, sformo) → M2 → M5 → M6 → M7 → M4 → M8 resto | Derivato da `GAP_ANALYSIS.md`: impatto quotidiano / sforzo, con la UI come fondamenta |
| 2026-10-07 | Le schede del command manager sono toolbar standard di FreeCAD ("Forge <Scheda>"), mostrate una alla volta da una QTabBar in una QToolBar propria | Riusa creazione delle azioni, menu a tendina dei comandi di gruppo e personalizzazione del core; nessuna patch al core |
| 2026-10-07 | Cambio scheda automatico solo al cambio di contesto, con ritorno alla scheda precedente all'uscita; si memorizza solo la scheda scelta a mano | Comportamento di SolidWorks; evita di "rubare" la scheda all'utente |
| 2026-10-07 | Contesto letto con un QTimer a 300 ms mentre Forge è attivo | Non esiste un segnale Python unico per cambio vista MDI / modifica / oggetto attivo; costo trascurabile |
| 2026-10-07 | Pacchetto Python `forgelib` (non `forge`) | Evita ambiguità con la cartella `Mod/Forge` su file system case-insensitive |
| 2026-10-07 | M1.1 non cambia il passaggio allo Sketcher durante la modifica di uno schizzo | Richiede una patch al core: rimandata a M1.2 come task separato |
| 2026-10-07 | Modifica dello schizzo in Forge: patch al core basata su un attributo generico del workbench (`HandlesSketchEditing`) invece di un nome cablato | Patch di una riga, neutra per gli altri workbench, riutilizzabile da altri ambienti |
| 2026-10-07 | In modifica schizzo la scheda Schizzo mostra due toolbar Forge proprie ("Disegno", "Vincoli") invece di riusare i nomi delle toolbar dello Sketcher | Le toolbar dello Sketcher hanno visibilità "Unavailable" non impostabile da un workbench Python; con nomi propri la visibilità resta tutta sotto il controllo del command manager |
| 2026-10-07 | Impostazioni SolidWorks applicate da Python con backup JSON invece che come preference pack | Nessuna API Python per i pack e i pack nei Mod di sistema non vengono cercati; così si possono annullare con precisione (testato) |
| 2026-10-07 | Scorciatoie: Ctrl+1..8 sostituiscono quelle di FreeCAD (1..6, 0) per le viste; F per adatta; Ctrl+B ricostruisci | Sono le predefinite di SolidWorks; quelle precedenti si recuperano con "Ripristina" |
