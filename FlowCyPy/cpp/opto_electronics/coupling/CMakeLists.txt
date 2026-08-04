set(NAME "coupling_model")
set(LIB_NAME "${NAME}_lib")

add_library("${LIB_NAME}" STATIC coupling.cpp)
target_link_libraries("${LIB_NAME}" PUBLIC pybind11::module)

pybind11_add_module("interface_${NAME}" MODULE interface.cpp)
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "${NAME}")
target_link_libraries("interface_${NAME}" PUBLIC pybind11::module "${LIB_NAME}")

install(
    TARGETS "${LIB_NAME}" "interface_${NAME}"
    LIBRARY DESTINATION "FlowCyPy/opto_electronics"
    RUNTIME DESTINATION "FlowCyPy/opto_electronics"
    ARCHIVE DESTINATION "FlowCyPy/opto_electronics"
)
