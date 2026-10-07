# SPDX-License-Identifier: LGPL-2.1-or-later
# FreeCAD Forge: addon SheetMetal (LGPL 2.1, https://github.com/shaise/FreeCAD_SheetMetal)
# copiato senza modifiche, vedi THIRD_PARTY.md. Questo file e' l'unica aggiunta di Forge.

file(GLOB_RECURSE SheetMetal_FILES
    RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}"
    CONFIGURE_DEPENDS
    "${CMAKE_CURRENT_SOURCE_DIR}/*.py"
    "${CMAKE_CURRENT_SOURCE_DIR}/*.svg"
    "${CMAKE_CURRENT_SOURCE_DIR}/*.ui"
    "${CMAKE_CURRENT_SOURCE_DIR}/*.qm"
    "${CMAKE_CURRENT_SOURCE_DIR}/*.png"
    "${CMAKE_CURRENT_SOURCE_DIR}/*.xml"
    "${CMAKE_CURRENT_SOURCE_DIR}/*.FCStd"
    "${CMAKE_CURRENT_SOURCE_DIR}/*.FCMacro"
    "${CMAKE_CURRENT_SOURCE_DIR}/LICENSE"
)

ADD_CUSTOM_TARGET(SheetMetal ALL SOURCES ${SheetMetal_FILES})
fc_copy_sources(SheetMetal "${CMAKE_BINARY_DIR}/Mod/SheetMetal" ${SheetMetal_FILES})

foreach(f ${SheetMetal_FILES})
    get_filename_component(d "${f}" DIRECTORY)
    INSTALL(FILES "${f}" DESTINATION "Mod/SheetMetal/${d}")
endforeach()
