# cpp/utils/CMakeLists.txt

set(NAME "filter")

# Create your library target
add_library("cpp_${NAME}" STATIC "${NAME}.cpp")

# Link with pybind11 module target
target_link_libraries("cpp_${NAME}" PUBLIC pybind11::module cpp_utils)

# Create your Python module
pybind11_add_module("interface_${NAME}" MODULE interface.cpp)
target_link_libraries("interface_${NAME}" PRIVATE "cpp_${NAME}")
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "interface_${NAME}")
