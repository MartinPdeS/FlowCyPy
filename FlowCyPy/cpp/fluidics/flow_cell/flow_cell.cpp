#include "flow_cell.h"

FlowCell::FlowCell(
    double width,
    double height,
    double sample_volume_flow,
    double sheath_volume_flow,
    double viscosity,
    int N_terms,
    int n_int,
    const std::string& event_scheme,
    bool perfectly_aligned
)
    : width(width),
      height(height),
      area(width * height),
      viscosity(viscosity),
      sample_volume_flow(sample_volume_flow),
      sheath_volume_flow(sheath_volume_flow),
      N_terms(N_terms),
      n_int(n_int),
      event_scheme(event_scheme),
      perfectly_aligned(perfectly_aligned)
{
    this->validate_event_scheme();
    this->initialize();
}

std::tuple<std::vector<double>, std::vector<double>, std::vector<double>>
FlowCell::sample_transverse_profile(int n_samples) const {
    std::vector<double> y_samples;
    std::vector<double> z_samples;
    std::vector<double> velocity_samples;

    y_samples.reserve(n_samples);
    z_samples.reserve(n_samples);
    velocity_samples.reserve(n_samples);

    std::random_device random_device;
    std::mt19937 generator(random_device());
    std::uniform_real_distribution<double> y_distribution(-sample.width / 2.0, sample.width / 2.0);
    std::uniform_real_distribution<double> z_distribution(-sample.height / 2.0, sample.height / 2.0);

    for (int sample_index = 0; sample_index < n_samples; ++sample_index) {
        const double y = perfectly_aligned ? 0.0 : y_distribution(generator);
        const double z = perfectly_aligned ? 0.0 : z_distribution(generator);

        y_samples.push_back(y);
        z_samples.push_back(z);
        velocity_samples.push_back(this->get_velocity(y, z, dpdx));
    }

    return std::make_tuple(y_samples, z_samples, velocity_samples);
}

void FlowCell::initialize() {
    Q_total = sample_volume_flow + sheath_volume_flow;

    const double reference_channel_flow = compute_channel_flow(dpdx_ref);

    if (reference_channel_flow == 0.0) {
        throw std::runtime_error("Reference channel flow is zero. Cannot compute dpdx.");
    }

    dpdx = dpdx_ref * (Q_total / reference_channel_flow);

    u_center = this->get_velocity(0.0, 0.0, dpdx);

    if (u_center <= 0.0) {
        throw std::runtime_error("Computed center velocity is non positive.");
    }

    const double sample_area = sample_volume_flow / u_center;
    const double sample_height = std::sqrt(sample_area * height / width);
    const double sample_width = (width / height) * sample_height;
    const double average_flow_speed_sample = sample_volume_flow / sample_area;

    this->sample = FluidRegion(
        sample_height,
        sample_width,
        sample_volume_flow,
        u_center,
        average_flow_speed_sample
    );

    this->sheath = FluidRegion(height, width, sheath_volume_flow);
}

void FlowCell::validate_event_scheme() const {
    if (
        event_scheme != "uniform-random" &&
        event_scheme != "linear" &&
        event_scheme != "poisson"
    ) {
        throw std::runtime_error(
            "Unsupported event_scheme '" + event_scheme +
            "'. Expected one of: 'uniform-random', 'linear', 'poisson'."
        );
    }
}

double FlowCell::get_velocity(double y, double z, double dpdx_local) const {
    double velocity = 0.0;
    const double prefactor =
        (4.0 * height * height / (std::pow(M_PI, 3) * viscosity)) * (-dpdx_local);

    for (int n = 1; n < 2 * N_terms; n += 2) {
        const double term_y =
            1.0 - std::cosh((n * M_PI * y) / height) / std::cosh((n * M_PI * width / 2.0) / height);

        const double term_z =
            std::sin((n * M_PI * (z + height / 2.0)) / height);

        velocity += term_y * term_z / std::pow(static_cast<double>(n), 3);
    }

    return prefactor * velocity;
}

double FlowCell::compute_channel_flow(double dpdx_input) const {
    const double y_min = -width / 2.0;
    const double y_max = width / 2.0;
    const double z_min = -height / 2.0;
    const double z_max = height / 2.0;

    const double dy = (y_max - y_min) / static_cast<double>(n_int - 1);
    const double dz = (z_max - z_min) / static_cast<double>(n_int - 1);

    double sum = 0.0;

    for (int i = 0; i < n_int; ++i) {
        const double y = y_min + static_cast<double>(i) * dy;

        for (int j = 0; j < n_int; ++j) {
            const double z = z_min + static_cast<double>(j) * dz;
            sum += this->get_velocity(y, z, dpdx_input);
        }
    }

    return sum * dy * dz;
}

std::vector<double>
FlowCell::sample_arrival_times_uniform_random(
    const std::size_t n_events,
    const double run_time
) const
{
    std::random_device random_device;
    std::mt19937 generator(random_device());

    std::vector<double> arrival_times;
    arrival_times.reserve(n_events);

    std::uniform_real_distribution<double> uniform_distribution(0.0, run_time);

    for (std::size_t event_index = 0; event_index < n_events; ++event_index) {
        arrival_times.push_back(uniform_distribution(generator));
    }

    std::sort(arrival_times.begin(), arrival_times.end());

    return arrival_times;
}

std::vector<double>
FlowCell::sample_arrival_times_linear(
    const std::size_t n_events,
    const double run_time
) const
{
    std::vector<double> arrival_times;
    arrival_times.reserve(n_events);

    if (n_events == 0) {
        return arrival_times;
    }

    if (n_events == 1) {
        arrival_times.push_back(0.0);
        return arrival_times;
    }

    const double dt = run_time / static_cast<double>(n_events - 1);

    for (std::size_t event_index = 0; event_index < n_events; ++event_index) {
        arrival_times.push_back(static_cast<double>(event_index) * dt);
    }

    return arrival_times;
}

std::vector<double>
FlowCell::sample_arrival_times_poisson(
    const double run_time,
    const double particle_flux
) const
{
    if (particle_flux <= 0.0) {
        throw std::runtime_error("particle_flux must be strictly positive for poisson sampling.");
    }

    std::vector<double> arrival_times;
    arrival_times.reserve(static_cast<std::size_t>(run_time * particle_flux));

    std::random_device random_device;
    std::mt19937 generator(random_device());
    std::exponential_distribution<double> exponential_distribution(particle_flux);

    double current_time = 0.0;

    while (current_time <= run_time) {
        const double dt = exponential_distribution(generator);
        current_time += dt;

        if (current_time > run_time) {
            break;
        }

        arrival_times.push_back(current_time);
    }

    return arrival_times;
}

std::vector<double>
FlowCell::sample_arrival_times(
    const std::size_t n_events,
    const double run_time,
    const double particle_flux
) const
{
    if (run_time < 0.0) {
        throw std::runtime_error("run_time must be non negative.");
    }

    if (event_scheme == "uniform-random") {
        return this->sample_arrival_times_uniform_random(n_events, run_time);
    }

    if (event_scheme == "linear") {
        return this->sample_arrival_times_linear(n_events, run_time);
    }

    if (event_scheme == "poisson") {
        return this->sample_arrival_times_poisson(run_time, particle_flux);
    }

    throw std::runtime_error(
        "Unsupported event_scheme '" + event_scheme +
        "'. Expected one of: 'uniform-random', 'linear', 'poisson'."
    );
}
