# cpp/core/CMakeLists.txt
set(NAME "core")

# Create your library target
add_library("cpp_${NAME}" STATIC "${NAME}.cpp")

# Link with pybind11 module target
target_link_libraries("cpp_${NAME}" PRIVATE pybind11::module)


# Create your Python module
pybind11_add_module("interface_${NAME}" MODULE interface.cpp)
target_link_libraries("interface_${NAME}" PRIVATE pybind11::module "cpp_${NAME}")
target_include_directories("interface_${NAME}" PRIVATE pybind11::module)
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "interface_${NAME}")
