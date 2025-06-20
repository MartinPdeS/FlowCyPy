#include <vector>
#include <string>


// Represents a single trigger event, including its source signal and extracted segments.
struct Trigger {
    const std::string detector_name;   // Identifier for this detector's signal
    const std::vector<double> signal;  // Raw input signal buffer from Python

    // Output vectors filled after processing:
    std::vector<double> time_out;      // Time stamps corresponding to each segment sample
    std::vector<double> signal_out;    // Signal values extracted for each segment
    std::vector<int> segment_ids_out;  // Mapping of sample indices to segment IDs

    double* buffer_ptr;                // Direct pointer into the signal buffer
    size_t buffer_size;                // Number of samples in the input signal

    // Construct from a detector name and Python buffer. Initializes pointers for fast access.
    Trigger(const std::string &detector_name, const std::vector<double> &signal) : detector_name(detector_name), signal(signal)
    {
        buffer_ptr = const_cast<double*>(signal.data());
        buffer_size = signal.size();
    }
};