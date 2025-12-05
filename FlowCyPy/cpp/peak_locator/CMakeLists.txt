# cpp/peak_locator/CMakeLists.txt
set(NAME "peak_locator")

# --- C++ static library -------------------------------------------------
add_library("${NAME}" STATIC "${NAME}.cpp")

# Link with pybind11 module target
target_link_libraries("${NAME}" PRIVATE pybind11::module)
set_target_properties("${NAME}" PROPERTIES OUTPUT_NAME "${NAME}")

# --- Python extension module --------------------------------------------
pybind11_add_module("interface_${NAME}" MODULE interface.cpp)
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "interface_${NAME}")
target_link_libraries("interface_${NAME}" PRIVATE "${NAME}")
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "${NAME}")

# --- Install -------------------------------------------------------------
set_property(GLOBAL APPEND PROPERTY FLOWCYPY_TARGETS "${NAME}" "interface_${NAME}")
