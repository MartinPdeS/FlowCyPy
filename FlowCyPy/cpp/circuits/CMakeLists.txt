# cpp/circuits/CMakeLists.txt

set(NAME "circuits")

# --- C++ static library -------------------------------------------------
add_library("${NAME}" STATIC "${NAME}.cpp")
target_link_libraries("${NAME}" PUBLIC pybind11::module OpenMP::OpenMP_CXX signal_generator)
set_target_properties("${NAME}" PROPERTIES OUTPUT_NAME "${NAME}")
target_include_directories("${NAME}" PRIVATE ${FFTW_INCLUDE_DIRS})

# --- Python extension module --------------------------------------------
pybind11_add_module("interface_${NAME}" MODULE interface.cpp)
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "interface_${NAME}")
target_link_libraries("interface_${NAME}" PRIVATE "${NAME}" pint)
target_include_directories("interface_${NAME}" PRIVATE ${FFTW_INCLUDE_DIRS})
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "${NAME}")

# --- Install -------------------------------------------------------------

set_property(GLOBAL APPEND PROPERTY FLOWCYPY_TARGETS "${NAME}" "interface_${NAME}")
