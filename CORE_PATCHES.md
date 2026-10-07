# CORE_PATCHES — modifiche al codice di FreeCAD fuori da `src/Mod/Forge`

Ogni patch al core è elencata qui con il motivo, per facilitare i merge da upstream.

| File | Modifica | Motivo |
|---|---|---|
| `cMake/FreeCAD_Helpers/InitializeFreeCADBuildOptions.cmake` | `option(BUILD_FORGE ... ON)` | Opzione di build del modulo Forge |
| `cMake/FreeCAD_Helpers/CheckInterModuleDependencies.cmake` | `REQUIRES_MODS(BUILD_FORGE BUILD_PART BUILD_PART_DESIGN BUILD_SKETCHER)` | Forge usa i comandi di Part, PartDesign e Sketcher |
| `cMake/FreeCAD_Helpers/PrintFinalReport.cmake` | `value(BUILD_FORGE)` | Riepilogo di configurazione |
| `src/Mod/CMakeLists.txt` | `add_subdirectory(Forge)` se `BUILD_FORGE` | Inclusione del modulo nella build |
| `.gitignore` | log di build locali | Evita di committare `configure.log`/`build.log` |
| `src/Mod/Sketcher/Gui/ViewProviderSketch.cpp` (script di "visibility automation" in `setEdit`) | Non chiama `tv.activateWorkbench(EditingWorkbench)` se il workbench attivo ha l'attributo `HandlesSketchEditing = True` | M1.2: modificare uno schizzo restando nell'ambiente Forge. Senza l'attributo il comportamento è identico a upstream (verificato da `TestForgeGui.test_sketch_edit_outside_forge_unchanged`) |
