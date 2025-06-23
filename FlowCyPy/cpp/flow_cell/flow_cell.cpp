#include "flow_cell.h"




FlowCell::FlowCell(double width, double height, double sample_volume_flow, double sheath_volume_flow, double viscosity, int N_terms, int n_int)
    : width(width), height(height), viscosity(viscosity), sample_volume_flow(sample_volume_flow), sheath_volume_flow(sheath_volume_flow), N_terms(N_terms), n_int(n_int)
{
    this->initialize();
}

std::tuple<std::vector<double>, std::vector<double>, std::vector<double>>
FlowCell::sample_transverse_profile(int n_samples) const {
    std::vector<double> y_samples, z_samples, velocity_samples;

    y_samples.reserve(n_samples);
    z_samples.reserve(n_samples);
    velocity_samples.reserve(n_samples);

    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<> dist_y(-sample.width / 2.0, sample.width / 2.0);
    std::uniform_real_distribution<> dist_z(-sample.height / 2.0, sample.height / 2.0);

    for (int i = 0; i < n_samples; ++i) {
        double y = dist_y(gen);
        double z = dist_z(gen);
        y_samples.push_back(y);
        z_samples.push_back(z);
        velocity_samples.push_back(this->get_velocity(y, z, dpdx));
    }

    return std::make_tuple(y_samples, z_samples, velocity_samples);
}


void FlowCell::initialize() {
    Q_total = sample_volume_flow + sheath_volume_flow;
    double Q_ref = compute_channel_flow(dpdx_ref);
    dpdx = dpdx_ref * (Q_total / Q_ref);

    u_center = this->get_velocity(0.0, 0.0, dpdx);

    double area_sample = sample_volume_flow / u_center;
    double height_sample = 2.0 * std::sqrt((area_sample * height) / (4.0 * width));
    double width_sample = (width / height) * height_sample;
    double average_flow_speed_sample = sample_volume_flow / area_sample;

    this->sample = FluidRegion(height_sample, width_sample, sample_volume_flow, u_center, average_flow_speed_sample);
    this->sheath = FluidRegion(height, width, sheath_volume_flow);
}

double FlowCell::get_velocity(double y, double z, double dpdx_local) const {
    double u = 0.0;
    double prefactor = (4.0 * height * height / (std::pow(M_PI, 3) * viscosity)) * (-dpdx_local);

    for (int n = 1; n < 2 * N_terms; n += 2) {
        double term_y = 1.0 - std::cosh((n * M_PI * y) / height) / std::cosh((n * M_PI * width / 2.0) / height);
        double term_z = std::sin((n * M_PI * (z + height / 2.0)) / height);
        u += term_y * term_z / std::pow(n, 3);
    }
    return prefactor * u;
}

double FlowCell::compute_channel_flow(double dpdx_input) {
    double y_min = -width / 2.0, y_max = width / 2.0;
    double z_min = -height / 2.0, z_max = height / 2.0;
    double dy = (y_max - y_min) / (n_int - 1);
    double dz = (z_max - z_min) / (n_int - 1);

    double sum = 0.0;
    for (int i = 0; i < n_int; ++i) {
        double y = y_min + i * dy;
        for (int j = 0; j < n_int; ++j) {
            double z = z_min + j * dz;
            sum += this->get_velocity(y, z, dpdx_input);
        }
    }

    return sum * dy * dz;
}

std::vector<double> FlowCell::sample_arrival_times(double run_time, double particle_flux) const {
    std::vector<double> arrival_times;
    arrival_times.reserve(static_cast<int>(run_time * particle_flux));  // Estimate

    std::random_device rd;
    std::mt19937 gen(rd());
    std::exponential_distribution<> exp_dist(particle_flux);

    double current_time = 0.0;
    while (current_time <= run_time) {
        double dt = exp_dist(gen);
        current_time += dt;
        if (current_time > run_time)
            break;
        arrival_times.push_back(current_time);
    }

    return arrival_times;
}