cmake_minimum_required(VERSION 3.10)
project(BooleanMeshOperation)

option(BUILD_CGAL "Build CGAL engine" ON)
option(BUILD_MCUT "Build MCUT engine" OFF)
option(BUILD_IRMB "Build IRMB engine" ON)
option(BUILD_CORK "Build Cork engine" OFF)
option(BUILD_IGL  "Build IGL engine"  OFF)

if(BUILD_CGAL)
    add_subdirectory(cgal)
endif()

if(BUILD_MCUT)
    add_subdirectory(mcut)
endif()

if(BUILD_IRMB)
    add_subdirectory(irmb)
endif()

if(BUILD_CORK)
    add_subdirectory(cork)
endif()

if(BUILD_IGL)
    add_subdirectory(libigl)
endif()
