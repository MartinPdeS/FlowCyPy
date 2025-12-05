# cpp/triggering_system/CMakeLists.txt
set(NAME "trigger")

# --- C++ static library -------------------------------------------------
add_library("${NAME}" STATIC "${NAME}.cpp")
target_link_libraries("${NAME}" PRIVATE)

# --- Install -------------------------------------------------------------
set_property(GLOBAL APPEND PROPERTY FLOWCYPY_TARGETS "${NAME}")
