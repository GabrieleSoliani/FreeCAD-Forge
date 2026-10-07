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
)


@dataclass(frozen=True)
class Tab:
    """Una scheda del command manager."""

    key: str  # identificatore stabile, usato nei parametri e nei test
    label: str  # testo mostrato sulla linguetta
    commands: tuple  # nomi dei comandi FreeCAD, con SEPARATOR tra i gruppi

    @property
    def toolbar_name(self):
        """Nome della toolbar FreeCAD che contiene i comandi della scheda."""
        return "Forge " + self.label


TABS = (
    Tab(
        "sketch",
        "Schizzo",
        (
            "PartDesign_NewSketch",
            "Sketcher_EditSketch",
            SEPARATOR,
            "Sketcher_MapSketch",
            "Sketcher_ReorientSketch",
            "Sketcher_MirrorSketch",
            "Sketcher_MergeSketches",
            SEPARATOR,
            "Sketcher_ValidateSketch",
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
            "PartDesign_MoveTip",
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
        "evaluate",
        "Valuta",
        (
            "Std_Measure",
            "Std_MassProperties",
            SEPARATOR,
            "Part_CheckGeometry",
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
            "Assembly_CreateView",
            "Assembly_CreateBom",
            "Assembly_CreateSimulation",
        ),
    ),
    Tab(
        "drawing",
        "Tavola",
        (
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
