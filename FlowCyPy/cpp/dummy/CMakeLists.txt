# cpp/dummy/CMakeLists.txt

set(NAME "dummy")

# Create your Python module
pybind11_add_module("interface_${NAME}" MODULE interface.cpp)
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "interface_${NAME}")


install(
    TARGETS interface_${NAME}
    LIBRARY DESTINATION ${FLOWCYPY_BIN_DIR}
    ARCHIVE DESTINATION ${FLOWCYPY_BIN_DIR}
    RUNTIME DESTINATION ${FLOWCYPY_BIN_DIR}
)