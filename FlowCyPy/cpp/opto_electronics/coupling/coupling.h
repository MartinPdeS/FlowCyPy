#pragma once

#include <vector>
#include "scatterer/sphere/sphere.h"
#include "sets/scatterer.h"
#include "sets/source.h"
#include "sets/detector.h"

class ScatteringSimulator {
    public:

        std::vector<double> process_scattering(const GaussianSourceSet& source_set, const SphereSet& scatterer_set, const DetectorSet& detector_set) {
            // Implementation of the coupling processing logic goes here

            std::vector<size_t> array_shape = {source_set.wavelength.size()};
            size_t full_size = source_set.wavelength.size();
            scatterer_set.validate_sequential_data(full_size);
            source_set.validate_sequential_data(full_size);
            detector_set.validate_sequential_data(full_size);

            std::vector<double> output_array(full_size);

            #pragma omp parallel for
            for (size_t idx = 0; idx < full_size; ++idx) {

                BaseSource source = source_set.get_source_by_index_sequential(idx);

                std::unique_ptr<BaseScatterer> scatterer_ptr = scatterer_set.get_scatterer_ptr_by_index_sequential(idx, source);

                Detector detector = detector_set.get_detector_by_index_sequential(idx);

                detector.medium_refractive_index = scatterer_ptr->medium_refractive_index;

                output_array[idx] = detector.get_coupling(*scatterer_ptr);
            }

            return output_array;
        }

        std::vector<double> process_fluorescence(const GaussianSourceSet& source_set, const SphereSet& scatterer_set, const DetectorSet& detector_set) {
            // Implementation of the coupling processing logic goes here

            std::vector<size_t> array_shape = {source_set.wavelength.size()};
            size_t full_size = source_set.wavelength.size();
            scatterer_set.validate_sequential_data(full_size);
            source_set.validate_sequential_data(full_size);
            detector_set.validate_sequential_data(full_size);

            std::vector<double> output_array(full_size);

            #pragma omp parallel for
            for (size_t idx = 0; idx < full_size; ++idx) {

                BaseSource source = source_set.get_source_by_index_sequential(idx);

                std::unique_ptr<BaseScatterer> scatterer_ptr = scatterer_set.get_scatterer_ptr_by_index_sequential(idx, source);

                Detector detector = detector_set.get_detector_by_index_sequential(idx);

                detector.medium_refractive_index = scatterer_ptr->medium_refractive_index;

                output_array[idx] = 1.0;
            }

            return output_array;

        }
};
