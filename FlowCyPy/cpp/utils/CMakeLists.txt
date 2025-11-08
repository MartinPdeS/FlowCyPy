set(NAME "utils")


add_library("cpp_${NAME}" STATIC "utils.cpp")
target_include_directories("cpp_${NAME}" PUBLIC ${FFTW_INCLUDE_DIRS})
target_link_libraries("cpp_${NAME}" PUBLIC pybind11::module PkgConfig::FFTW OpenMP::OpenMP_CXX)


# Create your Python module
pybind11_add_module("interface_${NAME}" MODULE interface.cpp)
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "interface_${NAME}")
target_link_libraries("interface_${NAME}" PRIVATE pybind11::module PkgConfig::FFTW "cpp_${NAME}")
target_include_directories("interface_${NAME}" PRIVATE pybind11::module ${FFTW_INCLUDE_DIRS})


install(
    TARGETS cpp_${NAME} interface_${NAME}
    LIBRARY DESTINATION ${LOCAL_BIN_DIR}
    ARCHIVE DESTINATION ${LOCAL_BIN_DIR}
    RUNTIME DESTINATION ${LOCAL_BIN_DIR}
)
