#include <pybind11/pybind11.h>
#include <vector>
#include <limits>



struct PeakMetrics {
    double width;
    double area;
};


// Sorts a vector of PeakData in descending order by the peak's value.
struct PeakData {
    int index;
    double value;
    double width;  // Will be NaN if not computed.
    double area;   // Will be NaN if not computed.

    PeakData(int idx, double val, double w = std::numeric_limits<double>::quiet_NaN(), double a = std::numeric_limits<double>::quiet_NaN())
        : index(idx), value(val), width(w), area(a) {}
};

class BasePeakLocator {
    public:
        bool compute_width;
        bool compute_area;
        int padding_value;
        int max_number_of_peaks;
        std::vector<int> peak_indices;
        std::vector<double> peak_heights;
        std::vector<double> peak_widths;
        std::vector<double> peak_areas;

        /**
         * \brief Constructor for BasePeakLocator.
         * \param compute_width        If true, compute the peak's width (number of samples above threshold).
         * \param compute_area         If true, compute the peak's area (sum of values above threshold).
         * \param padding_value        Value used for padding indices when fewer peaks are detected.
         * \param max_number_of_peaks  Maximum number of peaks to report.
         * \details This constructor initializes the BasePeakLocator with the specified parameters.
         */
        BasePeakLocator(bool compute_width, bool compute_area, int padding_value, int max_number_of_peaks);

        /**
         * \brief Get the specified metric as a Python list.
         * \param metric_name Name of the metric to retrieve (e.g., "Index", "Height", "Width", "Area").
         * \return A vector of doubles representing the requested metric.
         * \throws py::value_error if the metric name is invalid.
         * \details This function retrieves the specified metric from the peak locator's data.
         */
        std::vector<double> get_metric_py(const std::string &metric_name);

        /**
         * \brief Virtual destructor for BasePeakLocator.
         * \details Ensures proper cleanup of derived classes.
         */
        virtual ~BasePeakLocator(){};

        /**
         * \brief Sorts the peaks in descending order based on their values.
         * \param peaks A vector of PeakData objects representing the detected peaks.
         * \details This function sorts the peaks in place, modifying the input vector.
         */
        void sort_peaks_descending(std::vector<PeakData>& peaks);

        /**
         * \brief Finds the index of the local maximum in the given window.
         * \param ptr Pointer to the data array.
         * \param start Start index of the window.
         * \param end End index of the window.
         * \return The index of the local maximum within the specified window.
         */
        size_t find_local_peak(const double* ptr, size_t start, size_t end);

        /**
         * \brief Computes the metrics for a segment around a detected peak.
         * \param ptr Pointer to the data array.
         * \param start Start index of the segment.
         * \param end End index of the segment.
         * \param peak_index Index of the peak in the segment.
         * \param threshold Fraction of the peak height used to determine boundaries.
         * \return A PeakMetrics object containing the computed width and area.
         */
        PeakMetrics compute_segment_metrics(const double* ptr, size_t start, size_t end, size_t peak_index, double threshold);

        /**
         * \brief Computes the left and right boundaries for a peak given a threshold.
         * \param ptr Pointer to the data array.
         * \param start Start index of the segment.
         * \param end End index of the segment.
         * \param peak_index Index of the peak in the segment.
         * \param threshold Fraction of the peak height used to determine boundaries.
         * \param left_boundary Output parameter for the left boundary index.
         * \param right_boundary Output parameter for the right boundary index.
         * \details This function finds the boundaries where the signal drops below the specified threshold
         *          relative to the peak value.
         */
        void compute_boundaries(const double* ptr, size_t start, size_t end, size_t peak_index, double threshold, size_t &left_boundary, size_t &right_boundary);
        /**
         * \brief Sorts the peaks in descending order based on their heights.
         * \param peaks A vector of pairs where each pair contains the peak index and its height.
         * \details This function sorts the peaks in place, modifying the input vector.
         */
        void sort_peaks_descending(std::vector<std::pair<int, double>>& peaks);

        /**
         * \brief Pads the peak indices and heights to a fixed size.
         * \param peaks A vector of pairs where each pair contains the peak index and its height.
         * \param max_number_of_peaks The maximum number of peaks to report.
         * \param padding_value The value to use for padding.
         * \param pad_index Output vector for padded peak indices.
         * \param pad_height Output vector for padded peak heights.
         * \details This function fills the output vectors with the peak data, using the padding value
         *          for any unused entries.
         */
        void pad_peaks(const std::vector<std::pair<int, double>>& peaks, size_t max_number_of_peaks, int padding_value, std::vector<int>& pad_index, std::vector<double>& pad_height);

};

class SlidingWindowPeakLocator : public BasePeakLocator {
    public:
        int window_size;
        int window_step;
        double threshold;

        /**
         * \brief Constructor for SlidingWindowPeakLocator.
         * \param window_size          Size of the sliding window to analyze.
         * \param window_step          Step size for sliding the window (default is -1, which means equal to window_size).
         * \param max_number_of_peaks  Maximum number of peaks to report (default is 5).
         * \param padding_value        Value used for padding indices when fewer peaks are detected (default is -1).
         * \param compute_width        If true, compute the peak's width (number of samples above threshold).
         * \param compute_area         If true, compute the peak's area (sum of values above threshold).
         * \param threshold            Fraction of the peak height used to determine boundaries (default is 0.5).
         * \details This constructor initializes the SlidingWindowPeakLocator with the specified parameters.
         *          The window_step defaults to the window_size if not specified.
         *          The padding_value is used to fill the peak indices, heights, widths, and
         */
        SlidingWindowPeakLocator(int window_size, int window_step = -1, int max_number_of_peaks = 5, int padding_value = -1, bool compute_width = false, bool compute_area = false, double threshold = 0.5);

        /**
         * \brief Computes the peak indices, heights, widths, and areas from the provided signal.
         * \param array A 1D vector of doubles representing the signal.
         * \throws std::runtime_error if the input array is not 1D.
         * \details This function processes the signal in sliding windows, finds local peaks,
         *          and computes their metrics based on the specified parameters.
         */
        void compute(const std::vector<double> &array);
    };



// GlobalPeakLocator class that uses the PeakUtils helper functions.
class GlobalPeakLocator : public BasePeakLocator {
    public:
        double threshold;

        /// Constructor.
        ///
        /// \param max_number_of_peaks Maximum number of peaks to report (only one peak is found here,
        ///                            so additional entries are padded).
        /// \param padding_value        Value used for padding indices when fewer peaks are detected.
        /// \param compute_width        If true, compute the peak's width (number of samples above threshold).
        /// \param compute_area         If true, compute the peak's area (sum of values above threshold).
        /// \param threshold            Fraction of the peak height used to determine boundaries.
        GlobalPeakLocator(int max_number_of_peaks = 1, int padding_value = -1, bool compute_width = false, bool compute_area = false, double threshold = 0.5);


        /**
         * \brief Computes the peak indices, heights, widths, and areas from the provided signal.
         * \param array A 1D vector of doubles representing the signal.
         * \throws std::runtime_error if the input array is not 1D.
         * \details This function processes the signal in sliding windows, finds local peaks,
         *          and computes their metrics based on the specified parameters.
         */
        void compute(const std::vector<double> &array);
    };
