set(NAME "signal_generator")

# Find FFTW library
find_package(OpenMP REQUIRED)
find_package(PkgConfig REQUIRED)
pkg_search_module(FFTW REQUIRED fftw3 IMPORTED_TARGET)



add_library("cpp_${NAME}" STATIC "signal_generator.cpp")
target_include_directories("cpp_${NAME}" PUBLIC ${FFTW_INCLUDE_DIRS})
target_link_libraries("cpp_${NAME}" PRIVATE pybind11::module PkgConfig::FFTW OpenMP::OpenMP_CXX cpp_utils)


# Create your Python module
pybind11_add_module("interface_${NAME}" MODULE interface.cpp)
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "interface_${NAME}")
target_link_libraries("interface_${NAME}" PRIVATE pybind11::module PkgConfig::FFTW OpenMP::OpenMP_CXX "cpp_${NAME}")
target_include_directories("interface_${NAME}" PRIVATE pybind11::module ${FFTW_INCLUDE_DIRS})


install(
    TARGETS cpp_${NAME} interface_${NAME}
    LIBRARY DESTINATION ${LOCAL_BIN_DIR}
    ARCHIVE DESTINATION ${LOCAL_BIN_DIR}
    RUNTIME DESTINATION ${LOCAL_BIN_DIR}
)
