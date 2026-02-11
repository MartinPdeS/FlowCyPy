# cpp/distributions/CMakeLists.txt

set(NAME "distributions")

# --- C++ static library -------------------------------------------------
add_library("${NAME}" STATIC "${NAME}.cpp")
target_link_libraries("${NAME}" PUBLIC pint)
set_target_properties("${NAME}" PROPERTIES OUTPUT_NAME "${NAME}")

# --- Python extension module --------------------------------------------
pybind11_add_module("interface_${NAME}" MODULE interface.cpp)
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "interface_${NAME}")
target_link_libraries("interface_${NAME}" PRIVATE "${NAME}" pint pybind11::module)
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "${NAME}")

# --- Install -------------------------------------------------------------

set_property(GLOBAL APPEND PROPERTY FLOWCYPY_TARGETS "${NAME}" "interface_${NAME}")
