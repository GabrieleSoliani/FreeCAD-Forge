# SPDX-License-Identifier: LGPL-2.1-or-later
"""Catalogo delle schede del command manager di Forge.

Ogni scheda corrisponde a una toolbar standard di FreeCAD: in questo modo si riusano la
creazione delle azioni, i menu a tendina dei comandi di gruppo e la personalizzazione delle
toolbar del core. Questo modulo contiene solo dati e funzioni pure, quindi è testabile senza GUI.
"""

from dataclasses import dataclass

SEPARATOR = "Separator"

# Moduli GUI da importare perché i comandi del catalogo risultino registrati.
# Ogni voce è (nome del modulo, obbligatorio). I moduli facoltativi possono mancare se
# il modulo corrispondente è stato escluso dalla build.
GUI_MODULES = (
    ("PartGui", True),
    ("SketcherGui", True),
    ("PartDesignGui", True),
    ("MeasureGui", False),
    ("SurfaceGui", False),
    ("TechDrawGui", False),
    ("AssemblyGui", False),
)

# Moduli Python che registrano comandi (gli stessi importati dai rispettivi workbench).
PYTHON_COMMAND_MODULES = (
    "CommandCreateAssembly",
    "CommandInsertLink",
    "CommandInsertNewPart",
    "CommandCreateJoint",
    "CommandSolveAssembly",
    "CommandExportASMT",
    "CommandCreateView",
    "CommandCreateSimulation",
    "CommandCreateSnapshot",
    "CommandCreateBom",
    "TechDrawTools",
    # addon SheetMetal integrato (src/Mod/SheetMetal)
    "ExtrudedCutout",
    "SheetMetalBaseCmd",
    "SheetMetalBaseShapeCmd",
    "SheetMetalBend",
    "SheetMetalCmd",
    "SheetMetalHem",
    "SheetMetalCornerReliefCmd",
    "SheetMetalExtendCmd",
    "SheetMetalFoldCmd",
    "SheetMetalFormingCmd",
    "SheetMetalJunction",
    "SheetMetalRelief",
    "SheetMetalUnfoldCmd",
    "SketchOnSheetMetalCmd",
    "SheetMetalSketch",
    "SheetMetalFromSolid",
)


@dataclass(frozen=True)
class Tab:
    """Una scheda del command manager."""

    key: str  # identificatore stabile, usato nei parametri e nei test
    label: str  # testo mostrato sulla linguetta
    commands: tuple  # nomi dei comandi FreeCAD, con SEPARATOR tra i gruppi
    # Toolbar mostrate al posto di ``commands`` mentre uno schizzo è in modifica:
    # tuple di coppie (etichetta, comandi). Vuota per le schede senza modalità di modifica.
    edit_groups: tuple = ()

    @property
    def toolbar_name(self):
        """Nome della toolbar FreeCAD che contiene i comandi della scheda."""
        return "Forge " + self.label

    def edit_toolbar_names(self):
        """Nomi delle toolbar della modalità di modifica, nell'ordine di ``edit_groups``."""
        return [f"Forge {self.label} - {label}" for label, _ in self.edit_groups]

    def all_toolbars(self):
        """Coppie (nome toolbar, comandi) di tutte le toolbar della scheda."""
        pairs = [(self.toolbar_name, self.commands)]
        pairs += list(zip(self.edit_toolbar_names(), (c for _, c in self.edit_groups)))
        return pairs


TABS = (
    Tab(
        "sketch",
        "Schizzo",
        (
            "PartDesign_NewSketch",
            "Sketcher_EditSketch",
            "Forge_Sketch3D",
            SEPARATOR,
            "Sketcher_MapSketch",
            "Sketcher_ReorientSketch",
            "Sketcher_MirrorSketch",
            "Sketcher_MergeSketches",
            SEPARATOR,
            "Sketcher_ValidateSketch",
            "Forge_SketchDoctor",
        ),
        edit_groups=(
            (
                "Disegno",
                (
                    "Sketcher_LeaveSketch",
                    "Sketcher_ViewSketch",
                    "Sketcher_ViewSection",
                    SEPARATOR,
                    "Sketcher_CreatePoint",
                    "Sketcher_CompLine",
                    "Sketcher_CompCreateArc",
                    "Sketcher_CompCreateConic",
                    "Sketcher_CompCreateRectangles",
                    "Sketcher_CompCreateRegularPolygon",
                    "Sketcher_CompSlot",
                    "Sketcher_CompCreateBSpline",
                    "Sketcher_CreateText",
                    SEPARATOR,
                    "Sketcher_ToggleConstruction",
                    SEPARATOR,
                    "Sketcher_CompCreateFillets",
                    "Sketcher_CompCurveEdition",
                    "Sketcher_CompExternal",
                    "Sketcher_CarbonCopy",
                    SEPARATOR,
                    "Sketcher_Translate",
                    "Sketcher_Rotate",
                    "Sketcher_Scale",
                    "Sketcher_Offset",
                    "Sketcher_Symmetry",
                    SEPARATOR,
                    "Forge_SaveSketchBlock",
                    "Forge_InsertSketchBlock",
                ),
            ),
            (
                "Vincoli",
                (
                    "Sketcher_CompDimensionTools",
                    SEPARATOR,
                    "Sketcher_ConstrainCoincidentUnified",
                    "Sketcher_CompHorVer",
                    "Sketcher_ConstrainParallel",
                    "Sketcher_ConstrainPerpendicular",
                    "Sketcher_ConstrainTangent",
                    "Sketcher_ConstrainEqual",
                    "Sketcher_ConstrainSymmetric",
                    "Sketcher_ConstrainBlock",
                    SEPARATOR,
                    "Sketcher_CompToggleConstraints",
                    SEPARATOR,
                    "Sketcher_SelectElementsWithDoFs",
                    "Sketcher_SelectConflictingConstraints",
                    "Sketcher_SelectRedundantConstraints",
                    "Forge_SketchDoctor",
                ),
            ),
        ),
    ),
    Tab(
        "features",
        "Feature",
        (
            "PartDesign_Body",
            SEPARATOR,
            "PartDesign_Pad",
            "PartDesign_Revolution",
            "PartDesign_AdditiveLoft",
            "PartDesign_AdditivePipe",
            "PartDesign_AdditiveHelix",
            "PartDesign_CompPrimitiveAdditive",
            SEPARATOR,
            "PartDesign_Pocket",
            "PartDesign_Hole",
            "PartDesign_Groove",
            "PartDesign_SubtractiveLoft",
            "PartDesign_SubtractivePipe",
            "PartDesign_SubtractiveHelix",
            "PartDesign_CompPrimitiveSubtractive",
            SEPARATOR,
            "PartDesign_Fillet",
            "PartDesign_Chamfer",
            "PartDesign_Draft",
            "PartDesign_Thickness",
            SEPARATOR,
            "PartDesign_Mirrored",
            "PartDesign_LinearPattern",
            "PartDesign_PolarPattern",
            "PartDesign_PathPattern",
            "PartDesign_PointPattern",
            "PartDesign_MultiTransform",
            SEPARATOR,
            "PartDesign_Boolean",
            "PartDesign_CompDatums",
            "PartDesign_SubShapeBinder",
            "Forge_Configurations",
            "PartDesign_MoveTip",
            "Forge_RollbackPrevious",
            "Forge_RollbackNext",
            "Forge_RollbackToEnd",
        ),
    ),
    Tab(
        "surfaces",
        "Superfici",
        (
            "Part_Extrude",
            "Part_Revolve",
            "Part_Loft",
            "Part_Sweep",
            "Part_RuledSurface",
            SEPARATOR,
            "Surface_Filling",
            "Surface_GeomFillSurface",
            "Surface_Sections",
            "Surface_BlendCurve",
            SEPARATOR,
            "Surface_ExtendFace",
            "Part_ProjectionOnSurface",
            SEPARATOR,
            "Part_CompOffset",
            "Part_Thickness",
        ),
    ),
    Tab(
        "sheetmetal",
        "Lamiera",
        (
            "SheetMetal_BaseShape",
            "SheetMetal_NewSketch",
            "SheetMetal_AddBase",
            "SheetMetal_FromSolid",
            SEPARATOR,
            "SheetMetal_AddWall",
            "SheetMetal_AddHem",
            "SheetMetal_Extrude",
            "SheetMetal_ExtendBySketch",
            "SheetMetal_AddFoldWall",
            "SheetMetal_AddBend",
            SEPARATOR,
            "SheetMetal_AddCornerRelief",
            "SheetMetal_AddRelief",
            "SheetMetal_AddJunction",
            "SheetMetal_AddCutout",
            "SheetMetal_Forming",
            "SheetMetal_SketchOnSheet",
            SEPARATOR,
            "SheetMetal_Unfold",
            "SheetMetal_UnfoldUpdate",
            "Forge_BendTable",
            "Forge_ExportFlatDXF",
        ),
    ),
    Tab(
        "weldments",
        "Saldature",
        (
            "Forge_Sketch3D",
            "PartDesign_NewSketch",
            SEPARATOR,
            "Forge_StructuralMember",
            "Forge_CutList",
            SEPARATOR,
            "Forge_Interference",
        ),
    ),
    Tab(
        "evaluate",
        "Valuta",
        (
            "Std_Measure",
            "Std_MassProperties",
            SEPARATOR,
            "Part_CheckGeometry",
            "Forge_Diagnostics",
            SEPARATOR,
            "Forge_Interference",
            "Forge_DraftAnalysis",
            SEPARATOR,
            "Part_SectionCut",
            "Std_ToggleClipPlane",
        ),
    ),
    Tab(
        "assembly",
        "Assieme",
        (
            "Assembly_CreateAssembly",
            "Assembly_Insert",
            "Assembly_SolveAssembly",
            SEPARATOR,
            "Assembly_ToggleGrounded",
            "Assembly_CreateJointFixed",
            "Assembly_CreateJointRevolute",
            "Assembly_CreateJointCylindrical",
            "Assembly_CreateJointSlider",
            "Assembly_CreateJointBall",
            SEPARATOR,
            "Assembly_CreateJointDistance",
            "Assembly_CreateJointParallel",
            "Assembly_CreateJointPerpendicular",
            "Assembly_CreateJointAngle",
            SEPARATOR,
            "Assembly_CreateJointRackPinion",
            "Assembly_CreateJointScrew",
            "Assembly_CreateJointGearBelt",
            SEPARATOR,
            "Forge_Interference",
            SEPARATOR,
            "Forge_Fastener",
            "Forge_ComponentPattern",
            "Forge_MirrorComponent",
            SEPARATOR,
            "Assembly_CreateView",
            "Assembly_CreateBom",
            "Assembly_CreateSimulation",
        ),
    ),
    Tab(
        "drawing",
        "Tavola",
        (
            "Forge_AutoDrawing",
            "TechDraw_PageDefault",
            "TechDraw_PageTemplate",
            SEPARATOR,
            "TechDraw_View",
            "TechDraw_ActiveView",
            "TechDraw_SectionGroup",
            "TechDraw_DetailView",
            "TechDraw_BrokenView",
            SEPARATOR,
            "TechDraw_Dimension",
            "TechDraw_Balloon",
            "TechDraw_HoleShaftFit",
            SEPARATOR,
            "TechDraw_CenterLineGroup",
            "TechDraw_Hatch",
            "TechDraw_LeaderLine",
            "TechDraw_RichTextAnnotation",
            "TechDraw_SurfaceFinishSymbols",
            "TechDraw_WeldSymbol",
            SEPARATOR,
            "TechDraw_SpreadsheetView",
            "TechDraw_FillTemplateFields",
            "TechDraw_ExportPageSVG",
            "TechDraw_ExportPageDXF",
        ),
    ),
)

DEFAULT_TAB = "features"


def tab_by_key(key):
    """Restituisce la scheda con la chiave data, oppure None."""
    for tab in TABS:
        if tab.key == key:
            return tab
    return None


def resolve_commands(commands, available):
    """Filtra i comandi tenendo solo quelli registrati.

    ``available`` è l'insieme dei comandi esistenti (``FreeCADGui.listCommands()``).
    Rimuove anche i separatori iniziali, finali e doppi lasciati dai comandi mancanti.
    Restituisce la coppia (comandi risolti, comandi mancanti).
    """
    resolved = []
    missing = []
    for name in commands:
        if name == SEPARATOR:
            if resolved and resolved[-1] != SEPARATOR:
                resolved.append(SEPARATOR)
        elif name in available:
            resolved.append(name)
        else:
            missing.append(name)
    while resolved and resolved[-1] == SEPARATOR:
        resolved.pop()
    return resolved, missing
