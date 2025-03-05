cmake_minimum_required(VERSION 3.20)
set(CMAKE_OSX_DEPLOYMENT_TARGET "14.0" CACHE STRING "Minimum OS X deployment version")
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
# set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=address -fno-omit-frame-pointer")

# Include directories
include_directories("${LOCAL_CXX_DIR}")

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)
find_package(pybind11 CONFIG REQUIRED)

# Platform-specific settings for static linking
if (WIN32 AND CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    message("MinGW detected on Windows")
    set(STATIC_LINK_OPTIONS "-static")
    add_link_options(-static)
elseif (CMAKE_CXX_COMPILER_ID STREQUAL "AppleClang")
    message("AppleClang compiler detected")
elseif (CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    message("GNU compiler detected")
endif()


# Function to add project modules
function(add_project_module name)
    # Create an empty list to store full paths for source files.
    set(SOURCES "")

    # ARGN contains all the arguments passed after the first one (the module name).
    foreach(src IN LISTS ARGN)
        list(APPEND SOURCES "${LOCAL_CXX_DIR}/${src}")
    endforeach()

    pybind11_add_module(${name} MODULE ${SOURCES})
    set_target_properties(${name} PROPERTIES OUTPUT_NAME ${name})
    target_link_options(${name} PUBLIC ${STATIC_LINK_OPTIONS})
endfunction()

add_compile_options(-Wall -Wextra -pedantic-errors)

add_project_module(filtering "filter.cpp")

# add_project_module(triggering_system "triggering.cpp" "filter.cpp")

add_project_module(triggering_system "triggering_system.cpp" "filter.cpp")