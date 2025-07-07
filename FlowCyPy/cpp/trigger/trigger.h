#pragma once

#include <vector>
#include <string>
#include <map>

// Represents a single trigger event, including its source signal and extracted segments.
struct Trigger {
    std::map<std::string, std::vector<double>> signal_map; // Map of signal names to their data


    // Output vectors filled after processing:
    std::map<std::string, std::vector<double>> signal_segments;
    std::vector<double> global_time; // Global time vector used for all signal operations
    std::vector<double> time_out;      // Time stamps corresponding to each segment sample
    std::vector<int> segment_ids_out;  // Mapping of sample indices to segment IDs

    Trigger() = default;


    void clear() {
        // signal_map.clear();
        signal_segments.clear();
        // global_time.clear();
        time_out.clear();
        segment_ids_out.clear();
    }

    /**
     * @brief Add a signal to the trigger system.
     * @param signal_name Name of the signal to add.
     * @param signal_data 1D vector of signal values.
     * This adds a new signal to the trigger system, which can be processed later.
     */
    void add_signal(const std::string &signal_name, const std::vector<double> &signal_data);

    /**
     * @brief Add a global time axis for subsequent signal additions.
     * @param time 1D vector of time values.
     * This sets the global time axis used for all signals in this trigger system.
     * The time stamps must be monotonically increasing and match the length of any signals added.
     */
    void add_time(const std::vector<double> &time);

    /**
     * @brief Get the segmented signal for a specific detector.
     * @param detector_name Name of the detector whose segments to retrieve.
     * @return vector<double> Extracted signal segments for the specified detector.
     * This will return the segments that were extracted based on valid trigger indices.
     */
    std::vector<double>& get_segmented_signal(const std::string &detector_name);

    /**
     * @brief Run segmentation based on valid trigger indices.
     * @param valid_triggers Vector of (start, end) indices for each trigger.
     * This populates `signal_segments`, `time_out`, and `segment_ids_out` with the
     * corresponding segments, time stamps, and segment IDs for each trigger segment.
     */
    void run_segmentation(const std::vector<std::pair<int, int>> &valid_triggers);

    /**
     * @brief Extract signal segments based on valid trigger indices.
     * @param detector_name Name of the detector whose signal segments to extract.
     * @param signal Vector of signal values for the detector.
     * @param valid_triggers Vector of (start, end) indices for each trigger.
     * This populates `signal_segments` with the extracted segments for the specified detector.
     * The segments are extracted based on the provided start and end indices,
     * ensuring they align with the global time axis.
     */
    void extract_signal_segments(const std::string &detector_name, const std::vector<double> &signal, const std::vector<std::pair<int, int>> &valid_triggers);

    /**
     * @brief Extract time and segment ID information from valid triggers.
     * @param valid_triggers Vector of (start, end) indices for each trigger.
     * This populates `time_out` and `segment_ids_out` with the corresponding time stamps
     * and segment IDs for each trigger segment.
     * The time stamps are aligned with the global time axis.
     */
    void extract_time_and_id(const std::vector<std::pair<int, int>> &valid_triggers);
};