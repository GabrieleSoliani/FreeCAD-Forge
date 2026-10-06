# PROGRESS — FreeCAD Forge

Leggere questo file per primo a ogni ripresa. Prompt completo del progetto: `FORGE_PROMPT.md`.

## Stato attuale (2026-10-06)

**Fase 0 — Setup: in corso.**

- [x] Fork su GitHub: https://github.com/GabrieleSoliani/FreeCAD-Forge (remote `origin`; `upstream` = FreeCAD/FreeCAD).
- [x] Branch `forge` creato da upstream `main` @ `82d3fa0` (6 ott 2026).
- [x] `ARCHITECTURE_NOTES.md` scritto.
- [ ] Build locale (Windows 11, PC "PCDellGabriele"): in attesa di MSVC (Build Tools 2022 + workload C++ in installazione) e dell'ambiente pixi (`pixi install` in corso).
- [ ] Baseline: tempi di build e test falliti all'origine.
- [ ] Build cloud (Linux headless) per l'esecuzione non presidiata.

## Ambienti

| Ambiente | Toolchain | Stato |
|---|---|---|
| Windows locale | pixi 0.81 + MSVC 14.44 (Build Tools 2022), `pixi run configure/build/install` | in setup |
| Cloud Linux | pixi (vedi `pixi.toml`), `pixi run configure` → `build` → `test`; GUI test con `xvfb-run` | da creare |

## Prossimo passo

1. Completare la build locale, misurare i tempi, eseguire `ctest` + `FreeCADCmd -t 0`, registrare la baseline qui sotto.
2. Fase 1: scrivere `GAP_ANALYSIS.md` e riordinare le milestone.

## Baseline

(da compilare)

## Problemi noti

- Il primo `pixi install` su Windows non ha scritto nulla nel log pur restando attivo a lungo: controllare `.pixi/envs/default` prima di rilanciarlo.

## DA VERIFICARE A VIDEO

(nessuna voce)
