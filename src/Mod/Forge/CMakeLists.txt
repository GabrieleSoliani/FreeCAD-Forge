# SPDX-License-Identifier: LGPL-2.1-or-later
# FreeCAD Forge: ambiente unificato in stile SolidWorks (modulo solo Python).

SET(Forge_SRCS
    Init.py
    InitGui.py
)

SET(ForgeLib_SRCS
    forgelib/__init__.py
    forgelib/commands.py
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
)

SET(Forge_Icons
    Resources/icons/ForgeWorkbench.svg
    Resources/icons/Forge_Rollback_prev.svg
    Resources/icons/Forge_Rollback_next.svg
    Resources/icons/Forge_Rollback_end.svg
    Resources/icons/Forge_RadialMenu.svg
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
