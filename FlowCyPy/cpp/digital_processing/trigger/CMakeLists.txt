# cpp/trigger/CMakeLists.txt
set(NAME "trigger")
set(LIB_NAME "${NAME}_lib")

add_library("${LIB_NAME}" STATIC "${NAME}.cpp")


install(
    TARGETS "${LIB_NAME}"
    LIBRARY DESTINATION "FlowCyPy/digital_processing"
    RUNTIME DESTINATION "FlowCyPy/digital_processing"
    ARCHIVE DESTINATION "FlowCyPy/digital_processing"
)
