cmake_minimum_required(VERSION 3.12)
project(cgal)

set(CGAL_DIR ${CMAKE_CURRENT_SOURCE_DIR}/cgal CACHE PATH "Path to CGAL installation")
set(EXECUTABLE_OUTPUT_PATH ${CMAKE_CURRENT_SOURCE_DIR})

# Find CGAL package
find_package(CGAL REQUIRED COMPONENTS Core)

# Add executable
add_executable(exec_cgal exec_cgal.cc)

# Link CGAL libraries
target_link_libraries(exec_cgal PRIVATE CGAL::CGAL)

# Enable C++11 features
target_compile_features(exec_cgal PRIVATE cxx_std_11)
