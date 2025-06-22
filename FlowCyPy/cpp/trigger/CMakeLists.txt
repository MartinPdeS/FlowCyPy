# cpp/triggering_system/CMakeLists.txt
set(NAME "trigger")

# Create your library target
add_library("cpp_${NAME}" STATIC "${NAME}.cpp")
target_link_libraries("cpp_${NAME}" PRIVATE)


install(
    TARGETS cpp_${NAME}
    LIBRARY DESTINATION ${LOCAL_BIN_DIR}
    ARCHIVE DESTINATION ${LOCAL_BIN_DIR}
    RUNTIME DESTINATION ${LOCAL_BIN_DIR}
)