# Find FFTW library
find_package(OpenMP REQUIRED)
find_package(PkgConfig REQUIRED)
pkg_search_module(FFTW REQUIRED fftw3 IMPORTED_TARGET)



add_library("cpp_signal_generator" STATIC "signal_generator.cpp")
target_include_directories("cpp_signal_generator" PUBLIC ${FFTW_INCLUDE_DIRS})
target_link_libraries("cpp_signal_generator" PRIVATE pybind11::module PkgConfig::FFTW OpenMP::OpenMP_CXX)




# Create your Python module
pybind11_add_module("interface_signal_generator" MODULE interface.cpp)
target_link_libraries("interface_signal_generator" PRIVATE pybind11::module PkgConfig::FFTW "cpp_signal_generator")
target_include_directories("interface_signal_generator" PRIVATE pybind11::module ${FFTW_INCLUDE_DIRS})
set_target_properties("interface_signal_generator" PROPERTIES OUTPUT_NAME "interface_signal_generator")
