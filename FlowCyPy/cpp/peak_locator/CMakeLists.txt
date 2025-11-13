# cpp/peak_locator/CMakeLists.txt
set(NAME "peak_locator")

# --- C++ static library -------------------------------------------------
add_library("core_${NAME}" STATIC "${NAME}.cpp")

# Link with pybind11 module target
target_link_libraries("core_${NAME}" PRIVATE pybind11::module)
set_target_properties("core_${NAME}" PROPERTIES OUTPUT_NAME "${NAME}")

# --- Python extension module --------------------------------------------
pybind11_add_module("interface_${NAME}" MODULE interface.cpp)
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "interface_${NAME}")
target_link_libraries("interface_${NAME}" PRIVATE "core_${NAME}")
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "${NAME}")

# --- Install -------------------------------------------------------------
install(
    TARGETS core_${NAME} interface_${NAME}
    LIBRARY DESTINATION ${LOCAL_BIN_DIR}
    ARCHIVE DESTINATION ${LOCAL_BIN_DIR}
    RUNTIME DESTINATION ${LOCAL_BIN_DIR}
)
