# CORE_PATCHES — modifiche al codice di FreeCAD fuori da `src/Mod/Forge`

Ogni patch al core è elencata qui con il motivo, per facilitare i merge da upstream.

| File | Modifica | Motivo |
|---|---|---|
| `cMake/FreeCAD_Helpers/InitializeFreeCADBuildOptions.cmake` | `option(BUILD_FORGE ... ON)` | Opzione di build del modulo Forge |
| `cMake/FreeCAD_Helpers/CheckInterModuleDependencies.cmake` | `REQUIRES_MODS(BUILD_FORGE BUILD_PART BUILD_PART_DESIGN BUILD_SKETCHER)` | Forge usa i comandi di Part, PartDesign e Sketcher |
| `cMake/FreeCAD_Helpers/PrintFinalReport.cmake` | `value(BUILD_FORGE)` | Riepilogo di configurazione |
| `src/Mod/CMakeLists.txt` | `add_subdirectory(Forge)` se `BUILD_FORGE` | Inclusione del modulo nella build |
| `.gitignore` | log di build locali | Evita di committare `configure.log`/`build.log` |
