# GAP_ANALYSIS — FreeCAD Forge vs SolidWorks

Base di confronto: FreeCAD upstream `main` @ `82d3fa0` (6 ott 2026, serie 1.1/1.2-dev) contro SolidWorks
(funzioni standard di Premium, escluse Simulation/Flow avanzate). Valutazione orientata all'**uso quotidiano**
di un utente singolo che modella parti meccaniche, assiemi e tavole.

Legenda
- **Stato**: ✅ presente · 🟡 parziale · ❌ assente · 🧩 solo addon (Addon Manager)
- **Gravità** del divario per l'uso quotidiano: **A** alta · **M** media · **B** bassa
- **Sforzo** stimato nel fork: **S** ≤ 1 settimana · **M** 1–4 settimane · **L** > 1 mese · **XL** progetto a sé

## 1. Schizzo

| Funzione SolidWorks | FreeCAD | Gravità | Sforzo | Note / punto d'intervento |
|---|---|---|---|---|
| Linee, archi, cerchi, spline, slot, poligoni, rettangoli | ✅ | — | — | `Sketcher/Gui/CommandCreateGeo.cpp` |
| Quota intelligente unica | ✅ | B | S | `Sketcher_Dimension`; manca qualche caso (quota tra arco e linea "max/min") |
| Inferenze durante il disegno | 🟡 | M | M | Auto-vincoli presenti (`AutoConstraint.h`, `SnapManager`), mancano linee d'inferenza tratteggiate verso punti notevoli e allineamenti a distanza |
| Colori di stato (sotto/completamente vincolato, conflitti) | ✅ | — | — | |
| Diagnosi conflitti con proposta di soluzione (SketchXpert) | 🟡 | **A** | M | Elenco conflitti/ridondanti c'è (`getLastConflicting`), manca la proposta "elimina uno di questi" con anteprima |
| Trascinamento fluido di geometrie sottovincolate | 🟡 | M | M | Funziona ma salta / inverte archi; solutore `planegcs` |
| Offset, trim, extend, split, fillet/chamfer di schizzo | ✅ | — | — | |
| Specchia / pattern lineare e circolare in schizzo | ✅ | — | — | `Sketcher_Symmetry`, `Sketcher_RectangularArray`, `Sketcher_Rotate` |
| Converti entità / interseca | ✅ | — | — | Geometria esterna + "intersezione" |
| Testo nello schizzo | ✅ | — | — | `Sketcher_CreateText` (nuovo in upstream) |
| Blocchi di schizzo | 🟡 | M | M | Esiste solo il vincolo "Block" (blocca), non i blocchi riutilizzabili |
| Schizzo 3D | ❌ | M | L | Nessun equivalente; surrogato: Part Wire/Draft BSpline |
| Equazioni/variabili nelle quote | ✅ | — | — | Espressioni ovunque |
| Immagine di schizzo / tracciatura | ✅ | — | — | Image workbench |

## 2. Feature di parte

| Funzione | FreeCAD | Gravità | Sforzo | Note |
|---|---|---|---|---|
| Estrusione / taglio con condizioni finali (fino a superficie, offset, fino al prossimo) | ✅ | — | — | Pad/Pocket |
| Rivoluzione, sweep, loft, elica | ✅ | — | — | Revolution/Groove, Pipe, Loft, Helix |
| Raccordi costanti | ✅ | **A** | L | Robustezza bassa: fallimenti frequenti con catene tangenti e vertici a 3+ spigoli (OCC) → M3 |
| Raccordi variabili / a faccia / a set di raccordi | ❌ | M | L | Solo raggio costante (o variabile lineare in Part) |
| Smussi distanza-distanza, distanza-angolo | ✅ | — | — | |
| Svuotamento (shell) | 🟡 | **A** | L | `PartDesign::Thickness`: spesso fallisce su raccordi; nessun messaggio utile → M3 |
| Sformo | ✅ | M | M | Funziona, ma mancano analisi di sformo e linea di divisione |
| Foro guidato (Hole Wizard) | 🟡 | M | M | ISO/UNC/... presenti; manca libreria UNI di lamature, foro "a gradino" multi-sezione, filettatura cosmetica in tavola |
| Filettatura cosmetica | 🟡 | M | M | Solo dati sul foro; nessuna rappresentazione in vista/tavola |
| Filettatura modellata | 🟡 | B | S | Elica + sweep manuale |
| Pattern lineare/circolare/specchio | ✅ | — | — | Più lenti di SW su molti istanze |
| Pattern da curva, da schizzo/punti | ✅ | — | — | `PathPattern`, `PointPattern` |
| Pattern da tabella / con varianti | ❌ | B | M | |
| Costola (rib) | ✅ Forge | — | — | Nervatura da profilo aperto (M4.2) |
| Scritte in rilievo/incise su superficie | 🟡 | M | M | ShapeString + Pad (piano); manca avvolgi su superficie curva |
| Avvolgi (wrap) / deforma / flessione | ❌ | B | L | |
| Instant3D (trascina quote nella vista) | ❌ | M | M | Mattone: `EditableDatumLabel` |
| Rollback bar | 🟡 | **A** | M | Concetto = `Body.Tip`; manca la barra trascinabile nell'albero → M1 |
| Riordino con controllo dipendenze | 🟡 | M | S | `PartDesign_MoveFeature` / drag nel tree con regole limitate |
| Soppressione feature | ✅ | — | — | `SuppressibleExtension` |
| Messaggi d'errore comprensibili | ❌ | **A** | M | Messaggi OCC grezzi ("BRep_API: command not done") → M3 |

## 3. Multi-corpo

| Funzione | FreeCAD | Gravità | Sforzo | Note |
|---|---|---|---|---|
| Più corpi in una parte | ✅ | — | — | Più `Body` in un documento/Part |
| Booleane tra corpi | ✅ | — | — | `PartDesign::Boolean` |
| Cartella "corpi solidi" e "unisci risultato" sì/no per feature | 🟡 | M | M | Nessun flag "merge result" per singola feature |
| Dividi (split) / salva corpi come parti | 🟡 | B | M | Part SplitShape; nessun "salva corpi" con link |

## 4. Superfici

| Funzione | FreeCAD | Gravità | Sforzo | Note |
|---|---|---|---|---|
| Estrusa/rivoluzione/sweep/loft di superficie | ✅ | — | — | Part workbench (non in PartDesign) |
| Riempimento (fill), boundary | ✅ | — | — | Surface WB: Filling, GeomFillSurface, Sections |
| Offset, estendi, rifila, cuci (knit) | 🟡 | M | M | Offset/Extend/Sewing/Cut ok; trim "reciproco" scomodo |
| Ispessisci superficie → solido | 🟡 | M | S | Part Thickness/Offset, non integrato nel flusso Body |
| Analisi di curvatura / zebra | ❌ | B | M | |

## 5. Lamiera

| Funzione | FreeCAD | Gravità | Sforzo | Note |
|---|---|---|---|---|
| Flangia base, flangia su bordo, piega, scarico, sviluppo, DXF | ✅ Forge | — | — | Addon SheetMetal (LGPL) integrato in `src/Mod/SheetMetal` + scheda Lamiera (M5.1) |
| Tabella di piega / fattore K | ✅ Forge | — | — | Comando "Tabella di piega" (M5.1) |
| Flangia a raccordo (miter), formatura, angolo chiuso | 🧩/❌ | M | L | |

## 6. Saldature / profilati

| Funzione | FreeCAD | Gravità | Sforzo | Note |
|---|---|---|---|---|
| Profilati strutturali da schizzo 3D | ✅ Forge (ridotto) | — | — | Libreria EN, mitra, schizzo 3D (M2.4, M5.2); mancano giunzioni a T e UPN |
| Rifilatura/estensione, cut list | 🟡 Forge | M | M | Distinta di taglio sì (M5.2); rifilatura contro altri membri no |

## 7. Assiemi

| Funzione | FreeCAD | Gravità | Sforzo | Note |
|---|---|---|---|---|
| Inserimento componenti, fisso/flottante | ✅ | — | — | Assembly integrato (OndselSolver) |
| Accoppiamenti standard (coincidente, concentrico, parallelo, distanza, angolo) | ✅ | — | — | `JointObject.py` |
| Meccanici (ingranaggio, cremagliera, vite, cinghia) | ✅ | — | — | |
| Larghezza, slot, camma, limiti generalizzati | ❌ | M | M | Limiti solo su alcuni giunti |
| Smart mates (trascina con Alt) | ❌ | M | M | |
| Rilevamento interferenze / giochi | ✅ Forge | — | — | Comando "Rileva interferenze" (M8) |
| Viste esplose | ✅ | — | — | Animazione limitata |
| BOM assieme | ✅ | — | — | `BomObject` |
| Pattern / specchia componenti | ✅ Forge | — | — | Serie lineare/circolare parametrica e specchiatura (M6.2) |
| Componenti flessibili (sottoassiemi) | 🟡 | M | M | |
| Modifica in contesto / riferimenti esterni | 🟡 | M | L | Possibile ma fragile |
| Toolbox viteria | ✅ Forge (ridotto) | B | M | ISO 4762/4017/4032/7089 M3–M20 con posizionamento sul foro (M6.1); niente filettatura modellata |

## 8. Messa in tavola

| Funzione | FreeCAD | Gravità | Sforzo | Note |
|---|---|---|---|---|
| Viste standard, gruppo di proiezione, sezioni, dettagli, interrotte | ✅ | — | — | TechDraw |
| Palette delle viste / viste automatiche | ✅ Forge | B | S | Viste automatiche con scala unificata (M7); niente palette trascinabile |
| Importa quote di modello | ❌ | M | L | |
| Quotatura automatica (ordinata, da riferimento) | 🟡 | M | M | Estensioni TechDraw (catene/coordinate) manuali |
| BOM collegata in tavola + palloncini automatici | ✅ Forge | — | — | "Tavola automatica" (M7) |
| Tabella fori | ❌ | B | M | |
| Cartiglio con proprietà personalizzate | ✅ Forge | — | — | Compilato automaticamente (M7) |
| Export PDF/DXF | ✅ | — | — | DWG solo con convertitore esterno (ODA) |

## 9. Configurazioni / equazioni

| Funzione | FreeCAD | Gravità | Sforzo | Note |
|---|---|---|---|---|
| Variabili globali ed equazioni | ✅ Forge | — | — | Gestore unico "Equazioni" (M4.3) |
| Configurazioni con parametri | 🟡 | M | M | "Configuration table" dello Spreadsheet |
| Soppressione per configurazione | ✅ Forge | — | — | Configurazioni (M4.1) |
| Tabella dati (design table) | ✅ Forge | — | — | Importazione da foglio di calcolo (M4.1) |

## 10. Valutazione

| Funzione | FreeCAD | Gravità | Sforzo | Note |
|---|---|---|---|---|
| Misura (distanza, angolo, area, raggio) | ✅ | — | — | Measure workbench |
| Proprietà di massa con materiale | ✅ | — | — | `MassPropertiesObject` |
| Interferenze (parte/assieme) | ✅ Forge | — | — | M8 |
| Analisi di sformo | ✅ Forge | — | — | M8 |
| Analisi di spessore | ✅ Forge | — | — | M8 |
| Sezione dinamica | ✅ | — | — | `SectionCutting`, clipping plane |
| Verifica geometria | ✅ | — | — | `Part_CheckGeometry` |
| Confronto versioni | ✅ Forge | — | — | M8 (geometrico) |

## 11. Libreria di parti standard

| Funzione | FreeCAD | Gravità | Sforzo | Note |
|---|---|---|---|---|
| Viteria/cuscinetti/profili standard | 🧩 | M | M | Addon Fasteners, Parts Library |
| Design library personale (drag & drop) | 🟡 Forge | B | S | Aggiungi/inserisci da menu (M8); niente trascinamento |

## 12. Rendering / aspetti

| Funzione | FreeCAD | Gravità | Sforzo | Note |
|---|---|---|---|---|
| Aspetti per faccia/corpo, materiali | ✅ | B | — | Material + appearance |
| Rendering fotorealistico | 🧩 | B | M | Addon Render (POV/Cycles/LuxCore) |

## 13. Simulazione base

| Funzione | FreeCAD | Gravità | Sforzo | Note |
|---|---|---|---|---|
| Statica lineare (SimulationXpress) | ✅ | B | S | FEM + CalculiX: completo ma con flusso lungo; wizard guidato utile ma non prioritario |
| Moto di assieme | 🟡 | B | — | Simulazione Assembly |

## 14. Interoperabilità

| Formato | FreeCAD | Gravità | Note |
|---|---|---|---|
| STEP/IGES/STL/OBJ/glTF/3MF/DXF | ✅ | — | STEP con colori e struttura d'assieme |
| DWG | 🟡 | B | Solo con ODA File Converter esterno |
| Parasolid/SLDPRT | ❌ | — | Escluso per vincolo di progetto |

## 15. Interfaccia ed ergonomia

| Funzione | FreeCAD | Gravità | Sforzo | Note |
|---|---|---|---|---|
| Ambiente unico senza cambio workbench | ❌ | **A** | M | Il cambio Part/PartDesign/Sketcher/Assembly/TechDraw è la prima fonte di attrito → M1 (`WorkbenchManipulator`) |
| Command manager a schede contestuali | ❌ | **A** | M | Widget Qt proprio |
| Albero feature con rollback bar, cartelle | 🟡 | **A** | M | Patch a `Tree.cpp` probabile |
| Pannello proprietà con anteprima e OK/Annulla | ✅ | — | — | Task panel + `PreviewExtension` |
| Navigazione SolidWorks | ✅ | — | — | `SolidWorksNavigationStyle` |
| Scorciatoie configurabili | ✅ | — | — | Preference pack Forge per impostarle in blocco |
| Menu radiale / mouse gestures | ❌/🧩 | M | M | Addon "Pie Menu" |
| Barra heads-up nella vista | 🟡 | M | S | Navigation cube + overlay; manca barra viste/sezione/stile |
| Menu contestuale nella vista (quote/feature/schizzo) | 🟡 | M | S | |
| Autosalvataggio con ripristino | ✅ | — | — | Recovery file già presenti |
| Pack and Go | ✅ Forge (ridotto) | B | S | Dipendenze nella cartella del documento (M8) |

## Riepilogo: divari ad alta gravità

1. Ambiente unico + command manager a schede (UI) — sforzo M
2. Rollback bar e albero feature più capace — sforzo M
3. Messaggi d'errore comprensibili sulle feature — sforzo M
4. Robustezza raccordi/svuotamenti — sforzo L (limitata da OCC: migliorabile con strategie di ripiego, non risolvibile del tutto)
5. Lamiera — sforzo L (ridotto integrando l'addon SheetMetal)
6. Interferenze in assieme — sforzo S
7. BOM collegata in tavola + palloncini automatici — sforzo M
8. Diagnosi conflitti di schizzo con soluzioni proposte — sforzo M

## Ordine delle milestone rivisto

Criterio: impatto sull'uso quotidiano / sforzo, con le fondamenta (UI) prima perché tutto il resto si aggancia lì.

| Ordine | Milestone | Motivo |
|---|---|---|
| 1 | **M1 — Interfaccia unificata** (prima parte: ambiente Forge, schede, preference pack, heads-up; la rollback bar in seconda battuta) | Tocca ogni sessione di lavoro; è il contenitore di tutte le funzioni successive |
| 2 | **M3 — Robustezza ed errori** (iniziando dai messaggi d'errore) | Alta gravità, misurabile con suite di modelli "difficili" |
| 3 | **M8 (parziale) — Interferenze, analisi di sformo** | Sforzo S/M con alto impatto; anticipate dalla M8 |
| 4 | **M2 — Schizzo** (diagnosi conflitti, inferenze) | Lo schizzo funziona già: si migliorano gli spigoli |
| 5 | **M5 — Lamiera** (integrazione addon) e profilati | Divario A, ma relativo a un sottoinsieme di lavori |
| 6 | **M6 — Assiemi** (resto) | Base già solida in upstream |
| 7 | **M7 — Tavola** | BOM+palloncini prioritari |
| 8 | **M4 — Feature mancanti / configurazioni** | Molte funzioni già presenti; restano rifiniture |
| 9 | **M8 — Resto della valutazione/produttività** | |

Questo ordine è registrato in `DECISIONS.md` ed è rivedibile alla fine di ogni milestone.
