# THIRD_PARTY — codice di terze parti integrato in Forge

| Componente | Licenza | Origine | Versione | Dove | Modifiche |
|---|---|---|---|---|---|
| SheetMetal Workbench (shaise e contributori, Ondsel) | LGPL 2.1 | https://github.com/shaise/FreeCAD_SheetMetal | 0.8.24, commit `a1cf212d8b86b3849e5cc12070226d5d4bded2a3` (30 set 2026) | `src/Mod/SheetMetal` | Nessuna ai file dell'addon; aggiunto solo `CMakeLists.txt` per la build. Rimossi `.vscode`, `.github`, file `.pyc` |

## Aggiornare SheetMetal

1. `git clone https://github.com/shaise/FreeCAD_SheetMetal` in una cartella temporanea.
2. Copiare tutto tranne `.git`, `.github`, `.vscode` sopra `src/Mod/SheetMetal`, mantenendo il nostro `CMakeLists.txt`.
3. Aggiornare commit e versione in questa tabella; eseguire `FreeCADCmd -t ForgeTests.TestForgeSheetMetal`.

Nota: il nuovo algoritmo di sviluppo dell'addon richiede il pacchetto Python `networkx`, non presente
nell'ambiente pixi; l'addon usa automaticamente l'algoritmo V1, verificato dai test Forge.
