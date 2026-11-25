# PyMieSim/cpp/pint/CMakeLists.txt
set(NAME "pint")

add_library("${NAME}_lib" STATIC "${NAME}.cpp")
set_target_properties("${NAME}_lib" PROPERTIES OUTPUT_NAME "${NAME}")
target_link_libraries("${NAME}_lib" PUBLIC pybind11::pybind11)

pybind11_add_module("interface_${NAME}" MODULE interface.cpp)
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "interface_${NAME}")
target_link_libraries("interface_${NAME}" PUBLIC "${NAME}_lib" pybind11::module)

install(
    TARGETS "${NAME}_lib" "interface_${NAME}"
    LIBRARY DESTINATION "FlowCyPy"
    RUNTIME DESTINATION "FlowCyPy"
    ARCHIVE DESTINATION "FlowCyPy"
)
