#include "triggering_system.h"
#include <string>
#include <cmath>      // for std::isnan
#include "../utils.h"

namespace py = pybind11;

void TriggeringSystem::add_time(const py::buffer &time) {
    if (time.request().ndim != 1)
        throw std::runtime_error("Time arrays must be 1D");

    global_time = time;
}

void TriggeringSystem::add_signal(const std::string &detector_name, const py::buffer signal) {
    if (signal.request().ndim != 1)
        throw std::runtime_error("Signal arrays must be 1D");

    this->triggers.emplace_back(detector_name, signal);
}


void TriggeringSystem::run(const std::string &algorithm) {
    // Validate that the trigger detector exists.
    this->validate_detector_existence(trigger_detector_name);

    // For time, try the per-detector map; if not found, check global_time.
    if (!global_time)
        throw py::value_error("No time array found. Please add a time array using add_time().");

    std::vector<std::pair<int, int>> trigger_indices;

    if (algorithm == "fixed-window")
        trigger_indices = this->run_fixed_window();
    else if (algorithm == "dynamic")
        trigger_indices = this->run_dynamic_single_threshold();
    else if (algorithm == "dynamic-simple")
        trigger_indices = this->run_dynamic();
    else
        throw py::value_error("Invalid triggering algorithm, options are: 'fixed-window', 'dynamic', or 'dynamic-simple'.");

    if (trigger_indices.empty())
        return ;

    extract_signal_segments(trigger_indices);
}

// Fixed-window triggered acquisition.
std::vector<std::pair<int, int>> TriggeringSystem::run_fixed_window() {
    struct Trigger trigger_channel = this->get_trigger(trigger_detector_name);

    std::vector<std::pair<int, int>> valid_triggers;

    std::vector<int> trigger_indices;
    for (size_t i = 1; i < trigger_channel.buffer_size; ++i)
        if (trigger_channel.buffer_ptr[i - 1] <= threshold && trigger_channel.buffer_ptr[i] > threshold)
            trigger_indices.push_back(i - 1);

    int last_end = -1;
    for (int idx : trigger_indices) {
        int start = idx - pre_buffer - 1;
        int end = idx + post_buffer;
        if (start < 0 || end >= static_cast<int>(trigger_channel.buffer_size))
            continue;
        if (start > last_end) {
            valid_triggers.emplace_back(start, end);
            last_end = end;
        }
        if (max_triggers > 0 && valid_triggers.size() >= static_cast<size_t>(max_triggers))
            break;
    }

    return valid_triggers;
}

// Simple dynamic triggered acquisition.
std::vector<std::pair<int, int>> TriggeringSystem::run_dynamic() {
    struct Trigger trigger_channel = this->get_trigger(trigger_detector_name);

    std::vector<std::pair<int, int>> valid_triggers;

    int last_end = -1;
    for (size_t i = 1; i < trigger_channel.buffer_size; ++i) {
        if (trigger_channel.buffer_ptr[i - 1] <= threshold && trigger_channel.buffer_ptr[i] > threshold) {
            int start = static_cast<int>(i) - pre_buffer;
            if (start < 0)
                start = 0;
            size_t j = i;
            while (j < trigger_channel.buffer_size && trigger_channel.buffer_ptr[j] > threshold)
                j++;
            int end = static_cast<int>(j) - 1 + post_buffer;
            if (end >= static_cast<int>(trigger_channel.buffer_size))
                end = static_cast<int>(trigger_channel.buffer_size) - 1;
            if (start > last_end) {
                valid_triggers.emplace_back(start, end);
                last_end = end;
            }
            if (max_triggers > 0 && valid_triggers.size() >= static_cast<size_t>(max_triggers))
                break;
            i = j;
        }
    }

    return valid_triggers;
}

// Dynamic triggered acquisition with single threshold (with optional lower_threshold and debounce).
std::vector<std::pair<int, int>> TriggeringSystem::run_dynamic_single_threshold() {
    struct Trigger trigger_channel = this->get_trigger(trigger_detector_name);

    std::vector<std::pair<int, int>> valid_triggers;

    if (std::isnan(lower_threshold))
        this->lower_threshold = this->threshold;

    int last_end = -1;
    for (size_t i = 1; i < trigger_channel.buffer_size; ++i) {
        if (trigger_channel.buffer_ptr[i - 1] <= this->threshold && trigger_channel.buffer_ptr[i] > this->threshold) {
            size_t j = i;
            if (debounce_enabled && min_window_duration != -1) {
                size_t count = 0;
                while (j < trigger_channel.buffer_size && trigger_channel.buffer_ptr[j] > this->threshold) {
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
                while (j < trigger_channel.buffer_size && trigger_channel.buffer_ptr[j] > this->threshold)
                    ++j;
            }
            int start = static_cast<int>(i) - pre_buffer;
            if (start < 0)
                start = 0;
            size_t k = j;
            while (k < trigger_channel.buffer_size && trigger_channel.buffer_ptr[k] > this->lower_threshold)
                ++k;
            int end = static_cast<int>(k) - 1 + post_buffer;
            if (end >= static_cast<int>(trigger_channel.buffer_size))
                end = static_cast<int>(trigger_channel.buffer_size) - 1;
            if (start > last_end) {
                valid_triggers.emplace_back(start, end);
                last_end = end;
            }
            if (max_triggers > 0 && valid_triggers.size() >= static_cast<size_t>(max_triggers))
                break;
            i = k;
        }
    }

    return valid_triggers;
}

struct Trigger TriggeringSystem::get_trigger(const std::string &detector_name) {
    for (struct Trigger &trigger : this->triggers)
        if (trigger.detector_name == detector_name)
            return trigger;

    throw std::runtime_error("Detector not found");
}

std::vector<double> TriggeringSystem::get_signals_py(const std::string &detector_name) {
    struct Trigger trigger = this->get_trigger(detector_name);

    return trigger.signal_out;

    // return to_array_double(trigger.signal_out);
}

std::vector<double> TriggeringSystem::get_times_py(const std::string &detector_name) {
    struct Trigger trigger = this->get_trigger(detector_name);

    return trigger.time_out;

    // return to_array_double(trigger.time_out);
}

std::vector<int> TriggeringSystem::get_segments_ID_py(const std::string &detector_name) {
    struct Trigger trigger = this->get_trigger(detector_name);

    return trigger.segment_ids_out;

    // return to_array_int(trigger.segment_ids_out);
}

void TriggeringSystem::validate_detector_existence(const std::string &detector_name)
{
    for (struct Trigger trigger: this->triggers)
        if (detector_name == trigger.detector_name)
            return;

    std::runtime_error("Trigger detector not found in signal map.");
}

// Helper function: Extract signal segments given valid trigger indices.
void TriggeringSystem::extract_signal_segments(const std::vector<std::pair<int, int>> &valid_triggers)
{
    double* time_ptr = static_cast<double *>(global_time.request().ptr);

    for (struct Trigger &trigger : this->triggers) {
        size_t segment_id = 0;
        for (const auto &[start, end] : valid_triggers) {
            for (int i = start; i <= end; ++i) {
                if (i >= static_cast<int>(trigger.buffer_size))
                    break;

                trigger.signal_out.push_back(trigger.buffer_ptr[i]);
                trigger.time_out.push_back(time_ptr[i]);
                trigger.segment_ids_out.push_back(segment_id);
            }
            segment_id++;
        }
    }
}

