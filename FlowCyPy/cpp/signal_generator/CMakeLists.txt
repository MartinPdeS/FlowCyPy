set(NAME "signal_generator")

# --- C++ static library -------------------------------------------------
add_library("core_${NAME}" STATIC "signal_generator.cpp")
set_target_properties("core_${NAME}" PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_include_directories("core_${NAME}" PUBLIC ${FFTW_INCLUDE_DIRS})
target_link_libraries("core_${NAME}" PUBLIC  OpenMP::OpenMP_CXX PRIVATE pybind11::module PkgConfig::FFTW core_utils)
set_target_properties("core_${NAME}" PROPERTIES OUTPUT_NAME "${NAME}")

# --- Python extension module --------------------------------------------
pybind11_add_module("interface_${NAME}" MODULE interface.cpp)
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "interface_${NAME}")
target_include_directories("interface_${NAME}" PRIVATE ${FFTW_INCLUDE_DIRS})
target_link_libraries("interface_${NAME}" PRIVATE pybind11::module PkgConfig::FFTW "core_${NAME}")
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
install(
    TARGETS core_${NAME} interface_${NAME}
    LIBRARY DESTINATION ${LOCAL_BIN_DIR}
    ARCHIVE DESTINATION ${LOCAL_BIN_DIR}
    RUNTIME DESTINATION ${LOCAL_BIN_DIR}
)
