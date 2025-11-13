# cpp/classifier/CMakeLists.txt
set(NAME "classifier")

# Create your library target
add_library("core_${NAME}" STATIC "${NAME}.cpp")
target_link_libraries("core_${NAME}" PRIVATE)
set_target_properties("core_${NAME}" PROPERTIES OUTPUT_NAME "${NAME}")

# Create your Python module
pybind11_add_module("interface_${NAME}" MODULE interface.cpp)
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "interface_${NAME}")
target_link_libraries("interface_${NAME}" PUBLIC "core_${NAME}")
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "${NAME}")


install(
    TARGETS core_${NAME} interface_${NAME}
    LIBRARY DESTINATION ${LOCAL_BIN_DIR}
    ARCHIVE DESTINATION ${LOCAL_BIN_DIR}
    RUNTIME DESTINATION ${LOCAL_BIN_DIR}
)
