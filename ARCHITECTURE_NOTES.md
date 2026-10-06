# ARCHITECTURE_NOTES — FreeCAD Forge

Note sull'architettura di FreeCAD (upstream `main` @ `82d3fa0`, 6 ott 2026) orientate ai punti di
intervento del fork. Percorsi relativi alla radice del repository.

## 0. Sintesi: cosa esiste già e cosa no

Già presente in upstream (da **riusare**, non riscrivere):

| Funzione SolidWorks-like | Dove sta in FreeCAD |
|---|---|
| Navigazione mouse stile SolidWorks | `src/Gui/Navigation/SolidWorksNavigationStyle.cpp` |
| Quota intelligente unica nello schizzo | `Sketcher_Dimension` → `DrawSketchHandlerDimension` in `src/Mod/Sketcher/Gui/CommandConstraints.cpp` |
| Anteprima live delle feature | `Part::PreviewExtension` (`src/Mod/Part/App/PreviewExtension.h`), `PartGui::ViewProviderPreviewExtension`, doc in `src/Mod/Part/previews.dox` |
| Rollback (concetto) | `Body.Tip` (`src/Mod/Part/App/BodyBase.h`) + comando `PartDesign_MoveTip` |
| Tabella configurazioni | Spreadsheet → "Configuration table…" (`src/Mod/Spreadsheet/Gui/DlgSheetConf.cpp`) + `App::Link` `LinkCopyOnChange` |
| Proprietà di massa | `src/Mod/Measure/App/MassPropertiesObject.*`, `Gui/TaskMassProperties.*` |
| Libreria materiali | `src/Mod/Material` (densità usata da `Part::Feature::ShapeMaterial`) |
| Foro con dati ISO | `PartDesign::Hole` (`FeatureHole.cpp`) + JSON in `src/Mod/PartDesign/Resources/Hole/` |
| Pattern da curva/punti | `PathPattern`, `PointPattern` in `src/Mod/PartDesign/App/FeatureTransformed.h` |
| Viste esplose, BOM, simulazione assieme | `src/Mod/Assembly` (Python + `AssemblyObject` C++ su OndselSolver) |
| Verifica geometria | `Part_CheckGeometry` (`src/Mod/Part/Gui/TaskCheckGeometry.h`) |

**Assente** nel core: lamiera, saldature/profilati, command manager a schede (ribbon), menu radiale,
rollback bar nell'albero, analisi di sformo e di spessore, rilevamento interferenze in assieme,
tabella BOM nativa in TechDraw (esiste solo `DrawViewSpreadsheet`).

## 1. Struttura generale

- `src/Base`: tipi di base (Vector3D, Placement, Quantity/Unit, Parameter, Console, PyObjectBase, Persistence).
- `src/App`: modello del documento: `Document`, `DocumentObject`, `GeoFeature`, `FeaturePython`, proprietà
  (`Property*`, `DynamicProperty`), espressioni (`Expression*`, `PropertyExpressionEngine`), `Link`, `VarSet`,
  `Origin`, `GroupExtension`, `SuppressibleExtension`, `MeasureManager`, transazioni.
- `src/Gui`: Qt + Coin3D: `Application`, `MainWindow`, `Command`, `Workbench*`, `Tree`, `TaskView/`,
  `Navigation/`, `Selection/`, `propertyeditor/`, `DAGView/`, `PreferencePacks/`, `OverlayManager`.
- `src/Mod/*`: moduli (Assembly, Part, PartDesign, Sketcher, TechDraw, Spreadsheet, Measure, Material, Fem, …).
- `src/3rdParty`: OndselSolver, coin, pivy, GSL, nlohmann json, FastSignals.

### Struttura di un modulo
- `CMakeLists.txt`: `add_subdirectory(App)`, `if(BUILD_GUI) add_subdirectory(Gui)`, copia degli script Python.
- `Init.py` (headless: tipi di import/export, `FreeCAD.__unit_test__ += [...]`), `InitGui.py` (classe Workbench + `Gui.addWorkbench`).
- C++: libreria `X` (App) e `XGui` (Gui); binding Python generati da stub `.pyi` con `generate_from_py()` + `*PyImp.cpp`.
- Modelli puramente Python: `src/Mod/Tux/CMakeLists.txt` (CMake più pulito), `src/Mod/TemplatePyMod/` (workbench, TaskPanel, FeaturePython; non compilato di default), `src/Mod/OpenSCAD` (workbench Python reale con test).

### Registrazione nella build (le uniche patch al core necessarie per un nuovo modulo)
1. `cMake/FreeCAD_Helpers/InitializeFreeCADBuildOptions.cmake` → `option(BUILD_FORGE ...)`.
2. `cMake/FreeCAD_Helpers/CheckInterModuleDependencies.cmake` → `REQUIRES_MODS(BUILD_FORGE BUILD_PART_DESIGN BUILD_SKETCHER ...)`.
3. `cMake/FreeCAD_Helpers/PrintFinalReport.cmake` → riga di riepilogo.
4. `src/Mod/CMakeLists.txt` → `if(BUILD_FORGE) add_subdirectory(Forge) endif()`.

## 2. Workbench e interfaccia (M1)

- `src/Gui/Workbench.h/.cpp`: `setupMenuBar/ToolBars/CommandBars/DockWindows`, `setupContextMenu`,
  `activated/deactivated`. Python: `PythonWorkbench` (`appendToolbar`, `appendMenu`, `appendContextMenu`).
- **`WorkbenchManipulator`** (`src/Gui/WorkbenchManipulator.h`, `Gui.addWorkbenchManipulator`): permette di
  modificare menu/toolbar/menu contestuali di *qualsiasi* workbench senza toccarne il codice → è il punto
  d'innesto meno invasivo per l'ambiente unificato "Forge".
- Toolbar/menu: `ToolBarManager.cpp`, `MenuManager.cpp`, `ToolBarAreaWidget.h`, `Action.cpp` (gruppi, split button),
  `CommandCompleter`. **Nessun ribbon nel core**: il command manager a schede sarà un widget Qt proprio
  (QTabWidget in un dock/toolbar sopra la vista), installato da Python.
- **Task panel** (pannello proprietà con OK/Annulla): `src/Gui/TaskView/TaskDialog.h` (`accept/reject/clicked`),
  `TaskDialogPython.cpp` (`Gui.Control.showDialog(panel)`), `TaskWatcher.cpp` (pannelli contestuali), `Gui/Control.h`.
- **Albero**: `src/Gui/Tree.cpp` (drag&drop: `TreeWidget::dropMimeData` ~r.2225, logica ~2400–3200), hook nei
  view provider `canDropObjects/canDragObject(s)/dropObjectEx` (`ViewProvider.h`, `ViewProviderDocumentObject`).
  Gruppi: `ViewProviderGroupExtension`. Grafo dipendenze: `src/Gui/DAGView/`.
  **Rollback bar**: non esiste; implementabile pilotando `Body.Tip`. Una barra trascinabile *dentro* l'albero
  richiede quasi certamente una patch a `Tree.cpp` (item speciale) → da documentare in CORE_PATCHES.md.
- **Navigazione**: `src/Gui/Navigation/*` (inclusi SolidWorks, Gesture, SiemensNX), registrazione in `src/Gui/SoFCDB.cpp`.
  Gesture mouse: `GestureNavigationStyle.cpp`. **Menu radiale**: assente (solo addon esterni).
- Preference pack: `src/Gui/PreferencePackManager.cpp`, `src/Gui/PreferencePacks/` → un pack "Forge" può
  impostare navigazione, colori, scorciatoie in un colpo solo.
- Scorciatoie: `src/Gui/ShortcutManager.h`. Altri mattoni utili: `InputHint*` (barra suggerimenti),
  `ToolHandler.cpp`, `EditableDatumLabel` (input numerico nella vista → base per drag handles "Instant3D"),
  `QuantitySpinBox`, `ExpressionBinding`.

## 3. PartDesign (M3, M4)

- `Body` (`src/Mod/PartDesign/App/Body.h`, base `Part::BodyBase`): `Tip`, `addObject` (inserisce dopo il Tip),
  `insertObject`, `getPrev/NextSolidFeature`. Riordino: `PartDesign_MoveFeature`.
- `PartDesign::Feature : Part::Feature, Part::PreviewExtension` (`Feature.h`): `BaseFeature`, `getBaseTopoShape`.
  Gerarchia: `FeatureAddSub` → `FeatureSketchBased` → `FeatureExtrude` (Pad/Pocket), `FeatureRevolved`,
  `FeatureBoolean`, `FeaturePrimitive`, `FeatureRefine`.
- Dress-up (`FeatureDressUp.h`): Fillet, Chamfer, Draft, Thickness; `FeatureDefeaturing`.
- Pattern (`FeatureTransformed.h`): Mirrored, Linear, Polar, Circular, PathPattern, PointPattern, Scaled, MultiTransform.
- Foro: `FeatureHole.cpp` (filettature ISO grosso/fine, UNC/UNF/UNEF, NPT, BSP, BSW, BSF; svasature/lamature
  da JSON in `Resources/Hole/`); GUI `Gui/TaskHoleParameters.*`.
- **Errori**: `execute()` restituisce `App::DocumentObjectExecReturn(msg)` (`src/App/DocumentObject.h`);
  visualizzati come overlay nell'albero + Report view + `Gui/Notifications.h`. Per M3 il punto di intervento è
  qui: arricchire i messaggi e associare la sotto-geometria problematica.

## 4. Sketcher (M2)

- `SketchObject` (`src/Mod/Sketcher/App/SketchObject*.cpp`): diagnosi `hasConflicts()`, `getLastConflicting()`,
  `getLastRedundant()`, `getLastPartiallyRedundant()`, `getLastMalformedConstraints()`, `signalSolverUpdate`.
- Solutore: `App/planegcs/` (GCS). Analisi: `SketchAnalysis.cpp`.
- Strumenti di disegno: `DrawSketchHandler.h` (`seekAutoConstraint`, `createAutoConstraints`), framework
  `DrawSketchDefaultHandler/ControllableHandler/Controller` (parametri nella vista).
- Inferenze: `AutoConstraint.h`, `SnapManager.h`. Messaggi conflitti: `TaskSketcherMessages.cpp`, `TaskSketcherConstraints.cpp`.

## 5. Assembly (M6)

- C++: `src/Mod/Assembly/App/AssemblyObject.cpp` (OndselSolver: `solve`, `preDrag/doDragStep`, `generateSimulation`,
  `exportAsASMT`), `BomObject`, gruppi (Joint/View/Simulation/Snapshot/Bom). GUI: `ViewProviderAssembly.cpp` (trascinamento).
- Python: `JointObject.py` — giunti Fixed, Revolute, Cylindrical, Slider, Ball, Distance, Parallel, Perpendicular,
  Angle, RackPinion, Screw, Gears, Belt. Comandi `CommandCreate*.py`, `CommandInsertLink.py`.
- **Mancano**: interferenze/giochi, larghezza, camma, slot, limiti generalizzati, smart mates, pattern/specchia componenti.

## 6. TechDraw (M7)

- Viste: `DrawViewPart`, `DrawProjGroup(Item)`, `DrawViewSection`, `DrawComplexSection`, `DrawViewDetail`, `DrawBrokenView`.
- Quote: `DrawViewDimension`, `DrawDimHelper`, `LandmarkDimension`; GUI `CommandCreateDims.cpp`, `CommandExtensionDims.cpp`.
- Palloncini: `DrawViewBalloon`. BOM: solo `DrawViewSpreadsheet`. Template SVG: `Templates/` (ISO/ASME), riempimento campi `TechDrawTools/CommandFillTemplateFields.py`.
- Export: `exportPageAsPdf/Svg`, `writeDXFPage` (`App/AppTechDrawPy.cpp`, `App/TechDrawExport.cpp`).

## 7. Part

- `TopoShape` + `TopoShapeExpansion.cpp` (`makeElementBoolean/Fuse/Cut/Fillet/Chamfer/ThickSolid` con naming topologico).
- Booleane: `FCBRepAlgoAPI_BooleanOperation.cpp`, `BOPTools/`. Raccordi: `makeElementFillet`, `FeatureFillet.cpp`.
- Feature Python: `Part::FeaturePython` (`PartFeature.h`) — sarà la base di quasi tutte le nuove feature Forge
  (lamiera, profilati) in prima battuta.
- `Gui/SectionCutting.cpp` (sezioni), `MeasureClient.cpp`.

## 8. Espressioni, variabili, configurazioni (M4)

- Espressioni: `src/App/Expression*.cpp`, `ObjectIdentifier`, `PropertyExpressionEngine`; GUI `ExpressionBinding`, `ExpressionCompleter`.
- Variabili globali: `App::VarSet` (`src/App/VarSet.h`). Spreadsheet: `src/Mod/Spreadsheet/App/Sheet.cpp`.
- Configurazioni: la "Configuration table" dello Spreadsheet crea una `PropertyEnumeration` e lega le celle via
  espressione; manca la **soppressione per configurazione** e un oggetto configurazione nativo → M4.

## 9. Test

- C++ (GoogleTest): `tests/` (`tests/src/{Base,App,Gui,Mod}`), attivati da `ENABLE_DEVELOPER_TESTS`, eseguiti da `ctest`.
  Esempio: `tests/src/Mod/PartDesign/CMakeLists.txt`.
- Python: ogni modulo aggiunge i propri test a `FreeCAD.__unit_test__`; runner `src/Mod/Test/TestApp.py`;
  CLI `FreeCADCmd -t 0` (tutti) o `-t <Modulo>`. **Non** registrati in ctest: la baseline va presa con entrambi.
- Forge: test Python in `src/Mod/Forge/ForgeTests/`, registrati via `Init.py`; test C++ (se servono) in `tests/src/Mod/Forge/`.

## 10. Piano d'innesto del modulo Forge

```
src/Mod/Forge/
  CMakeLists.txt        # modello: Tux (solo Python) all'inizio; App/Gui C++ solo se necessario
  Init.py               # registrazione test, import
  InitGui.py            # ForgeWorkbench + WorkbenchManipulator
  forge/ui/             # command manager a schede, heads-up bar, menu radiale, rollback
  forge/features/       # nuove feature (Part::FeaturePython + PreviewExtension)
  forge/sheetmetal/  forge/weldments/  forge/evaluate/  forge/drawing/
  ForgeTests/
forge_examples/         # modelli di riferimento per milestone
```

Regola: tutto nuovo codice in `src/Mod/Forge`; le patch al core (registrazione build, Tree.cpp per la rollback bar,
eventuali hook) si elencano in `CORE_PATCHES.md`.
