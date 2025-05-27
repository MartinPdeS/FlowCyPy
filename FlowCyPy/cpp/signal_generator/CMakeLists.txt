set(NAME "signal_generator")

# Find FFTW library
find_package(OpenMP REQUIRED)
find_package(PkgConfig REQUIRED)
pkg_search_module(FFTW REQUIRED fftw3 IMPORTED_TARGET)



add_library("cpp_signal_generator" STATIC "signal_generator.cpp")
target_include_directories("cpp_signal_generator" PUBLIC ${FFTW_INCLUDE_DIRS})
target_link_libraries("cpp_signal_generator" PRIVATE pybind11::module PkgConfig::FFTW OpenMP::OpenMP_CXX)


# Create your Python module
pybind11_add_module("interface_${NAME}" MODULE interface.cpp)
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "interface_${NAME}")
target_link_libraries("interface_${NAME}" PRIVATE pybind11::module PkgConfig::FFTW "cpp_signal_generator")
target_include_directories("interface_${NAME}" PRIVATE pybind11::module ${FFTW_INCLUDE_DIRS})


install(
    TARGETS cpp_${NAME} interface_${NAME}
    LIBRARY DESTINATION ${FLOWCYPY_BIN_DIR}
    ARCHIVE DESTINATION ${FLOWCYPY_BIN_DIR}
    RUNTIME DESTINATION ${FLOWCYPY_BIN_DIR}
)