#include "triggering_system.h"





// ------------- BaseTrigger class implementation-------------//
void BaseTrigger::add_time(const std::vector<double> &time) {
    if (time.empty())
        throw std::runtime_error("Time arrays must be 1D");

    this->global_time = time;
}

void BaseTrigger::add_signal(const std::string &detector_name, const std::vector<double> &signal) {
     if (signal.empty())
        throw std::runtime_error("Signal arrays must be 1D");

    this->triggers.emplace_back(detector_name, signal);
}

struct Trigger BaseTrigger::get_trigger(const std::string &detector_name) const {
    for (const struct Trigger &trigger : this->triggers)
        if (trigger.detector_name == detector_name)
            return trigger;

    throw std::runtime_error("Detector not found");
}



void BaseTrigger::validate_detector_existence(const std::string &detector_name) const
{
    for (struct Trigger trigger: this->triggers)
        if (detector_name == trigger.detector_name)
            return;

    std::runtime_error("Trigger detector not found in signal map.");
}

// Helper function: Extract signal segments given valid trigger indices.
void BaseTrigger::extract_signal_segments(const std::vector<std::pair<int, int>> &valid_triggers)
{
    for (struct Trigger &trigger : this->triggers) {
        size_t segment_id = 0;
        for (const auto &[start, end] : valid_triggers) {
            for (int i = start; i <= end; ++i) {
                if (i >= static_cast<int>(trigger.buffer_size))
                    break;

                trigger.signal_out.push_back(trigger.buffer_ptr[i]);
                trigger.time_out.push_back(this->global_time[i]);
                trigger.segment_ids_out.push_back(segment_id);
            }
            segment_id++;
        }
    }
}

std::vector<double> BaseTrigger::get_signals_py(const std::string &detector_name) const {
    struct Trigger trigger = this->get_trigger(detector_name);

    return trigger.signal_out;
}

std::vector<double> BaseTrigger::get_times_py(const std::string &detector_name) const {
    struct Trigger trigger = this->get_trigger(detector_name);

    return trigger.time_out;
}

std::vector<int> BaseTrigger::get_segments_ID_py(const std::string &detector_name) const {
    struct Trigger trigger = this->get_trigger(detector_name);

    return trigger.segment_ids_out;
}




// ------------- FixedWindow class implementation-------------//
void FixedWindow::run(const double threshold) {
    if (global_time.empty())
        throw pybind11::value_error("Global time axis must be set before running triggers");

    if (trigger_detector_name.empty())
        throw pybind11::value_error("Trigger detector name must be set before running triggers");


    struct Trigger trigger_channel = this->get_trigger(this->trigger_detector_name);

    std::vector<std::pair<int, int>> valid_triggers;

    std::vector<int> trigger_indices;
    for (size_t i = 1; i < trigger_channel.buffer_size; ++i)
        if (trigger_channel.buffer_ptr[i - 1] <= threshold && trigger_channel.buffer_ptr[i] > threshold)
            trigger_indices.push_back(i - 1);

    int last_end = -1;
    for (int idx : trigger_indices) {
        int start = idx - this->pre_buffer - 1;
        int end = idx + this->post_buffer;
        if (start < 0 || end >= static_cast<int>(trigger_channel.buffer_size))
            continue;
        if (start > last_end) {
            valid_triggers.emplace_back(start, end);
            last_end = end;
        }
        if (this->max_triggers > 0 && valid_triggers.size() >= static_cast<size_t>(this->max_triggers))
            break;
    }

    if (valid_triggers.empty())
        return ;

    this->extract_signal_segments(valid_triggers);
}


// ------------- DynamicWindow class implementation-------------//
void DynamicWindow::run(const double threshold) {
    if (global_time.empty())
        throw pybind11::value_error("Global time axis must be set before running triggers");

    if (trigger_detector_name.empty())
        throw pybind11::value_error("Trigger detector name must be set before running triggers");


    struct Trigger trigger_channel = this->get_trigger(trigger_detector_name);

    std::vector<std::pair<int, int>> valid_triggers;

    int last_end = -1;
    for (size_t i = 1; i < trigger_channel.buffer_size; ++i) {
        if (trigger_channel.buffer_ptr[i - 1] <= threshold && trigger_channel.buffer_ptr[i] > threshold) {
            int start = static_cast<int>(i) - this->pre_buffer;

            if (start < 0)
                start = 0;

            size_t j = i;

            while (j < trigger_channel.buffer_size && trigger_channel.buffer_ptr[j] > threshold)
                j++;
            int end = static_cast<int>(j) - 1 + this->post_buffer;


            if (end >= static_cast<int>(trigger_channel.buffer_size))
                end = static_cast<int>(trigger_channel.buffer_size) - 1;

            if (start > last_end) {
                valid_triggers.emplace_back(start, end);
                last_end = end;
            }

            if (this->max_triggers > 0 && valid_triggers.size() >= static_cast<size_t>(this->max_triggers))
                break;

            i = j;
        }
    }

    if (valid_triggers.empty())
        return ;

    this->extract_signal_segments(valid_triggers);
}


// ------------- DoubleThreshold class implementation-------------//
void DoubleThreshold::run(const double threshold, const double lower_threshold, const bool debounce_enabled, const int min_window_duration) {
    if (global_time.empty())
        throw pybind11::value_error("Global time axis must be set before running triggers");

    if (trigger_detector_name.empty())
        throw pybind11::value_error("Trigger detector name must be set before running triggers");


    struct Trigger trigger_channel = this->get_trigger(trigger_detector_name);

    std::vector<std::pair<int, int>> valid_triggers;

    double _lower_threshold;
    if (std::isnan(lower_threshold))
        _lower_threshold = threshold;
    else
        _lower_threshold = lower_threshold;

    int last_end = -1;
    for (size_t i = 1; i < trigger_channel.buffer_size; ++i) {
        if (trigger_channel.buffer_ptr[i - 1] <= threshold && trigger_channel.buffer_ptr[i] > threshold) {
            size_t j = i;
            if (debounce_enabled && min_window_duration != -1) {
                size_t count = 0;
                while (j < trigger_channel.buffer_size && trigger_channel.buffer_ptr[j] > threshold) {
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
                while (j < trigger_channel.buffer_size && trigger_channel.buffer_ptr[j] > threshold)
                    ++j;
            }
            int start = static_cast<int>(i) - this->pre_buffer;
            if (start < 0)
                start = 0;
            size_t k = j;
            while (k < trigger_channel.buffer_size && trigger_channel.buffer_ptr[k] > _lower_threshold)
                ++k;
            int end = static_cast<int>(k) - 1 + this->post_buffer;
            if (end >= static_cast<int>(trigger_channel.buffer_size))
                end = static_cast<int>(trigger_channel.buffer_size) - 1;
            if (start > last_end) {
                valid_triggers.emplace_back(start, end);
                last_end = end;
            }
            if (this->max_triggers > 0 && valid_triggers.size() >= static_cast<size_t>(this->max_triggers))
                break;
            i = k;
        }
    }


    if (valid_triggers.empty())
        return ;

    this->extract_signal_segments(valid_triggers);
}

