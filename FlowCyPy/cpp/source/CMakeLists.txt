set(NAME "source")

# --- C++ static library -------------------------------------------------
add_library("${NAME}" STATIC "source.cpp")
set_target_properties("${NAME}" PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_include_directories("${NAME}" PUBLIC ${FFTW_INCLUDE_DIRS})
target_link_libraries("${NAME}" PUBLIC  PRIVATE)
set_target_properties("${NAME}" PROPERTIES OUTPUT_NAME "${NAME}")

# --- Python extension module --------------------------------------------
pybind11_add_module("interface_${NAME}" MODULE interface.cpp)
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "interface_${NAME}")
target_include_directories("interface_${NAME}" PRIVATE ${FFTW_INCLUDE_DIRS})
target_link_libraries("interface_${NAME}" PRIVATE pybind11::module "${NAME}")
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "${NAME}")
