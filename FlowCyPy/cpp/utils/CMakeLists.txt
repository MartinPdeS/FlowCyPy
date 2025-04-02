# cpp/utils/CMakeLists.txt

set(NAME "utils")



find_package(PkgConfig REQUIRED)
pkg_search_module(FFTW REQUIRED fftw3 IMPORTED_TARGET)
include_directories(PkgConfig::FFTW)
link_libraries(PkgConfig::FFTW)






find_package(FFTW3 REQUIRED)

message(STATUS "FFTW3_LIBRARIES = ${FFTW3_LIBRARIES}")
message(STATUS "FFTW3_INCLUDE_DIRS = ${FFTW3_INCLUDE_DIRS}")

if(NOT FFTW3_FOUND)
    message(FATAL_ERROR "FFTW3 not found. Please install FFTW3 or set CMAKE_PREFIX_PATH accordingly.")
endif()


# Create your library target
add_library("cpp_${NAME}" STATIC "${NAME}.cpp")

# Link with pybind11 module target
target_link_libraries("cpp_${NAME}" PRIVATE pybind11::module)

# Add include directories for FFTW3 to your targets
# target_include_directories("cpp_${NAME}" PRIVATE ${FFTW3_INCLUDE_DIRS})
# target_link_directories("cpp_${NAME}" PRIVATE ${FFTW3_LIBRARY_DIRS})
target_include_directories("cpp_${NAME}" PRIVATE PkgConfig::FFTW)
target_link_directories("cpp_${NAME}" PRIVATE PkgConfig::FFTW)

# Create your Python module
pybind11_add_module("interface_${NAME}" MODULE interface.cpp)
# target_link_directories("interface_${NAME}" PRIVATE ${FFTW3_LIBRARY_DIRS})
# set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "interface_${NAME}")
# target_link_libraries("interface_${NAME}" PRIVATE "cpp_${NAME}" ${FFTW3_LIBRARIES})
# target_include_directories("interface_${NAME}" PRIVATE ${FFTW3_INCLUDE_DIRS})
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "interface_${NAME}")
target_link_directories("interface_${NAME}" PRIVATE PkgConfig::FFTW)
target_link_libraries("interface_${NAME}" PRIVATE "cpp_${NAME}" PkgConfig::FFTW)
target_include_directories("interface_${NAME}" PRIVATE PkgConfig::FFTW)
