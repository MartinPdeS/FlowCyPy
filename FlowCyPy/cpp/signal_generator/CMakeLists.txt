# cpp/signal_generator/CMakeLists.txt
set(NAME "signal_generator")


# Find FFTW library
find_package(PkgConfig REQUIRED)
pkg_search_module(FFTW REQUIRED fftw3 IMPORTED_TARGET)
include_directories(PkgConfig::FFTW)

# Create your library target
add_library("cpp_${NAME}" STATIC "${NAME}.cpp")

# Link with pybind11 module target
target_link_libraries("cpp_${NAME}" PRIVATE pybind11::module)
target_include_directories("cpp_${NAME}" PUBLIC ${FFTW_INCLUDE_DIRS})
target_link_libraries("cpp_${NAME}" PUBLIC PkgConfig::FFTW)



# Create your Python module
pybind11_add_module("interface_${NAME}" MODULE interface.cpp)
target_link_libraries("interface_${NAME}" PRIVATE pybind11::module "cpp_${NAME}")
target_include_directories("interface_${NAME}" PRIVATE pybind11::module)
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "interface_${NAME}")
