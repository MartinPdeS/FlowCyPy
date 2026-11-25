pybind11_add_module(fluidics_system MODULE system.cpp)
set_target_properties(fluidics_system PROPERTIES OUTPUT_NAME system)
target_link_libraries(fluidics_system PRIVATE flow_cell_lib population_events_lib)
install(TARGETS fluidics_system
    LIBRARY DESTINATION "FlowCyPy/fluidics"
    RUNTIME DESTINATION "FlowCyPy/fluidics"
)
