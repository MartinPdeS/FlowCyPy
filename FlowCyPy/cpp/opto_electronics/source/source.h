#pragma once

#include <vector>
#include <random>
#include <cmath>
#include <stdexcept>
#include <algorithm>
#include <limits>
#include <string>
#include <omp.h>

#include <utils/constants.h>


/**
 * @brief Abstract base class describing an illumination source.
 *
 * This class defines the shared physical parameters and utility operations used by
 * concrete source models such as Gaussian and flat top beams. A source is described
 * by its wavelength, optical power, polarization, and optional stochastic noise
 * mechanisms such as relative intensity noise (RIN) and photon shot noise.
 *
 * In addition to purely geometric profile evaluation, this class provides:
 * - conversion utilities between wavelength, frequency, and photon energy
 * - helpers to validate sampled time axes and pulse parameter vectors
 * - stochastic perturbation of signals through RIN and shot noise
 * - construction of temporally correlated gamma traces through source specific kernels
 *
 * Concrete derived classes must implement the spatial profile, focal amplitude,
 * particle transit width, pulse synthesis model, and temporal kernel used to represent
 * source induced smoothing in time.
 */
class BaseSource {
public:
    double wavelength;          // [meter]
    double rin;                 // [dB / hertz]
    double optical_power;       // [watt]
    double amplitude;           // [volt / meter]
    double polarization;        // [radian]
    double bandwidth;           // [hertz]
    bool include_shot_noise;    // include shot noise in power signals
    bool include_rin_noise;     // include RIN noise in amplitude or power signals
    bool debug_mode;            // print debug information during computation

    virtual ~BaseSource() = default;

    /**
     * @brief Construct a source with its fundamental optical parameters.
     *
     * @param wavelength Source wavelength in meter. Must be strictly positive.
     * @param rin Relative intensity noise expressed in dB / Hz.
     * @param optical_power Total optical power in watt. Must be non negative.
     * @param polarization Polarization angle in radian.
     * @param include_shot_noise Whether shot noise should be considered when generating
     * power signals.
     * @param include_rin_noise Whether RIN should be considered when perturbing
     * amplitude or power signals.
     *
     * @throws std::runtime_error If wavelength is not strictly positive or if
     * optical_power is negative.
     */
    BaseSource(
        const double wavelength,
        const double rin,
        const double optical_power,
        const double polarization,
        const double bandwidth = std::numeric_limits<double>::quiet_NaN(),
        const bool include_shot_noise = true,
        const bool include_rin_noise = true,
        const bool debug_mode = false
    );

    void test_openmp();

    /**
     * @brief Compute the optical frequency corresponding to the source wavelength.
     *
     * The frequency is evaluated from
     * c / lambda
     * where c is the speed of light in vacuum.
     *
     * @return Optical frequency in hertz.
     */
    double get_frequency() const;

    /**
     * @brief Compute the energy carried by a single photon.
     *
     * The photon energy is evaluated from
     * h * nu
     * where h is Planck's constant and nu is the optical frequency.
     *
     * @return Photon energy in joule.
     */
    double get_photon_energy() const;

    /**
     * @brief Convert the source RIN from logarithmic to linear units.
     *
     * The stored RIN value is assumed to be expressed in dB / Hz. This method returns
     * the corresponding linear spectral density in 1 / Hz.
     *
     * @return Linear RIN value in 1 / hertz.
     */
    double get_rin_linear() const;

    /**
     * @brief Compute the conversion factor from optical power to expected photon count.
     *
     * For a given sampling interval, the expected number of photons produced by a power P
     * is:
     * P * time_step / photon_energy
     *
     * This helper returns the factor
     * time_step / photon_energy
     * so that photon count can be obtained directly by multiplication with power.
     *
     * @param time_step Sampling interval in second. Must be strictly positive.
     * @return Conversion factor in photons / watt.
     *
     * @throws std::runtime_error If time_step is not strictly positive.
     */
    double get_watt_to_photon_factor(const double time_step) const;

    /**
     * @brief Infer the sampling interval from a uniformly sampled time axis.
     *
     * The method verifies that:
     * - at least two samples are present
     * - the time axis is strictly increasing
     * - the spacing is uniform within numerical tolerance
     *
     * @param time_array Time samples in second.
     * @return Sampling interval in second.
     *
     * @throws std::runtime_error If the time axis is too short, not strictly increasing,
     * or not uniformly sampled.
     */
    double get_time_step_from_time_array(const std::vector<double>& time_array) const;

    /**
     * @brief Apply independent relative intensity noise to a signal.
     *
     * Each sample is perturbed using a Gaussian approximation of source RIN, with
     * sample dependent standard deviation:
     * signal_value * sqrt(RIN_linear * bandwidth)
     *
     * This produces a multiplicative noise model consistent with white relative
     * intensity fluctuations over the specified bandwidth.
     *
     * If bandwidth is NaN, the function returns immediately and leaves the signal
     * unchanged. This is used to represent an unspecified or disabled bandwidth.
     *
     * @param signal_values Signal samples to perturb. Values are expected to be non negative.
     * @param bandwidth Effective bandwidth in hertz. Pass NaN to disable the perturbation.
     *
     * @throws std::runtime_error If bandwidth is non positive or if a signal sample is negative.
     */
    void add_rin_to_signal(std::vector<double>& signal_values) const;



    /**
     * @brief Apply one shared RIN realization across several detector channels.
     *
     * At each time sample, a single fractional fluctuation is drawn and applied to all
     * channels simultaneously. This models source noise that is common mode across
     * detector arms illuminated by the same optical field.
     *
     * The perturbation applied at each sample is:
     * channel_value *= (1 + fluctuation)
     * where fluctuation is Gaussian with standard deviation
     * sqrt(RIN_linear * bandwidth)
     *
     * If bandwidth is NaN, the function returns immediately and no perturbation is applied.
     *
     * @param signal_values_per_channel Collection of detector signals in watt. All channels
     * must have the same number of samples.
     *
     * @throws std::runtime_error If bandwidth is non positive, if the input is empty,
     * if any channel is empty, if channel lengths differ, or if a channel contains
     * negative power values.
     */
    void add_common_rin_to_signals(std::vector<std::vector<double>>& signal_values_per_channel) const;



    /**
     * @brief Apply photon shot noise to an optical power signal.
     *
     * The optical power at each sample is converted to an expected photon count over
     * the interval time_step. A noisy photon count is then drawn:
     * - from a Poisson distribution for small counts
     * - from a Gaussian approximation for large counts
     *
     * The noisy photon count is finally converted back to optical power.
     *
     * This produces a physically motivated discrete counting noise model.
     *
     * @param power_values Optical power samples in watt. Values must be non negative.
     * @param time_step Sampling interval in second. Must be strictly positive.
     *
     * @throws std::runtime_error If time_step is non positive or if a power sample is negative.
     */
    void add_shot_noise_to_signal(std::vector<double>& power_values, const double time_step) const;



    /**
     * @brief Evaluate the electric field amplitude at multiple spatial positions.
     *
     * The three coordinate vectors must have identical sizes. The returned vector has
     * the same length, with one amplitude value computed per point.
     *
     * The bandwidth parameter is currently ignored at this abstraction level. It is
     * accepted only to preserve a homogeneous interface with other signal generation
     * methods.
     *
     * @param x X coordinates in meter.
     * @param y Y coordinates in meter.
     * @param z Z coordinates in meter.
     * @param bandwidth Effective bandwidth in hertz, or NaN if unset.
     * @return Electric field amplitude values in volt / meter.
     *
     * @throws std::runtime_error If x, y, and z do not have identical sizes.
     */
    std::vector<double> get_amplitude_signal(
        const std::vector<double>& x,
        const std::vector<double>& y,
        const std::vector<double>& z
    ) const;

    /**
     * @brief Evaluate the optical power at multiple spatial positions.
     *
     * The power at each position is obtained from the normalized source profile scaled
     * by the total source power.
     *
     * The bandwidth and time_step arguments are currently ignored by this geometric
     * evaluation routine. They are kept in the interface for consistency with other
     * signal generation functions.
     *
     * @param x X coordinates in meter.
     * @param y Y coordinates in meter.
     * @param z Z coordinates in meter.
     * @param bandwidth Effective bandwidth in hertz.
     * @param time_step Sampling interval in second.
     * @return Optical power values in watt.
     *
     * @throws std::runtime_error If x, y, and z do not have identical sizes.
     */
    std::vector<double> get_power_signal(
        const std::vector<double>& x,
        const std::vector<double>& y,
        const std::vector<double>& z,
        const double time_step
    ) const;

    /**
     * @brief Evaluate the optical power at one spatial position.
     *
     * The returned value is the source total power multiplied by the normalized
     * profile value at the requested position.
     *
     * @param x X coordinate in meter.
     * @param y Y coordinate in meter.
     * @param z Z coordinate in meter.
     * @return Optical power in watt.
     */
    double get_power_at(
        const double x,
        const double y,
        const double z = 0.0
    ) const;

    /**
     * @brief Compute the characteristic pulse width associated with each particle velocity.
     *
     * This width represents the temporal duration induced by the transit of particles
     * through the source profile.
     *
     * @param velocity Particle velocities in meter / second.
     * @return Pulse widths in second, one per input velocity.
     */
    virtual std::vector<double> get_particle_width(
        const std::vector<double>& velocity
    ) const = 0;

    /**
     * @brief Evaluate the electric field amplitude at one spatial position.
     *
     * @param x X coordinate in meter.
     * @param y Y coordinate in meter.
     * @param z Z coordinate in meter.
     * @return Electric field amplitude in volt / meter.
     */
    virtual double get_amplitude_at(
        const double x,
        const double y,
        const double z = 0.0
    ) const = 0;

    /**
     * @brief Generate a deterministic pulse train defined by particle transit events.
     *
     * This method is implemented by each concrete source model using its own intrinsic
     * temporal shape. Each pulse is defined by a center time, an amplitude, and a width
     * induced by the corresponding particle velocity.
     *
     * @param velocities Particle velocities in meter / second.
     * @param pulse_centers Pulse center times in second.
     * @param pulse_amplitudes Pulse amplitudes in watt.
     * @param time_array Time axis in second.
     * @param base_level Baseline optical power in watt.
     * @param bandwidth Effective bandwidth in hertz, or NaN if unset.
     * @return Time domain optical power signal in watt.
     */
    virtual std::vector<double> generate_pulses(
        const std::vector<double>& velocities,
        const std::vector<double>& pulse_centers,
        const std::vector<double>& pulse_amplitudes,
        const std::vector<double>& time_array,
        const double base_level
    ) const = 0;

    /**
     * @brief Compute the characteristic temporal width of the source kernel.
     *
     * This quantity maps a particle mean velocity to the time scale over which the
     * source profile smooths a latent process. Derived classes define this relation
     * according to their geometry.
     *
     * @param mean_velocity Mean particle velocity in meter / second.
     * @return Characteristic kernel width in second.
     */
    virtual double get_kernel_width_from_velocity(
        const double mean_velocity
    ) const = 0;

    /**
     * @brief Construct the normalized temporal kernel associated with the source.
     *
     * The kernel is centered and normalized such that the sum of all samples is one.
     * It represents the temporal footprint induced by the source profile for a particle
     * moving at the specified mean velocity.
     *
     * @param time_step Sampling interval in second.
     * @param mean_velocity Mean particle velocity in meter / second.
     * @return Normalized discrete temporal kernel.
     */
    virtual std::vector<double> get_temporal_kernel(
        const double time_step,
        const double mean_velocity
    ) const = 0;

    /**
     * @brief Convolve a discrete signal with a kernel using zero padding.
     *
     * Samples outside the input signal support are treated as zero. The output has the
     * same size as the input signal.
     *
     * @param signal Input signal.
     * @param kernel Convolution kernel.
     * @return Convolved signal with the same size as the input.
     *
     * @throws std::runtime_error If signal or kernel is empty.
     */
    std::vector<double> convolve_with_kernel(
        const std::vector<double>& signal,
        const std::vector<double>& kernel
    ) const;



    /**
     * @brief Generate a temporally correlated gamma distributed optical power trace.
     *
     * A latent gamma process is first sampled independently at each time step using the
     * provided shape and scale parameters. This latent process is then convolved with
     * the source specific temporal kernel associated with the given mean particle
     * velocity. The result is a positive stochastic signal whose temporal correlation is
     * determined by the source geometry.
     *
     * This is useful when modeling random source fluctuations that should retain the
     * intrinsic temporal footprint of the beam rather than using an arbitrary smoothing
     * operation.
     *
     * @param time_array Uniformly sampled time axis in second.
     * @param shape Shape parameter of the gamma law. Must be strictly positive.
     * @param scale Scale parameter of the gamma law in watt. Must be non negative.
     * @param mean_velocity Mean particle velocity in meter / second. Must be strictly positive.
     * @return Correlated optical power trace in watt.
     *
     * @throws std::runtime_error If the time axis is invalid, or if any parameter is outside
     * its allowed range.
     */
    std::vector<double> get_gamma_trace(
        const std::vector<double>& time_array,
        double shape,
        double scale,
        double mean_velocity
    ) const;


    /**
     * @brief Recompute and store the focal electric field amplitude.
     *
     * Derived classes define how the on axis or focal amplitude is obtained from the
     * source geometry and optical power. This method updates the cached amplitude value
     * stored in the object.
     */
    void update_amplitude();

protected:
    /**
     * @brief Compute the electric field amplitude at the beam focus or peak location.
     *
     * @return Focal electric field amplitude in volt / meter.
     */
    virtual double get_amplitude_at_focus() const = 0;

    /**
     * @brief Evaluate the normalized spatial profile at one position.
     *
     * The returned value is dimensionless and typically lies in the range [0, 1].
     * It is used to map total optical power to local optical power.
     *
     * @param x X coordinate in meter.
     * @param y Y coordinate in meter.
     * @param z Z coordinate in meter.
     * @return Dimensionless normalized profile value.
     */
    virtual double get_normalized_profile_value(
        const double x,
        const double y,
        const double z = 0.0
    ) const = 0;

    /**
     * @brief Check that the three coordinate vectors have identical sizes.
     *
     * @param x X coordinates.
     * @param y Y coordinates.
     * @param z Z coordinates.
     *
     * @throws std::runtime_error If the three vectors do not have the same length.
     */
    void validate_coordinate_vectors(
        const std::vector<double>& x,
        const std::vector<double>& y,
        const std::vector<double>& z
    ) const ;

    /**
     * @brief Check that the pulse parameter vectors have identical sizes.
     *
     * Each entry in velocities, pulse_centers, and pulse_amplitudes must correspond to
     * one pulse event.
     *
     * @param velocities Particle velocities.
     * @param pulse_centers Pulse center times.
     * @param pulse_amplitudes Pulse amplitudes.
     *
     * @throws std::runtime_error If the vectors do not have the same length.
     */
    void validate_pulse_vectors(
        const std::vector<double>& velocities,
        const std::vector<double>& pulse_centers,
        const std::vector<double>& pulse_amplitudes
    ) const;

    /**
     * @brief Check that a velocity vector is non empty and strictly positive.
     *
     * @param velocity Particle velocities in meter / second.
     *
     * @throws std::runtime_error If the vector is empty or contains a non positive value.
     */
    void validate_velocity_vector(
        const std::vector<double>& velocity
    ) const;
};


/**
 * @brief Gaussian beam source with elliptical waists along Y and Z.
 *
 * This source models a transverse Gaussian intensity distribution. The temporal pulse
 * shape generated by particle transit is also Gaussian, with a width determined by the
 * beam extent along the flow direction.
 */
class Gaussian : public BaseSource {
public:
    double waist_y;   // [meter]
    double waist_z;   // [meter]

    /**
     * @brief Construct a Gaussian source.
     *
     * @param wavelength Source wavelength in meter.
     * @param rin Relative intensity noise in dB / Hz.
     * @param optical_power Total optical power in watt.
     * @param waist_y Gaussian waist along Y in meter. Must be strictly positive.
     * @param waist_z Gaussian waist along Z in meter. Must be strictly positive.
     * @param polarization Polarization angle in radian.
     * @param include_shot_noise Whether shot noise is enabled.
     * @param include_rin_noise Whether RIN is enabled.
     */
    Gaussian(
        const double wavelength,
        const double rin,
        const double optical_power,
        const double waist_y,
        const double waist_z,
        const double polarization,
        const double bandwidth = std::numeric_limits<double>::quiet_NaN(),
        const bool include_shot_noise = true,
        const bool include_rin_noise = true,
        const bool debug_mode = false
    );

    /**
     * @brief Update the Gaussian waists and refresh the focal amplitude.
     *
     * @param waist_y Gaussian waist along Y in meter. Must be strictly positive.
     * @param waist_z Gaussian waist along Z in meter. Must be strictly positive.
     *
     * @throws std::runtime_error If either waist is non positive.
     */
    void set_waist(
        const double waist_y,
        const double waist_z
    );

    /**
     * @brief Compute Gaussian transit pulse widths for a set of particle velocities.
     *
     * The characteristic width is defined here as:
     * waist_z / (2 * velocity)
     *
     * @param velocity Particle velocities in meter / second.
     * @return Transit widths in second.
     */
    std::vector<double> get_particle_width(
        const std::vector<double>& velocity
    ) const override;

    /**
     * @brief Return the Gaussian kernel width associated with a mean velocity.
     *
     * @param mean_velocity Mean particle velocity in meter / second.
     * @return Characteristic temporal width in second.
     *
     * @throws std::runtime_error If mean_velocity is non positive.
     */
    double get_kernel_width_from_velocity(
        const double mean_velocity
    ) const override;

    /**
     * @brief Build a normalized Gaussian temporal kernel.
     *
     * The kernel support spans approximately four standard deviations on each side.
     * The result is normalized such that the discrete sum is one.
     *
     * @param time_step Sampling interval in second.
     * @param mean_velocity Mean particle velocity in meter / second.
     * @return Normalized Gaussian kernel.
     *
     * @throws std::runtime_error If time_step is non positive or if the derived width is invalid.
     */
    std::vector<double> get_temporal_kernel(
        const double time_step,
        const double mean_velocity
    ) const override;

    /**
     * @brief Evaluate the Gaussian electric field amplitude at one position.
     *
     * The X coordinate is ignored in this simplified model. The amplitude decreases
     * exponentially with the squared normalized transverse distance in the YZ plane.
     *
     * @param x X coordinate in meter.
     * @param y Y coordinate in meter.
     * @param z Z coordinate in meter.
     * @return Electric field amplitude in volt / meter.
     */
    double get_amplitude_at(
        const double x,
        const double y,
        const double z = 0.0
    ) const override;

    /**
     * @brief Generate a sum of Gaussian shaped transit pulses.
     *
     * Each pulse is centered at pulse_centers[index], scaled by
     * pulse_amplitudes[index], and widened according to the corresponding particle
     * velocity.
     *
     * @param velocities Particle velocities in meter / second.
     * @param pulse_centers Pulse center times in second.
     * @param pulse_amplitudes Pulse amplitudes in watt.
     * @param time_array Time axis in second.
     * @param base_level Constant baseline level in watt.
     * @param bandwidth Effective bandwidth in hertz, or NaN if unset. Currently unused.
     * @return Time domain optical power signal in watt.
     */
    std::vector<double> generate_pulses(
        const std::vector<double>& velocities,
        const std::vector<double>& pulse_centers,
        const std::vector<double>& pulse_amplitudes,
        const std::vector<double>& time_array,
        const double base_level
    ) const override;

protected:
    /**
     * @brief Compute the peak electric field amplitude of the Gaussian beam.
     *
     * The expression is derived by relating optical power to the electromagnetic
     * energy flux over the effective beam area.
     *
     * @return Peak electric field amplitude in volt / meter.
     */
    double get_amplitude_at_focus() const override;

    /**
     * @brief Evaluate the normalized Gaussian intensity profile.
     *
     * The X coordinate is ignored and the profile is defined only in the YZ plane.
     *
     * @param x X coordinate in meter.
     * @param y Y coordinate in meter.
     * @param z Z coordinate in meter.
     * @return Dimensionless normalized profile value.
     */
    double get_normalized_profile_value(
        const double x,
        const double y,
        const double z = 0.0
    ) const override;
};


/**
 * @brief Flat top source with uniform amplitude inside an elliptical support.
 *
 * This source models a beam that is constant within a bounded transverse region and
 * zero outside. The temporal pulse shape associated with particle transit is therefore
 * rectangular rather than Gaussian.
 */
class FlatTop : public BaseSource {
public:
    double waist_y;   // [meter]
    double waist_z;   // [meter]

    /**
     * @brief Construct a flat top source.
     *
     * @param wavelength Source wavelength in meter.
     * @param rin Relative intensity noise in dB / Hz.
     * @param optical_power Total optical power in watt.
     * @param waist_y Support semi width along Y in meter. Must be strictly positive.
     * @param waist_z Support semi width along Z in meter. Must be strictly positive.
     * @param polarization Polarization angle in radian.
     * @param include_shot_noise Whether shot noise is enabled.
     * @param include_rin_noise Whether RIN is enabled.
     */
    FlatTop(
        const double wavelength,
        const double rin,
        const double optical_power,
        const double waist_y,
        const double waist_z,
        const double polarization,
        const double bandwidth = std::numeric_limits<double>::quiet_NaN(),
        const bool include_shot_noise = true,
        const bool include_rin_noise = true,
        const bool debug_mode = false
    );

    /**
     * @brief Update the flat top support sizes and refresh the focal amplitude.
     *
     * @param waist_y Support semi width along Y in meter. Must be strictly positive.
     * @param waist_z Support semi width along Z in meter. Must be strictly positive.
     *
     * @throws std::runtime_error If either support size is non positive.
     */
    void set_waist(
        const double waist_y,
        const double waist_z
    );

    /**
     * @brief Compute flat top transit pulse widths for a set of particle velocities.
     *
     * The characteristic width is defined here as:
     * waist_z / (2 * velocity)
     *
     * @param velocity Particle velocities in meter / second.
     * @return Transit widths in second.
     */
    std::vector<double> get_particle_width(
        const std::vector<double>& velocity
    ) const override;

    /**
     * @brief Return the rectangular kernel width associated with a mean velocity.
     *
     * @param mean_velocity Mean particle velocity in meter / second.
     * @return Characteristic temporal width in second.
     *
     * @throws std::runtime_error If mean_velocity is non positive.
     */
    double get_kernel_width_from_velocity(
        const double mean_velocity
    ) const override;

    /**
     * @brief Build a normalized rectangular temporal kernel.
     *
     * The support length is derived from the transit width in samples, rounded to the
     * nearest odd integer so that the kernel remains centered.
     *
     * @param time_step Sampling interval in second.
     * @param mean_velocity Mean particle velocity in meter / second.
     * @return Normalized rectangular kernel.
     *
     * @throws std::runtime_error If time_step is non positive or if the derived width is invalid.
     */
    std::vector<double> get_temporal_kernel(
        const double time_step,
        const double mean_velocity
    ) const override;

    /**
     * @brief Evaluate the flat top electric field amplitude at one position.
     *
     * The field is constant inside the elliptical support and zero outside.
     * The X coordinate is ignored in this simplified transverse model.
     *
     * @param x X coordinate in meter.
     * @param y Y coordinate in meter.
     * @param z Z coordinate in meter.
     * @return Electric field amplitude in volt / meter.
     */
    double get_amplitude_at(
        const double x,
        const double y,
        const double z = 0.0
    ) const override;

    /**
     * @brief Generate a sum of rectangular transit pulses.
     *
     * Each pulse contributes a constant amplitude over its support interval and zero
     * outside. The support width is set by the corresponding particle velocity.
     *
     * @param velocities Particle velocities in meter / second.
     * @param pulse_centers Pulse center times in second.
     * @param pulse_amplitudes Pulse amplitudes in watt.
     * @param time_array Time axis in second.
     * @param base_level Constant baseline level in watt.
     * @return Time domain optical power signal in watt.
     */
    std::vector<double> generate_pulses(
        const std::vector<double>& velocities,
        const std::vector<double>& pulse_centers,
        const std::vector<double>& pulse_amplitudes,
        const std::vector<double>& time_array,
        const double base_level
    ) const override;

protected:
    /**
     * @brief Compute the constant electric field amplitude inside the flat top support.
     *
     * The expression is derived by relating optical power to the electromagnetic
     * energy flux over the effective support area.
     *
     * @return Flat top electric field amplitude in volt / meter.
     */
    double get_amplitude_at_focus() const override;

    /**
     * @brief Evaluate the normalized flat top intensity profile.
     *
     * The profile equals one inside the elliptical support and zero outside.
     * The X coordinate is ignored in this simplified transverse model.
     *
     * @param x X coordinate in meter.
     * @param y Y coordinate in meter.
     * @param z Z coordinate in meter.
     * @return Dimensionless normalized profile value.
     */
    double get_normalized_profile_value(
        const double x,
        const double y,
        const double z = 0.0
    ) const override;
};
