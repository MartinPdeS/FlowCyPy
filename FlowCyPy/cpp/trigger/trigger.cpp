#include "trigger.h"

void Trigger::add_signal(const std::string &signal_name, const std::vector<double> &signal_data) {
    signal_map[signal_name] = signal_data;
}

void Trigger::add_time(const std::vector<double> &time) {
    this->global_time = time;
}


std::vector<double>& Trigger::get_segmented_signal(const std::string &detector_name) {
    return this->signal_segments[detector_name];
}

void Trigger::run_segmentation(const std::vector<std::pair<int, int>> &valid_triggers) {
    if (valid_triggers.empty())
        return ;

    this->extract_time_and_id(valid_triggers);

    for (auto const& [detector_name, signal] : this->signal_map)
        this->extract_signal_segments(detector_name, signal, valid_triggers);

}


void Trigger::extract_signal_segments(const std::string &detector_name, const std::vector<double> &signal, const std::vector<std::pair<int, int>> &valid_triggers) {
    std::vector<double> signal_segment;

    for (const auto &[start, end] : valid_triggers) {
        for (int i = start; i <= end; ++i) {

            if (i >= static_cast<int>(this->global_time.size()))
                break;

            signal_segment.push_back(signal[i]);
        }
    }

    this->signal_segments[detector_name] = signal_segment;
}


void Trigger::extract_time_and_id(const std::vector<std::pair<int, int>> &valid_triggers) {

    size_t segment_id = 0;
    for (const auto &[start, end] : valid_triggers) {
        for (int i = start; i <= end; ++i) {

            if (i >= static_cast<int>(this->global_time.size()))
                break;

            this->time_out.push_back(this->global_time[i]);
            this->segment_ids_out.push_back(segment_id);
        }
        segment_id++;
    }
}
