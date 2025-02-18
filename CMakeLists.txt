cmake_minimum_required(VERSION 3.10)
project(FlowCyPy CXX)

# CMake settings
set(CMAKE_VERBOSE_MAKEFILE ON)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(CMAKE_BUILD_TYPE "Release" CACHE STRING "Type of build" FORCE)

# Directories
set(LOCAL_CXX_DIR "${PROJECT_NAME}/cpp")
set(LOCAL_BIN_DIR "${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/binary")
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${LOCAL_BIN_DIR}")

# Include directories
include_directories("${LOCAL_CXX_DIR}")

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)
find_package(pybind11 CONFIG REQUIRED)

# Function to add project modules
function(add_project_module name source)
    pybind11_add_module(${name} MODULE "${LOCAL_CXX_DIR}/${source}")
    set_target_properties(${name} PROPERTIES OUTPUT_NAME ${name})
endfunction()

add_project_module(Interface "interface.cpp")
