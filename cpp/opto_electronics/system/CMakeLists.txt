pybind11_add_module(opto_electronics_system MODULE system.cpp)
set_target_properties(opto_electronics_system PROPERTIES OUTPUT_NAME system)
install(TARGETS opto_electronics_system
    LIBRARY DESTINATION "FlowCyPy/opto_electronics"
    RUNTIME DESTINATION "FlowCyPy/opto_electronics"
)
