#include "triggering_system.h"



// ------------- BaseTrigger class implementation-------------//
void BaseTrigger::add_time(const std::vector<double> &time) {
    if (time.empty())
        throw std::runtime_error("Time arrays must be 1D");

    this->trigger.add_time(time);
}

void BaseTrigger::add_signal(const std::string &detector_name, const std::vector<double> &signal) {
     if (signal.empty())
        throw std::runtime_error("Signal arrays must be 1D");

    this->trigger.add_signal(detector_name, signal);
}

void BaseTrigger::validate_detector_existence(const std::string &detector_name) const
{
    if(this->trigger.signal_map.find(detector_name) == this->trigger.signal_map.end())
        std::runtime_error("Trigger detector not found in signal map.");
}




// ------------- FixedWindow class implementation-------------//
void FixedWindow::run(const double threshold) {
    this->trigger.clear();
    if (this->trigger.global_time.empty())
        throw pybind11::value_error("Global time axis must be set before running triggers");

    if (trigger_detector_name.empty())
        throw pybind11::value_error("Trigger detector name must be set before running triggers");

    const std::vector<double> &signal = this->trigger.signal_map.at(this->trigger_detector_name);


    std::vector<std::pair<int, int>> valid_triggers;

    std::vector<int> trigger_indices;
    for (size_t i = 1; i < signal.size(); ++i)
        if (signal[i - 1] <= threshold && signal[i] > threshold)
            trigger_indices.push_back(i - 1);

    int last_end = -1;
    for (int idx : trigger_indices) {
        int start = idx - this->pre_buffer - 1;

        int end = idx + this->post_buffer;

        if (start < 0 || end >= static_cast<int>(signal.size()))
            continue;

        if (start > last_end) {
            valid_triggers.emplace_back(start, end);
            last_end = end;
        }

        if (this->max_triggers > 0 && valid_triggers.size() >= static_cast<size_t>(this->max_triggers))
            break;
    }

    this->trigger.run_segmentation(valid_triggers);
}


// ------------- DynamicWindow class implementation-------------//
void DynamicWindow::run(const double threshold) {
    this->trigger.clear();

    if (this->trigger.global_time.empty())
        throw pybind11::value_error("Global time axis must be set before running triggers");


    if (trigger_detector_name.empty())
        throw pybind11::value_error("Trigger detector name must be set before running triggers");

    const std::vector<double> &signal = this->trigger.signal_map.at(this->trigger_detector_name);

    std::vector<std::pair<int, int>> valid_triggers;

    int last_end = -1;
    for (size_t i = 1; i < signal.size(); ++i) {
        if (signal[i - 1] <= threshold && signal[i] > threshold) {
            int start = static_cast<int>(i) - this->pre_buffer;

            if (start < 0)
                start = 0;

            size_t j = i;

            while (j < signal.size() && signal[j] > threshold)
                j++;
            int end = static_cast<int>(j) - 1 + this->post_buffer;


            if (end >= static_cast<int>(signal.size()))
                end = static_cast<int>(signal.size()) - 1;

            if (start > last_end) {
                valid_triggers.emplace_back(start, end);
                last_end = end;
            }

            if (this->max_triggers > 0 && valid_triggers.size() >= static_cast<size_t>(this->max_triggers))
                break;

            i = j;
        }
    }

    this->trigger.run_segmentation(valid_triggers);
}


// ------------- DoubleThreshold class implementation-------------//
void DoubleThreshold::run(const double threshold, const double lower_threshold, const bool debounce_enabled, const int min_window_duration) {
    this->trigger.clear();

    if (this->trigger.global_time.empty())
        throw pybind11::value_error("Global time axis must be set before running triggers");

    if (trigger_detector_name.empty())
        throw pybind11::value_error("Trigger detector name must be set before running triggers");

    const std::vector<double> &signal = this->trigger.signal_map.at(this->trigger_detector_name);

    std::vector<std::pair<int, int>> valid_triggers;

    double _lower_threshold;
    if (std::isnan(lower_threshold))
        _lower_threshold = threshold;
    else
        _lower_threshold = lower_threshold;

    int last_end = -1;
    for (size_t i = 1; i < signal.size(); ++i) {
        if (signal[i - 1] <= threshold && signal[i] > threshold) {
            size_t j = i;
            if (debounce_enabled && min_window_duration != -1) {
                size_t count = 0;
                while (j < signal.size() && signal[j] > threshold) {
                    ++count;
                    ++j;
                    if (count >= static_cast<size_t>(min_window_duration))
                        break;
                }
                if (count < static_cast<size_t>(min_window_duration)) {
                    i = j;
                    continue;
                }
            } else {
                while (j < signal.size() && signal[j] > threshold)
                    ++j;
            }
            int start = static_cast<int>(i) - this->pre_buffer;

            if (start < 0)
                start = 0;

            size_t k = j;

            while (k < signal.size() && signal[k] > _lower_threshold)
                ++k;

            int end = static_cast<int>(k) - 1 + this->post_buffer;

            if (end >= static_cast<int>(signal.size()))
                end = static_cast<int>(signal.size()) - 1;

            if (start > last_end) {
                valid_triggers.emplace_back(start, end);
                last_end = end;
            }

            if (this->max_triggers > 0 && valid_triggers.size() >= static_cast<size_t>(this->max_triggers))
                break;

            i = k;
        }
    }

    this->trigger.run_segmentation(valid_triggers);
}

