include_directories("${CMAKE_CURRENT_SOURCE_DIR}")

add_subdirectory(utils)
add_subdirectory(pint)

add_subdirectory(fluidics/distributions)
add_subdirectory(fluidics/populations)
add_subdirectory(fluidics/scatterer_collection)
add_subdirectory(fluidics/flow_cell)
add_subdirectory(fluidics/population_events)
add_subdirectory(fluidics/system)

add_subdirectory(opto_electronics/source)
add_subdirectory(opto_electronics/detector)
add_subdirectory(opto_electronics/amplifier)
add_subdirectory(opto_electronics/coupling)
add_subdirectory(opto_electronics/digitizer)
add_subdirectory(opto_electronics/circuits)
add_subdirectory(opto_electronics/system)

add_subdirectory(digital_processing/discriminator)
add_subdirectory(digital_processing/peak_locator)
add_subdirectory(digital_processing/classifier)
add_subdirectory(digital_processing/pipeline)
