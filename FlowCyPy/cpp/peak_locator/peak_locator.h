#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>

namespace py = pybind11;

class BasePeakLocator {
    public:
        bool compute_width;
        bool compute_area;
        std::vector<int> peak_indices;
        std::vector<double> peak_heights;
        std::vector<double> peak_widths;
        std::vector<double> peak_areas;

        // py::array get_indices_py() const {return to_array_int(this->peak_indices);}
        // py::array get_height_py() const {return to_array_double(this->peak_heights);}
        // py::array get_areas_py() const {return to_array_double(this->peak_areas);}
        // py::array get_widths_py() const {return to_array_double(this->peak_widths);}

        BasePeakLocator(bool compute_width, bool compute_area) : compute_width(compute_width), compute_area(compute_area) {}

        std::vector<double> get_metric_py(const std::string &metric_name){
            if (metric_name == "Index")
                return std::vector<double>(this->peak_indices.begin(), this->peak_indices.end());
            if (metric_name == "Height")
                return this->peak_heights;
            if (metric_name == "Width")
                return this->peak_widths;
            if (metric_name == "Area")
                return this->peak_areas;

            throw py::value_error(std::string("No valid metric chosen: ") + metric_name);
        }

        virtual ~BasePeakLocator(){};
};

class SlidingWindowPeakLocator : public BasePeakLocator {
    public:
        int window_size;
        int window_step;
        int max_number_of_peaks;
        int padding_value;
        double threshold;

        // If window_step is not provided (or provided as -1), default to window_size.
        SlidingWindowPeakLocator(
            int window_size,
            int window_step = -1,
            int max_number_of_peaks = 5,
            int padding_value = -1,
            bool compute_width = false,
            bool compute_area = false,
            double threshold = 0.5)
            :
                BasePeakLocator(compute_width, compute_area),
                window_size(window_size),
                max_number_of_peaks(max_number_of_peaks),
                padding_value(padding_value),
                threshold(threshold)
        {
            this->window_step = (window_step == -1) ? window_size : window_step;
        }

        void compute(const py::buffer array);
    };



// GlobalPeakLocator class that uses the PeakUtils helper functions.
class GlobalPeakLocator : public BasePeakLocator {
    public:
        int max_number_of_peaks;
        int padding_value;
        double threshold;

        /// Constructor.
        ///
        /// \param max_number_of_peaks Maximum number of peaks to report (only one peak is found here,
        ///                            so additional entries are padded).
        /// \param padding_value        Value used for padding indices when fewer peaks are detected.
        /// \param compute_width        If true, compute the peak's width (number of samples above threshold).
        /// \param compute_area         If true, compute the peak's area (sum of values above threshold).
        /// \param threshold            Fraction of the peak height used to determine boundaries.
        GlobalPeakLocator(
            int max_number_of_peaks = 1,
            int padding_value = -1,
            bool compute_width = false,
            bool compute_area = false,
            double threshold = 0.5)
            :
                BasePeakLocator(compute_width, compute_area),
                max_number_of_peaks(max_number_of_peaks),
                padding_value(padding_value),
                threshold(threshold)
        {}

        void compute(const py::buffer array);
    };


