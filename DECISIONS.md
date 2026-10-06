# DECISIONS — FreeCAD Forge

| Data | Decisione | Motivo |
|---|---|---|
| 2026-10-06 | Fork su GitHub `GabrieleSoliani/FreeCAD-Forge`, lavoro sul branch `forge`; `upstream` resta FreeCAD/FreeCAD | Serve un remote proprio per push continui dalle sessioni non presidiate e per il rebase periodico da upstream |
| 2026-10-06 | Toolchain di build: pixi (quella ufficiale del repo) sia su Windows sia su Linux | Un solo flusso `pixi run configure/build/install/test` su entrambe le macchine; dipendenze bloccate da `pixi.lock` |
| 2026-10-06 | Nuovo codice in `src/Mod/Forge`, inizialmente puro Python (modello `src/Mod/Tux`); C++ solo dove necessario; patch al core elencate in `CORE_PATCHES.md` | Mantenere il fork facilmente aggiornabile da upstream |
