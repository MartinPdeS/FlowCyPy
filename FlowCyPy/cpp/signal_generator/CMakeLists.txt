set(NAME "signal_generator")

# --- C++ static library -------------------------------------------------
add_library("cpp_${NAME}" STATIC "signal_generator.cpp")
# make sure it’s PIC so it can be linked into a Python module
set_target_properties("cpp_${NAME}" PROPERTIES POSITION_INDEPENDENT_CODE ON)

target_include_directories("cpp_${NAME}" PUBLIC ${FFTW_INCLUDE_DIRS})

# OpenMP is PUBLIC here so the module inherits it
target_link_libraries("cpp_${NAME}"
    PUBLIC  OpenMP::OpenMP_CXX
    PRIVATE pybind11::module PkgConfig::FFTW cpp_utils
)

# --- Python extension module --------------------------------------------
pybind11_add_module("interface_${NAME}" MODULE interface.cpp)
set_target_properties("interface_${NAME}" PROPERTIES OUTPUT_NAME "interface_${NAME}")

target_include_directories("interface_${NAME}" PRIVATE ${FFTW_INCLUDE_DIRS})

# the module links against the static lib (and therefore OpenMP)
target_link_libraries("interface_${NAME}"
    PRIVATE pybind11::module PkgConfig::FFTW "cpp_${NAME}"
)

# --- macOS: use shared Homebrew libomp, not a vendored copy -------------
if(APPLE)
    # where Homebrew normally installs libomp
    if(DEFINED ENV{HOMEBREW_PREFIX})
        set(_omp_root "$ENV{HOMEBREW_PREFIX}/opt/libomp")
    else()
        # default on GitHub macOS runners
        set(_omp_root "/opt/homebrew/opt/libomp")
    endif()

    # tell the module where to find libomp at runtime
    set_target_properties("interface_${NAME}" PROPERTIES
        BUILD_RPATH   "${_omp_root}/lib"
        INSTALL_RPATH "${_omp_root}/lib"
    )
endif()

# --- Install -------------------------------------------------------------
install(
    TARGETS cpp_${NAME} interface_${NAME}
    LIBRARY DESTINATION ${LOCAL_BIN_DIR}
    ARCHIVE DESTINATION ${LOCAL_BIN_DIR}
    RUNTIME DESTINATION ${LOCAL_BIN_DIR}
)
