pybind11_add_module(digital_processing_pipeline MODULE pipeline.cpp)
set_target_properties(digital_processing_pipeline PROPERTIES OUTPUT_NAME pipeline)
install(TARGETS digital_processing_pipeline
    LIBRARY DESTINATION "FlowCyPy/digital_processing"
    RUNTIME DESTINATION "FlowCyPy/digital_processing"
)
