# SPDX-License-Identifier: LGPL-2.1-or-later
# FreeCAD Forge: ambiente unificato in stile SolidWorks (modulo solo Python).

SET(Forge_SRCS
    Init.py
    InitGui.py
)

SET(ForgeLib_SRCS
    forgelib/__init__.py
    forgelib/commands.py
    forgelib/diagnostics.py
    forgelib/evaluate.py
    forgelib/evaluate_gui.py
    forgelib/sketch_doctor.py
    forgelib/sketch_doctor_gui.py
    forgelib/sketch_blocks.py
    forgelib/sketch_blocks_gui.py
    forgelib/features/__init__.py
    forgelib/features/sketch3d.py
    forgelib/sheetmetal.py
    forgelib/sheetmetal_gui.py
    forgelib/rollback.py
    forgelib/settings.py
    forgelib/ui/__init__.py
    forgelib/ui/catalog.py
    forgelib/ui/context.py
    forgelib/ui/command_manager.py
    forgelib/ui/headsup.py
    forgelib/ui/radial.py
)

SET(ForgeTests_SRCS
    ForgeTests/__init__.py
    ForgeTests/TestForgeApp.py
    ForgeTests/TestForgeGui.py
    ForgeTests/models.py
    ForgeTests/TestForgeRobustness.py
    ForgeTests/TestForgeDiagnostics.py
    ForgeTests/TestForgeExamples.py
    ForgeTests/examples.py
    ForgeTests/TestForgeEvaluate.py
    ForgeTests/TestForgeEvaluateGui.py
    ForgeTests/TestForgeSketchDoctor.py
    ForgeTests/TestForgeSketchBlocks.py
    ForgeTests/TestForgeSketch3D.py
    ForgeTests/TestForgeSheetMetal.py
)

SET(Forge_Icons
    Resources/icons/ForgeWorkbench.svg
    Resources/icons/Forge_Rollback_prev.svg
    Resources/icons/Forge_Rollback_next.svg
    Resources/icons/Forge_Rollback_end.svg
    Resources/icons/Forge_RadialMenu.svg
    Resources/icons/Forge_Diagnostics.svg
    Resources/icons/Forge_Interference.svg
    Resources/icons/Forge_DraftAnalysis.svg
    Resources/icons/Forge_SketchDoctor.svg
    Resources/icons/Forge_SketchBlock.svg
    Resources/icons/Forge_SketchBlockInsert.svg
    Resources/icons/Forge_Sketch3D.svg
    Resources/icons/Forge_BendTable.svg
    Resources/icons/Forge_FlatDXF.svg
)

SET(Forge_ALL ${Forge_SRCS} ${ForgeLib_SRCS} ${ForgeTests_SRCS} ${Forge_Icons})
SOURCE_GROUP("" FILES ${Forge_ALL})

ADD_CUSTOM_TARGET(Forge ALL
    SOURCES ${Forge_ALL}
)

fc_copy_sources(Forge "${CMAKE_BINARY_DIR}/Mod/Forge" ${Forge_ALL})

INSTALL(FILES ${Forge_SRCS} DESTINATION Mod/Forge)
INSTALL(FILES ${ForgeTests_SRCS} DESTINATION Mod/Forge/ForgeTests)
INSTALL(FILES ${Forge_Icons} DESTINATION Mod/Forge/Resources/icons)
INSTALL(DIRECTORY forgelib DESTINATION Mod/Forge FILES_MATCHING PATTERN "*.py")
