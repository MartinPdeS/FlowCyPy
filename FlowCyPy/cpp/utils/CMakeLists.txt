set(NAME "utils")

# --- C++ static library -------------------------------------------------
add_library("${NAME}" STATIC "utils.cpp")
target_include_directories("${NAME}" PUBLIC ${FFTW_INCLUDE_DIRS})
target_link_libraries("${NAME}" PUBLIC pybind11::module PkgConfig::FFTW OpenMP::OpenMP_CXX)
set_target_properties("${NAME}" PROPERTIES OUTPUT_NAME "${NAME}")

# --- Python extension module --------------------------------------------
pybind11_add_module("interface_${NAME}" MODULE interface.cpp)
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "interface_${NAME}")
target_link_libraries("interface_${NAME}" PRIVATE pybind11::module PkgConfig::FFTW "${NAME}")
target_include_directories("interface_${NAME}" PRIVATE pybind11::module ${FFTW_INCLUDE_DIRS})
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "${NAME}")

# --- Install -------------------------------------------------------------
set_property(GLOBAL APPEND PROPERTY FLOWCYPY_TARGETS "${NAME}" "interface_${NAME}")
