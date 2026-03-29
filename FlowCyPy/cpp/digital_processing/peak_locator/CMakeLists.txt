# cpp/peak_locator/CMakeLists.txt
set(NAME "peak_locator")
set(LIB_NAME "${NAME}_lib")

add_library("${LIB_NAME}" STATIC "${NAME}.cpp")
target_link_libraries("${LIB_NAME}" PUBLIC pybind11::module flowcypy_openmp)

pybind11_add_module("interface_${NAME}" MODULE interface.cpp)
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "${NAME}")
target_link_libraries("interface_${NAME}" PUBLIC pybind11::module "${LIB_NAME}" pint_lib)

# --- macOS: use shared Homebrew libomp, not a vendored copy -------------
if(APPLE)
    if(DEFINED ENV{HOMEBREW_PREFIX}) # where Homebrew normally installs libomp
        set(_omp_root "$ENV{HOMEBREW_PREFIX}/opt/libomp")
    else() # default on GitHub macOS runners
        set(_omp_root "/opt/homebrew/opt/libomp")
    endif()

    set_target_properties("${LIB_NAME}" PROPERTIES BUILD_RPATH "${_omp_root}/lib" INSTALL_RPATH "${_omp_root}/lib")
endif()

install(
    TARGETS "${LIB_NAME}" "interface_${NAME}"
    LIBRARY DESTINATION "FlowCyPy/digital_processing"
    RUNTIME DESTINATION "FlowCyPy/digital_processing"
    ARCHIVE DESTINATION "FlowCyPy/digital_processing"
)
