#pragma once

#include <vector>
#include <cmath>
#include <stdexcept>
#include <random>
#include <tuple>
#include <algorithm>
#include <string>

class FluidRegion {
public:
    double height = 0.0; // [m]
    double width = 0.0;  // [m]
    double area = 0.0;   // [m^2]
    double volume_flow = 0.0; // [m^3/s]
    double max_flow_speed = 0.0; // [m/s]
    double average_flow_speed = 0.0; // [m/s]

    FluidRegion() = default;

    FluidRegion(
        double height,
        double width,
        double volume_flow,
        double max_flow_speed,
        double average_flow_speed
    )
        : height(height),
          width(width),
          area(height * width),
          volume_flow(volume_flow),
          max_flow_speed(max_flow_speed),
          average_flow_speed(average_flow_speed)
    {}

    FluidRegion(double height, double width, double volume_flow)
        : height(height),
          width(width),
          area(height * width),
          volume_flow(volume_flow)
    {}
};

class FlowCell {
public:
    double width;  // [m]
    double height; // [m]
    double area;   // [m^2]
    double viscosity;     // [Pa.s]
    double sample_volume_flow; // [m^3/s]
    double sheath_volume_flow; // [m^3/s]
    int N_terms = 25;
    int n_int = 200;
    std::string event_scheme = "uniform-random";
    std::string transverse_sampling_scheme = "velocity-weighted";
    bool perfectly_aligned = false;

    double Q_total;
    double dpdx;
    double dpdx_ref = -1.0;
    double u_center;

    FluidRegion sample;
    FluidRegion sheath;

    FlowCell() = default;

    /**
     * @brief Construct a new FlowCell object with specified parameters.
     * This constructor initializes the flow cell with the given dimensions,
     * flow rates, viscosity, number of terms for series expansion, number of integration points
     * for numerical integration, and the default event sampling scheme.
     *
     * @param width Width of the flow cell in meters.
     * @param height Height of the flow cell in meters.
     * @param sample_volume_flow Volume flow rate of the sample in m^3/s.
     * @param sheath_volume_flow Volume flow rate of the sheath fluid in m^3/s.
     * @param viscosity Viscosity of the fluid in Pa.s.
     * @param N_terms Number of odd terms used in the Fourier series expansion.
     * @param n_int Number of integration points per axis used for numerical integration.
     * @param event_scheme Default event sampling scheme. Supported values are "uniform-random", "linear", and "poisson".
     * @param transverse_sampling_scheme Transverse position sampling scheme. Supported values are "velocity-weighted" and "uniform-random".
     * @param perfectly_aligned If true, the sample stream is perfectly aligned with the center of the channel.
     * @note The constructor calls the `initialize` method to set up the flow cell parameters.
     */
    FlowCell(
        double width,
        double height,
        double sample_volume_flow,
        double sheath_volume_flow,
        double viscosity,
        int N_terms,
        int n_int,
        const std::string& event_scheme,
        const std::string& transverse_sampling_scheme,
        bool perfectly_aligned
    );

    /**
     * @brief Sample the transverse velocity profile of the focused sample region.
     * This method generates a list of tuples representing the transverse profile
     * of the focused sample stream, where each tuple contains the y-coordinate, z-coordinate,
     * and the corresponding velocity at that point.
     *
     * By default, coordinates are sampled with probability proportional to the local
     * axial velocity. This gives flux-weighted trajectory sampling, so faster regions
     * of the sample stream contribute proportionally more particles per unit time.
     * If `transverse_sampling_scheme` is set to "uniform-random", coordinates are sampled
     * uniformly within the sample region dimensions.
     *
     * The velocity is calculated based on the flow cell's parameters and the
     * transverse position within the channel.
     *
     * @param n_samples Number of transverse samples to generate.
     * @return A tuple containing three vectors: y-coordinates, z-coordinates, and velocities.
     */
    std::tuple<std::vector<double>, std::vector<double>, std::vector<double>>
    sample_transverse_profile(int n_samples) const;

private:
    /**
     * @brief Initialize the flow cell parameters based on the provided dimensions and flow rates.
     * This method computes the total flow rate, estimates the pressure gradient required to match
     * the requested volumetric flow, calculates the centerline velocity, and estimates the focused
     * sample region dimensions from the integrated sample flow constraint.
     *
     * The sample core is assumed to be a centered rectangle with the same aspect ratio as the
     * channel. Its size is computed so that the integral of the velocity field over the sample
     * region equals the requested sample volume flow.
     */
    void initialize();

    /**
     * @brief Validate the configured event sampling scheme.
     * Throws an exception if the scheme is not supported.
     */
    void validate_event_scheme() const;

    /**
     * @brief Validate the configured transverse sampling scheme.
     * Throws an exception if the scheme is not supported.
     */
    void validate_transverse_sampling_scheme() const;

    /**
     * @brief Validate the physical and numerical parameters of the flow cell.
     * Throws an exception if dimensions, flow rates, viscosity, or integration settings are invalid.
     */
    void validate_physical_parameters() const;

    /**
     * @brief Compute the scale of the centered sample core.
     *
     * The sample core is parameterized as:
     *
     *     sample_width = scale * width
     *     sample_height = scale * height
     *
     * with scale in [0, 1]. The scale is found by bisection so that the integrated
     * axial flow through the centered sample core equals `sample_volume_flow`.
     *
     * @return Sample core scale factor.
     */
    double compute_sample_core_scale() const;

public:
    /**
     * @brief Calculate the velocity at a given point in the flow cell.
     * This method computes the local axial velocity based on the y and z coordinates and the
     * specified pressure gradient.
     * The velocity is calculated using a Fourier series solution for fully developed laminar
     * flow in a rectangular channel.
     *
     * @param y The y-coordinate in meters.
     * @param z The z-coordinate in meters.
     * @param dpdx_local The pressure gradient in Pa/m.
     * @return The calculated local axial velocity in m/s.
     */
    double get_velocity(double y, double z, double dpdx_local) const;

    /**
     * @brief Compute the volumetric flow rate through a centered rectangular region.
     * This method numerically integrates the velocity field over a centered rectangle
     * of dimensions `region_width` by `region_height`.
     *
     * @param region_width Width of the centered region in meters.
     * @param region_height Height of the centered region in meters.
     * @param dpdx_input The pressure gradient in Pa/m.
     * @return The computed regional flow rate in m^3/s.
     */
    double compute_region_flow(
        double region_width,
        double region_height,
        double dpdx_input
    ) const;

    /**
     * @brief Compute the channel volumetric flow rate for a given pressure gradient.
     * This method numerically integrates the velocity field over the rectangular channel
     * cross section in order to estimate the total volumetric flow rate.
     *
     * @param dpdx_input The pressure gradient in Pa/m.
     * @return The computed channel flow rate in m^3/s.
     */
    double compute_channel_flow(double dpdx_input) const;

    /**
     * @brief Sample event arrival times from a Poisson process.
     * This method generates inter-arrival times from an exponential distribution
     * with rate `particle_flux`, then cumulatively sums them until `run_time`
     * is reached.
     *
     * @param run_time Total duration over which events are sampled, in seconds.
     * @param particle_flux Event rate in events per second.
     * @return A sorted vector of event arrival times in seconds.
     */
    std::vector<double> sample_arrival_times_poisson(double run_time, double particle_flux) const;

    /**
     * @brief Sample sorted random arrival times uniformly over the run time.
     * This method draws `n_events` independent uniform samples in [0, run_time]
     * and sorts them in ascending order.
     *
     * @param n_events Number of events to generate.
     * @param run_time Total duration over which events are sampled, in seconds.
     * @return A sorted vector of event arrival times in seconds.
     */
    std::vector<double> sample_arrival_times_uniform_random(std::size_t n_events, double run_time) const;

    /**
     * @brief Sample linearly spaced arrival times over the run time.
     * This method is mainly intended for debugging or deterministic test cases.
     * The generated times include both the first and last time point when `n_events > 1`.
     *
     * @param n_events Number of events to generate.
     * @param run_time Total duration over which events are sampled, in seconds.
     * @return A vector of linearly spaced event arrival times in seconds.
     */
    std::vector<double> sample_arrival_times_linear(std::size_t n_events, double run_time) const;

    /**
     * @brief Sample event arrival times according to the configured scheme.
     *
     * Supported schemes are:
     *
     * - `"uniform-random"`: draw `n_events` random arrival times uniformly over the run time
     *   and return them sorted.
     * - `"linear"`: generate `n_events` linearly spaced arrival times over the run time.
     *   This is useful for debugging and deterministic tests.
     * - `"poisson"`: generate event times using a Poisson process with rate `particle_flux`.
     *   In this case, `n_events` is ignored and the number of returned events is determined
     *   by the sampled process over `run_time`.
     *
     * @param n_events Number of events to generate for deterministic schemes.
     * @param run_time Total duration over which events are sampled, in seconds.
     * @param particle_flux Event rate in events per second for the `"poisson"` scheme.
     * @return A vector of event arrival times in seconds.
     */
    std::vector<double> sample_arrival_times(
        std::size_t n_events,
        double run_time,
        double particle_flux = 0.0
    ) const;
};