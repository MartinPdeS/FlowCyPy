cmake_minimum_required(VERSION 3.20)
set(CMAKE_OSX_DEPLOYMENT_TARGET "14.0" CACHE STRING "Minimum OS X deployment version")
project(FlowCyPy CXX)

# CMake settings
set(CMAKE_VERBOSE_MAKEFILE ON)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(CMAKE_BUILD_TYPE "Release" CACHE STRING "Type of build" FORCE)


# Set the output directory for libraries
set(FLOWCYPY_CXX_DIR "${CMAKE_SOURCE_DIR}/FlowCyPy/cpp")
set(FLOWCYPY_BIN_DIR "${CMAKE_SOURCE_DIR}/FlowCyPy/binary")

# Directories
set(LOCAL_CXX_DIR "${PROJECT_NAME}/cpp")
set(LOCAL_BIN_DIR "${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/binary")
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${LOCAL_BIN_DIR}")

# Include directories
include_directories("${LOCAL_CXX_DIR}")

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)
find_package(pybind11 CONFIG REQUIRED)
message(STATUS "Found pybind11 version: ${pybind11_VERSION}")

# Platform-specific settings for static linking
if (WIN32 AND CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    message("MinGW detected on Windows")
    set(STATIC_LINK_OPTIONS "-static")
    add_link_options(-static)
endif()

add_compile_options(-Wall -Wextra -pedantic-errors)

add_subdirectory(FlowCyPy/cpp/dummy)               # dummy
add_subdirectory(FlowCyPy/cpp/triggering_system)   # triggering_system
add_subdirectory(FlowCyPy/cpp/signal_generator)    # signal_generator
add_subdirectory(FlowCyPy/cpp/peak_locator)        # peak_locator