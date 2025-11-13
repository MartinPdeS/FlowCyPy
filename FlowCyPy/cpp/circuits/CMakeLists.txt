# cpp/circuits/CMakeLists.txt

set(NAME "circuits")

# --- C++ static library -------------------------------------------------
add_library("core_${NAME}" STATIC "${NAME}.cpp")
target_link_libraries("core_${NAME}" PUBLIC pybind11::module OpenMP::OpenMP_CXX "core_signal_generator")
set_target_properties("core_${NAME}" PROPERTIES OUTPUT_NAME "${NAME}")
target_include_directories("core_${NAME}" PRIVATE ${FFTW_INCLUDE_DIRS})

# --- Python extension module --------------------------------------------
pybind11_add_module("interface_${NAME}" MODULE interface.cpp)
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "interface_${NAME}")
target_link_libraries("interface_${NAME}" PRIVATE "core_${NAME}")
target_include_directories("interface_${NAME}" PRIVATE ${FFTW_INCLUDE_DIRS})
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "${NAME}")

# --- Install -------------------------------------------------------------
install(
    TARGETS core_${NAME} interface_${NAME}
    LIBRARY DESTINATION ${LOCAL_BIN_DIR}
    ARCHIVE DESTINATION ${LOCAL_BIN_DIR}
    RUNTIME DESTINATION ${LOCAL_BIN_DIR}
)
