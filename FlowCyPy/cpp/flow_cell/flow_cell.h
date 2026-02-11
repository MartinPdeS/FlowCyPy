#pragma once

#include <vector>
#include <cmath>
#include <stdexcept>
#include <random>
#include <tuple>

class FluidRegion {
public:
    double height; // [m]
    double width;  // [m]
    double area;  // [m^2]
    double volume_flow; // [m^3/s]
    double max_flow_speed = 0.0; // [m/s]
    double average_flow_speed = 0.0; // [m/s]

    FluidRegion() = default;

    FluidRegion(double height, double width, double volume_flow, double max_flow_speed, double average_flow_speed)
        : height(height), width(width), volume_flow(volume_flow),
          max_flow_speed(max_flow_speed), average_flow_speed(average_flow_speed)
    {}

    FluidRegion(double height, double width, double volume_flow)
    : height(height), width(width), volume_flow(volume_flow)
    {
        this->area = height * width;
    }

};

class FlowCell {
public:
    double width;  // [m]
    double height; // [m]
    double area; //[m^2]
    double viscosity;     // [Pa.s]
    double sample_volume_flow; // [m^3/s]
    double sheath_volume_flow; // [m^3/s]
    int N_terms = 25;
    int n_int = 200;

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
     * flow rates, viscosity, number of terms for series expansion, and number of integration points
     * for numerical integration.
     * @param width Width of the flow cell in meters.
     * @param height Height of the flow cell in meters.
     * @param sample_volume_flow Volume flow rate of the sample in m^3/s.
     * @param sheath_volume_flow Volume flow rate of the sheath fluid in m^3/s.
     * @param viscosity Viscosity of the fluid in Pa.s.
     * @param N_terms Number of terms for series expansion (default is 25).
     * @param n_int Number of integration points for numerical integration (default is 200).
     * @note The constructor calls the `initialize` method to set up the flow cell parameters
     */
    FlowCell(double width, double height, double sample_volume_flow, double sheath_volume_flow, double viscosity, int N_terms, int n_int);

    /**
     * @brief Sample the transverse velocity profile of the flow cell.
     * This method generates a list of tuples representing the transverse profile
     * of the flow cell, where each tuple contains the y-coordinate, z-coordinate,
     * and the corresponding velocity at that point.
     * The coordinates are sampled uniformly within the flow cell's dimensions.
     * The velocity is calculated based on the flow cell's parameters and the
     * transverse position within the flow cell. The method returns a vector of tuples,
     * where each tuple contains the y-coordinate, z-coordinate, and velocity at that point.
     *
     * @param n_samples Number of samples to generate for the transverse profile.
     * @return A tuple containing three vectors: y-coordinates, z-coordinates, and velocities.
     */
    std::tuple<std::vector<double>, std::vector<double>, std::vector<double>> sample_transverse_profile(int n_samples) const;

private:
    /**
     * @brief Initialize the flow cell parameters based on the provided dimensions and flow rates.
     * This method computes the total flow rate, adjusts the pressure gradient, and calculates the
     * center velocity and dimensions of the sample region.
     */
    void initialize();

public:
    /**
     * @brief Calculate the velocity at a given point in the flow cell.
     * This method computes the velocity based on the y and z coordinates and the local pressure gradient.
     * The velocity is calculated using a series expansion based on the flow cell's parameters.
     *
     * @param y The y-coordinate in meters.
     * @param z The z-coordinate in meters.
     * @param dpdx_local The local pressure gradient in Pa/m.
     * @return The calculated velocity at the specified point in m/s.
     */
    double get_velocity(double y, double z, double dpdx_local) const;

    /**
     * @brief Compute the channel flow based on the pressure gradient.
     * This method calculates the flow rate through the channel based on the pressure gradient and
     * the dimensions of the flow cell.
     *
     * @param dpdx_input The pressure gradient in Pa/m.
     * @return The computed channel flow in m^3/s.
     */
    double compute_channel_flow(double dpdx_input);

    /**
     * @brief Get the local axial velocity at a point in the flow cell.
     * This method computes the local axial velocity \( u(y, z) \) at the point (y, z) in a rectangular microchannel
     * using the analytical Fourier series solution for pressure-driven flow.
     *
     * @param y Lateral (width-wise) position in meters.
     * @param z Vertical (height-wise) position in meters.
     * @param dpdx_local Pressure gradient (Pa/m) used for the computation.
     * @return The local axial velocity at the specified point in m/s.
     */
    std::vector<double> sample_arrival_times(double run_time, double particle_flux) const;
};
