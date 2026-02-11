set(NAME "signal_generator")

# --- C++ static library -------------------------------------------------
add_library("${NAME}" STATIC "signal_generator.cpp")
set_target_properties("${NAME}" PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_include_directories("${NAME}" PUBLIC ${FFTW_INCLUDE_DIRS})
target_link_libraries("${NAME}" PUBLIC  OpenMP::OpenMP_CXX PRIVATE pybind11::module PkgConfig::FFTW utils pint)
set_target_properties("${NAME}" PROPERTIES OUTPUT_NAME "${NAME}")

# --- Python extension module --------------------------------------------
pybind11_add_module("interface_${NAME}" MODULE interface.cpp)
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "interface_${NAME}")
target_include_directories("interface_${NAME}" PRIVATE ${FFTW_INCLUDE_DIRS})
target_link_libraries("interface_${NAME}" PRIVATE pybind11::module PkgConfig::FFTW "${NAME}")
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "${NAME}")

# --- macOS: use shared Homebrew libomp, not a vendored copy -------------
if(APPLE)
    if(DEFINED ENV{HOMEBREW_PREFIX}) # where Homebrew normally installs libomp
        set(_omp_root "$ENV{HOMEBREW_PREFIX}/opt/libomp")
    else() # default on GitHub macOS runners
        set(_omp_root "/opt/homebrew/opt/libomp")
    endif()

    set_target_properties("interface_${NAME}" PROPERTIES BUILD_RPATH   "${_omp_root}/lib" INSTALL_RPATH "${_omp_root}/lib")
endif()

# --- Install -------------------------------------------------------------
set_property(GLOBAL APPEND PROPERTY FLOWCYPY_TARGETS "${NAME}" "interface_${NAME}")
