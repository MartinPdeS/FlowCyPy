#pragma once

#include <vector>
#include <limits>
#include <cmath>
#include <stdexcept>

#include <utils/utils.h>


class BaseCircuit {
public:
    virtual ~BaseCircuit() = default;

    /**
     * @brief Process a one dimensional signal and return the processed output.
     *
     * This abstract interface is shared by all circuit elements. The signal is
     * provided as a vector of samples and the processed result is returned as a
     * new vector.
     *
     * Some circuit elements require the sampling rate to interpret time dependent
     * parameters such as filter cutoff frequency or baseline restoration window
     * duration. If a given circuit does not require the sampling rate, the value
     * may be left unset.
     *
     * @param signal Input signal samples.
     * @param sampling_rate Sampling rate in hertz. Use NaN when not required.
     * @return Processed signal samples.
     */
    virtual std::vector<double> process(
        const std::vector<double>& signal,
        const double sampling_rate = std::numeric_limits<double>::quiet_NaN()
    ) const = 0;
};


class BaseLineRestoration : public BaseCircuit {
public:
    double window_size;  // [second]

    BaseLineRestoration() = default;

    /**
     * @brief Construct a baseline restoration circuit with a specified time window.
     *
     * The window size is expressed in second. If set to -1, the window is treated
     * as infinite and all previous samples are considered when estimating the local
     * baseline.
     *
     * @param window_size Window size in second, or -1 for an infinite window.
     */
    BaseLineRestoration(const double window_size)
        : window_size(window_size)
    {
        if (this->window_size <= 0.0 && this->window_size != -1.0) {
            throw std::runtime_error(
                "window_size must be strictly positive or equal to -1 for infinite window."
            );
        }
    }

    /**
     * @brief Apply baseline restoration to a signal.
     *
     * This method removes a drifting baseline by subtracting the minimum value
     * observed inside a sliding window. The window size is expressed in second
     * and is converted internally to a number of samples using the provided
     * sampling rate.
     *
     * If `window_size` is `-1`, an infinite history window is used and the
     * method does not require a sampling rate.
     *
     * @param signal Input signal samples.
     * @param sampling_rate Sampling rate in hertz. Required for finite window sizes.
     * @return Baseline restored signal.
     *
     * @throws std::runtime_error If the input signal is empty.
     * @throws std::runtime_error If a finite window is requested and the sampling
     * rate is not strictly positive.
     * @throws std::runtime_error If the finite window corresponds to fewer than
     * one sample.
     */
    std::vector<double> process(
        const std::vector<double>& signal,
        const double sampling_rate = std::numeric_limits<double>::quiet_NaN()
    ) const override;
};


class ButterworthLowPassFilter : public BaseCircuit {
public:
    double cutoff_frequency;  // [hertz]
    int order;
    double gain;

    ButterworthLowPassFilter() = default;

    /**
     * @brief Construct a Butterworth low pass filter.
     *
     * @param cutoff_frequency Cutoff frequency in hertz.
     * @param order Filter order.
     * @param gain Output gain applied after filtering.
     */
    ButterworthLowPassFilter(
        const double cutoff_frequency,
        const int order,
        const double gain
    )
        : cutoff_frequency(cutoff_frequency),
          order(order),
          gain(gain)
    {
        if (this->cutoff_frequency <= 0.0) {
            throw std::runtime_error("cutoff_frequency must be strictly positive.");
        }

        if (this->order <= 0) {
            throw std::runtime_error("order must be strictly positive.");
        }
    }

    /**
     * @brief Process a signal using a Butterworth low pass filter.
     *
     * This method applies a Butterworth low pass filter to the input signal and
     * returns the filtered result. The filter is implemented in the frequency
     * domain and requires the sampling rate to determine the discrete frequency
     * axis.
     *
     * The transfer function magnitude is defined as:
     *
     *     H(f) = (1 / sqrt(1 + (f / cutoff_frequency)^2))^order
     *
     * where `cutoff_frequency` sets the cutoff point and `order` controls the
     * steepness of the transition band. The `gain` parameter adjusts the output
     * amplitude after filtering.
     *
     * @param signal Input signal samples.
     * @param sampling_rate Sampling rate in hertz.
     * @return Filtered signal samples.
     *
     * @throws std::runtime_error If the signal is empty.
     * @throws std::runtime_error If the sampling rate is not strictly positive.
     * @throws std::runtime_error If the cutoff frequency is greater than or equal
     * to the Nyquist frequency.
     */
    std::vector<double> process(
        const std::vector<double>& signal,
        const double sampling_rate
    ) const override;
};


class BesselLowPassFilter : public BaseCircuit {
public:
    double cutoff_frequency;  // [hertz]
    int order;
    double gain;

    BesselLowPassFilter() = default;

    /**
     * @brief Construct a Bessel low pass filter.
     *
     * @param cutoff_frequency Cutoff frequency in hertz.
     * @param order Filter order.
     * @param gain Output gain applied after filtering.
     */
    BesselLowPassFilter(
        const double cutoff_frequency,
        const int order,
        const double gain
    )
        : cutoff_frequency(cutoff_frequency),
          order(order),
          gain(gain)
    {
        if (this->cutoff_frequency <= 0.0) {
            throw std::runtime_error("cutoff_frequency must be strictly positive.");
        }

        if (this->order <= 0) {
            throw std::runtime_error("order must be strictly positive.");
        }
    }

    /**
     * @brief Process a signal using a Bessel low pass filter.
     *
     * This method applies a Bessel low pass filter to the input signal and
     * returns the filtered result. The filter is implemented in the frequency
     * domain and requires the sampling rate to determine the discrete frequency
     * axis.
     *
     * The Bessel filter is often preferred when preserving pulse shape and group
     * delay characteristics is more important than achieving the sharpest possible
     * magnitude roll off.
     *
     * The `gain` parameter adjusts the output amplitude after filtering.
     *
     * @param signal Input signal samples.
     * @param sampling_rate Sampling rate in hertz.
     * @return Filtered signal samples.
     *
     * @throws std::runtime_error If the signal is empty.
     * @throws std::runtime_error If the sampling rate is not strictly positive.
     * @throws std::runtime_error If the cutoff frequency is greater than or equal
     * to the Nyquist frequency.
     */
    std::vector<double> process(
        const std::vector<double>& signal,
        const double sampling_rate
    ) const override;
};
