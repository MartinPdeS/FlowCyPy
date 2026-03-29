# cpp/coupling/CMakeLists.txt

set(NAME "coupling")

# Create your library target
add_library("${NAME}" STATIC "${NAME}.cpp")

# Link with pybind11 module target
target_link_libraries("${NAME}" PRIVATE pybind11::module)

# Create your Python module
pybind11_add_module("interface_${NAME}" MODULE interface.cpp)
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "interface_${NAME}")
target_link_libraries("interface_${NAME}" PRIVATE "${NAME}")


set(PYMIESIM_REPO_PATH "/Users/m.poinsinetdesivry-houle/Desktop/GitRepositories/PyMieSim/")

add_subdirectory(/Users/m.poinsinetdesivry-houle/Desktop/GitRepositories/PyMieSim/ external_pymiesim)

target_include_directories(${NAME} PUBLIC ${PYMIESIM_REPO_PATH}/PyMieSim/cpp)

target_link_libraries(${NAME} PUBLIC sphere)

set_property(GLOBAL APPEND PROPERTY FLOWCYPY_TARGETS "${NAME}" "interface_${NAME}")
