# cpp/utils/CMakeLists.txt

set(NAME "utils")

# Find FFTW library
find_package(PkgConfig REQUIRED)
pkg_search_module(FFTW REQUIRED fftw3 IMPORTED_TARGET)
include_directories(PkgConfig::FFTW)

# Create your library target
add_library("cpp_${NAME}" STATIC "${NAME}.cpp")

# Link with pybind11 module target
target_link_libraries("cpp_${NAME}" PRIVATE pybind11::module)

# Add include directories for FFTW3 to your targets
target_include_directories("cpp_${NAME}" PUBLIC ${FFTW_INCLUDE_DIRS})
target_link_directories("cpp_${NAME}" PUBLIC PkgConfig::FFTW)
target_link_libraries("cpp_${NAME}" PUBLIC PkgConfig::FFTW)

# Create your Python  module
pybind11_add_module("interface_${NAME}" MODULE interface.cpp)
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "interface_${NAME}")
target_link_libraries("interface_${NAME}" PRIVATE "cpp_${NAME}")
