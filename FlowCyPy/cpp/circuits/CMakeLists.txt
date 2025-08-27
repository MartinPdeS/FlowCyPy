# cpp/circuits/CMakeLists.txt

set(NAME "circuits")

# Create your library target
add_library("cpp_${NAME}" STATIC "${NAME}.cpp")

# Link with pybind11 module target
target_link_libraries("cpp_${NAME}" PUBLIC pybind11::module OpenMP::OpenMP_CXX "cpp_signal_generator")

# Create your Python module
pybind11_add_module("interface_${NAME}" MODULE interface.cpp)
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "interface_${NAME}")
target_link_libraries("interface_${NAME}" PRIVATE "cpp_${NAME}")

install(
    TARGETS cpp_${NAME} interface_${NAME}
    LIBRARY DESTINATION ${LOCAL_BIN_DIR}
    ARCHIVE DESTINATION ${LOCAL_BIN_DIR}
    RUNTIME DESTINATION ${LOCAL_BIN_DIR}
)
