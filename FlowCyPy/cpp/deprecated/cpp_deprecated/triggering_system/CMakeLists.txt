# cpp/triggering_system/CMakeLists.txt

set(NAME "triggering_system")

# Create your library target
add_library("cpp_${NAME}" STATIC "${NAME}.cpp")

# Link with pybind11 module target
target_link_libraries("cpp_${NAME}" PRIVATE pybind11::module cpp_filter)

# Create your Python module
pybind11_add_module("interface_${NAME}" MODULE interface.cpp)

set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "interface_${NAME}")
