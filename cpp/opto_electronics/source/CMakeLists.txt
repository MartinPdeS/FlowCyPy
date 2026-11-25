# cpp/source/CMakeLists.txt
set(NAME "source")
set(LIB_NAME "${NAME}_lib")

add_library("${LIB_NAME}" STATIC "${NAME}.cpp")
target_link_libraries("${LIB_NAME}" PUBLIC OpenMP::OpenMP_CXX)
target_link_libraries("${LIB_NAME}" PUBLIC flowcypy_openmp)
target_include_directories("${LIB_NAME}" PUBLIC ${OpenMP_CXX_INCLUDE_DIRS})


pybind11_add_module("${NAME}" MODULE interface.cpp)
set_target_properties("${NAME}" PROPERTIES OUTPUT_NAME "${NAME}")
target_link_libraries("${NAME}" PUBLIC pybind11::module "${LIB_NAME}" pint_lib flowcypy_openmp)

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
    TARGETS "${LIB_NAME}" "${NAME}"
    LIBRARY DESTINATION "FlowCyPy/opto_electronics"
    RUNTIME DESTINATION "FlowCyPy/opto_electronics"
    ARCHIVE DESTINATION "FlowCyPy/opto_electronics"
)
