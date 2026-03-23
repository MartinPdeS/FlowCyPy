#pragma once

#include <vector>
#include <limits>
#include <random>
#include <cmath>
#include <stdexcept>

#include <utils/utils.h>


class Amplifier {
public:
    double gain;                    // [volt / ampere] or [volt / volt], depending on signal convention
    double bandwidth;               // [hertz]
    double voltage_noise_density;   // [volt / sqrt(hertz)]
    double current_noise_density;   // [ampere / sqrt(hertz)]
    int filter_order;               // low-pass filter order

    Amplifier(
        const double gain,
        const double bandwidth = std::numeric_limits<double>::quiet_NaN(),
        const double voltage_noise_density = 0.0,
        const double current_noise_density = 0.0,
        const int filter_order = 2
    );

    /**
     * @brief Return the amplifier output RMS noise over the configured bandwidth.
     *
     * The total RMS noise is computed from the quadratic sum of:
     * - voltage noise density integrated over bandwidth
     * - current noise density integrated over bandwidth and converted through gain
     *
     * @return RMS output noise.
     */
    double get_rms_noise() const;

    /**
     * @brief Return an amplified copy of the input signal.
     *
     * The signal is always amplified by the configured gain.
     *
     * If bandwidth is defined and sampling_rate is also provided, a realistic
     * Bessel low-pass filter is applied.
     *
     * If bandwidth is defined but sampling_rate is not provided, filtering is
     * skipped because a discrete-time filter requires sampling information.
     *
     * If noise densities are non zero and bandwidth is defined, additive Gaussian
     * noise is added after amplification.
     *
     * @param signal Input signal.
     * @param sampling_rate Sampling rate in hertz. If NaN, bandwidth filtering is skipped.
     * @return Amplified signal.
     */
    std::vector<double> amplify(
        const std::vector<double>& signal,
        const double sampling_rate = std::numeric_limits<double>::quiet_NaN()
    ) const;

    /**
     * @brief Return an amplified and bandwidth-limited copy of the input signal.
     *
     * A Bessel low-pass filter is applied with cutoff equal to the amplifier
     * bandwidth. The filter utility applies the amplifier gain during
     * reconstruction.
     *
     * @param signal Input signal.
     * @param sampling_rate Sampling rate in hertz.
     * @return Amplified and filtered signal.
     */
    std::vector<double> amplify_with_bandwidth(
        const std::vector<double>& signal,
        const double sampling_rate
    ) const;

    /**
     * @brief Return an amplified copy of the input signal without bandwidth limitation.
     *
     * @param signal Input signal.
     * @return Amplified signal.
     */
    std::vector<double> amplify_without_bandwidth(
        const std::vector<double>& signal
    ) const;

    /**
     * @brief Return a copy of the input signal with added Gaussian noise.
     *
     * @param signal Input signal.
     * @param mean Mean of the Gaussian noise.
     * @param standard_deviation Standard deviation of the Gaussian noise.
     * @return Noisy signal.
     */
    std::vector<double> add_gaussian_noise(
        const std::vector<double>& signal,
        const double mean,
        const double standard_deviation
    ) const;
};
