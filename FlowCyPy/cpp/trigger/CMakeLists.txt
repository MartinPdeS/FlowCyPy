# cpp/triggering_system/CMakeLists.txt
set(NAME "trigger")

# --- C++ static library -------------------------------------------------
add_library("core_${NAME}" STATIC "${NAME}.cpp")
target_link_libraries("core_${NAME}" PRIVATE)

# --- Install -------------------------------------------------------------
install(
    TARGETS core_${NAME}
    LIBRARY DESTINATION ${LOCAL_BIN_DIR}
    ARCHIVE DESTINATION ${LOCAL_BIN_DIR}
    RUNTIME DESTINATION ${LOCAL_BIN_DIR}
)
