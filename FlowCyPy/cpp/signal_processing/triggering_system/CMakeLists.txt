# cpp/triggering_system/CMakeLists.txt
set(NAME "triggering_system")
set(LIB_NAME "${NAME}_lib")

add_library("${LIB_NAME}" STATIC "${NAME}.cpp")
target_link_libraries("${LIB_NAME}" PRIVATE pybind11::module trigger_lib)

pybind11_add_module("interface_${NAME}" MODULE interface.cpp)
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "_${NAME}")
target_link_libraries("interface_${NAME}" PUBLIC pybind11::module "${LIB_NAME}" pint_lib)

install(
    TARGETS "${LIB_NAME}" "interface_${NAME}"
    LIBRARY DESTINATION "FlowCyPy/signal_processing"
    RUNTIME DESTINATION "FlowCyPy/signal_processing"
    ARCHIVE DESTINATION "FlowCyPy/signal_processing"
)
