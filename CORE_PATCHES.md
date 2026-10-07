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
| `src/Mod/PartDesign/App/FeatureFillet.cpp`, `FeatureChamfer.cpp` | Se il risultato resta non valido dopo `LimitTolerance`, la feature va in errore con un messaggio chiaro | M3: prima veniva accettato un solido non valido (es. volume negativo con raggio troppo grande) e le feature successive ci costruivano sopra. Suite upstream `TestPartDesignApp` (239 test) invariata |
| `src/Mod/PartDesign/App/FeatureThickness.cpp` | Errore se il guscio è non valido o se non cambia il volume del solido | M3: con parete troppo spessa OCC restituiva un solido non valido o il solido originale, accettati in silenzio |
| `src/Mod/PartDesign/App/FeatureDraft.cpp` | Messaggio esplicito quando OCC fallisce senza messaggio | M3: la feature andava in errore con testo vuoto |
| `cMake/FreeCAD_Helpers/*.cmake`, `src/Mod/CMakeLists.txt` | Opzione `BUILD_SHEETMETAL` e `add_subdirectory(SheetMetal)` | M5: addon SheetMetal integrato come modulo (vedi `THIRD_PARTY.md`) |
| `README.md` → `README.FreeCAD.md` | Il README originale di FreeCAD è stato rinominato; `README.md` descrive Forge in italiano | Consegna. In caso di conflitto al merge, applicare le modifiche upstream a `README.FreeCAD.md` |
