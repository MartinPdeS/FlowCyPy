cmake_minimum_required(VERSION 3.20)
set(CMAKE_OSX_DEPLOYMENT_TARGET "15.0" CACHE STRING "Minimum OS X deployment version")
project(FlowCyPy CXX)

# CMake settings
set(CMAKE_VERBOSE_MAKEFILE ON)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(CMAKE_BUILD_TYPE "Release" CACHE STRING "Type of build")

# Set the output directory for libraries
set(LOCAL_CXX_DIR "${PROJECT_NAME}/cpp")
set(LOCAL_BIN_DIR "${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/binary")




# Tell CMake which lib name AppleClang uses, then find OpenMP once, top-level
if(APPLE AND CMAKE_CXX_COMPILER_ID STREQUAL "AppleClang")
  set(OpenMP_C_LIB_NAMES  "omp" CACHE STRING "" FORCE)
  set(OpenMP_CXX_LIB_NAMES "omp" CACHE STRING "" FORCE)
endif()

find_package(OpenMP REQUIRED)

# Make CMake carry rpaths from link libraries into targets
set(CMAKE_MACOSX_RPATH ON)
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)

# Default rpath to Homebrew's libomp (works for GitHub macOS-14/15 runners)
if(APPLE)
  if(DEFINED ENV{HOMEBREW_PREFIX})
    set(_omp_root "$ENV{HOMEBREW_PREFIX}/opt/libomp")
  else()
    set(_omp_root "/opt/homebrew/opt/libomp")
  endif()
  # also helpful if you run from the build tree
  list(APPEND CMAKE_BUILD_RPATH "${_omp_root}/lib")
  list(APPEND CMAKE_INSTALL_RPATH "${_omp_root}/lib")
endif()















# # Find dependencies
# if(APPLE AND CMAKE_CXX_COMPILER_ID STREQUAL "AppleClang")
#   set(OpenMP_CXX_FLAGS "-Xpreprocessor -fopenmp" CACHE STRING "")
#   set(OpenMP_CXX_LIB_NAMES "omp" CACHE STRING "")
#   find_library(OpenMP_omp_LIBRARY omp HINTS $ENV{LIBOMP_PREFIX}/lib /opt/homebrew/opt/libomp/lib /usr/local/opt/libomp/lib)
#   if(OpenMP_omp_LIBRARY)
#     set(OpenMP_CXX_LIBRARIES "${OpenMP_omp_LIBRARY}" CACHE STRING "")
#   endif()
# endif()


# Include directories
find_package(OpenMP REQUIRED)
find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)
find_package(pybind11 CONFIG REQUIRED)

# Platform-specific settings for static linking
if (WIN32 AND CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    message("MinGW detected on Windows")
    set(STATIC_LINK_OPTIONS "-static")
    add_link_options(-static)
endif()

# Compiler and linker options
add_compile_options(-Wall -Wextra -pedantic-errors)

# Print some messages
message(STATUS "OPENMP flags: ${OpenMP_CXX_FLAGS}")
message(STATUS "FlowCyPy version is: ${FLOWCYPY_VERSION}")
message(STATUS "FlowCyPy includes directory is: ${FLOWCYPY_CXX_DIR}")
message(STATUS "Python version to be compiled against: ${PYBIND11_PYTHON_VERSION}")
message(STATUS "Binary will be installed in location: ${LOCAL_BIN_DIR}")

add_subdirectory(FlowCyPy/cpp/utils)               # utils
add_subdirectory(FlowCyPy/cpp/flow_cell)           # flow_cell
add_subdirectory(FlowCyPy/cpp/circuits)            # circuits
add_subdirectory(FlowCyPy/cpp/trigger)             # trigger
add_subdirectory(FlowCyPy/cpp/triggering_system)   # triggering_system
add_subdirectory(FlowCyPy/cpp/signal_generator)    # signal_generator
add_subdirectory(FlowCyPy/cpp/peak_locator)        # peak_locator
# add_subdirectory("FlowCyPy/cpp/coupling")          # coupling
