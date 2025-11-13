set(NAME "utils")

# --- C++ static library -------------------------------------------------
add_library("core_${NAME}" STATIC "utils.cpp")
message(STATUS "FFTW3_INCLUDE_DIRS       = ${FFTW_INCLUDE_DIRS}")
target_include_directories("core_${NAME}" PUBLIC ${FFTW_INCLUDE_DIRS})
target_link_libraries("core_${NAME}" PUBLIC pybind11::module PkgConfig::FFTW OpenMP::OpenMP_CXX)
set_target_properties("core_${NAME}" PROPERTIES OUTPUT_NAME "${NAME}")

# --- Python extension module --------------------------------------------
pybind11_add_module("interface_${NAME}" MODULE interface.cpp)
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "interface_${NAME}")
target_link_libraries("interface_${NAME}" PRIVATE pybind11::module PkgConfig::FFTW "core_${NAME}")
target_include_directories("interface_${NAME}" PRIVATE pybind11::module ${FFTW_INCLUDE_DIRS})
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "${NAME}")

# --- Install -------------------------------------------------------------
install(
    TARGETS core_${NAME} interface_${NAME}
    LIBRARY DESTINATION ${LOCAL_BIN_DIR}
    ARCHIVE DESTINATION ${LOCAL_BIN_DIR}
    RUNTIME DESTINATION ${LOCAL_BIN_DIR}
)
