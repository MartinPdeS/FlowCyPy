# cpp/amplifier/CMakeLists.txt
set(NAME "amplifier")
set(LIB_NAME "${NAME}_lib")

add_library("${LIB_NAME}" STATIC "${NAME}.cpp")
target_include_directories("${LIB_NAME}" PUBLIC ${FFTW_INCLUDE_DIRS})
target_link_libraries("${LIB_NAME}" PUBLIC signal_generator_lib)

pybind11_add_module("${NAME}" MODULE interface.cpp)
set_target_properties("${NAME}" PROPERTIES OUTPUT_NAME "${NAME}")
target_link_libraries("${NAME}" PUBLIC pybind11::module "${LIB_NAME}" pint_lib)


install(
    TARGETS "${LIB_NAME}" "${NAME}"
    LIBRARY DESTINATION "FlowCyPy/opto_electronics"
    RUNTIME DESTINATION "FlowCyPy/opto_electronics"
    ARCHIVE DESTINATION "FlowCyPy/opto_electronics"
)
