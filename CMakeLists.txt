# Copyright (C) 2023-2024 CEA/DES, EDF R&D
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
# See http://www.salome-platform.org/ or email : webmaster.salome@opencascade.com
#
CMAKE_MINIMUM_REQUIRED(VERSION 3.0 FATAL_ERROR)
INCLUDE(CMakeDependentOption)
PROJECT(BooleanMeshOperation)
STRING(TOUPPER ${PROJECT_NAME} PROJECT_NAME_UC)

# Options
# - SAT: use SALOME Tool to build and install this plugin
OPTION(USE_SAT  "Use SALOME Tool (SAT) to build boolean mesh operation" OFF)

# =======================
# - CGAL: Computational Geometry Algorithms Library
# - MCUT: library for detecting and resolving intersections between two surface meshes
# - IRMB: Interactive And Robust Mesh Booleans
# - CORK: 3D Boolean / CSG Library
# - IGL : A simple C++ geometry processing library
OPTION(BUILD_CGAL "Build CGAL engine"                                     ON )
OPTION(BUILD_MCUT "Build MCUT engine"                                     OFF)
OPTION(BUILD_IRMB "Build IRMB engine"                                     ON )
OPTION(BUILD_CORK "Build Cork engine"                                     OFF)
OPTION(BUILD_IGL  "Build IGL engine"                                      OFF)

IF (NOT USE_SAT)
  IF (BUILD_CGAL)
    ADD_SUBDIRECTORY(cgal)
  ENDIF()

  IF (BUILD_MCUT)
    ADD_SUBDIRECTORY(mcut)
  ENDIF()

  IF (BUILD_IRMB)
    ADD_SUBDIRECTORY(irmb)
  ENDIF()

  IF (BUILD_CORK)
    ADD_SUBDIRECTORY(cork)
  ENDIF()

  IF (BUILD_IGL)
    ADD_SUBDIRECTORY(libigl)
  ENDIF()
ELSE ()
  MESSAGE(STATUS "Using SALOME TOOL standard and recommended approach")

  # Check for CONFIGURATION package. Configuration provides a set of useful CMake macros
  # ====================================================================================
  SET(CONFIGURATION_ROOT_DIR $ENV{CONFIGURATION_ROOT_DIR} CACHE PATH "Path to the Salome CMake configuration files")
  IF (EXISTS ${CONFIGURATION_ROOT_DIR})
    LIST(APPEND CMAKE_MODULE_PATH "${CONFIGURATION_ROOT_DIR}/cmake")
    INCLUDE(SalomeMacros NO_POLICY_SCOPE)
  ELSE()
    MESSAGE(FATAL_ERROR "We absolutely need the Salome CMake configuration files, please define CONFIGURATION_ROOT_DIR !")
  ENDIF()

  # Set Version
  # ===========
  SALOME_SETUP_VERSION(1.0)

  SET(SMESH_ROOT_DIR $ENV{SMESH_ROOT_DIR} CACHE PATH "Path to SMESH")
  IF (NOT EXISTS ${SMESH_ROOT_DIR})
    MESSAGE(FATAL_ERROR "SMESH_ROOT_DIR environment variable is missing, please define SMESH_ROOT_DIR")
  ENDIF()

  # Python
  # ===========
  FIND_PACKAGE(SalomePythonInterp REQUIRED)
  FIND_PACKAGE(SalomePythonLibs REQUIRED)

  # Python Qt
  # ===========
  FIND_PACKAGE(SalomePyQt5 REQUIRED)
  INCLUDE(UsePyQt)

  SET(_plugin_SCRIPTS
    mesh_boolean_plugin.py
    mesh_boolean_dialog.py
    MyPlugDialog.ui
  )

  SET(_pyuic_FILES
    MyPlugDialog.ui
  )

  # scripts / pyuic wrappings
  PYQT_WRAP_UIC(_pyuic_SCRIPTS ${_pyuic_FILES} TARGET_NAME _target_name_pyuic)

  # Installation
  SET(Mesh_Boolean_INSTALL_PLUGIN "plugins/meshbooleanplugin")
  SET(Mesh_Boolean_INSTALL_TESTS  "."                        )
  SET(Mesh_Boolean_INSTALL_MISC   "misc"                     )
  SET(Mesh_Boolean_INSTALL_DOC    "doc"                      )
  SALOME_INSTALL_SCRIPTS("${_plugin_SCRIPTS}" "${Mesh_Boolean_INSTALL_PLUGIN}")
  SALOME_INSTALL_SCRIPTS("${_pyuic_SCRIPTS}" "${Mesh_Boolean_INSTALL_PLUGIN}" TARGET_NAME _target_name_pyuic_py)

  # add dependency toi compiled py files on uic files in order
  # to avoid races problems when compiling in parallel
  ADD_DEPENDENCIES(${_target_name_pyuic_py} ${_target_name_pyuic})

  # Install the files
  INSTALL(FILES "${PROJECT_SOURCE_DIR}/README.md" DESTINATION "${Mesh_Boolean_INSTALL_DOC}" )
  SALOME_CONFIGURE_FILE(__init__.py __init__.py INSTALL "${Mesh_Boolean_INSTALL_PLUGIN}")

  # Install all engines scripts
  SET(Mesh_Boolean_Engines vtk cgal cork irmb libigl mcut)
  FOREACH(Mesh_Boolean_Engine ${Mesh_Boolean_Engines})
    MESSAGE(status "hello ${PROJECT_SOURCE_DIR}/${Mesh_Boolean_Engine}/exec_${Mesh_Boolean_Engine}.py")
    INSTALL(FILES "${PROJECT_SOURCE_DIR}/${Mesh_Boolean_Engine}/exec_${Mesh_Boolean_Engine}.py" DESTINATION "${Mesh_Boolean_INSTALL_PLUGIN}/${Mesh_Boolean_Engine}" )
  ENDFOREACH()
ENDIF()
