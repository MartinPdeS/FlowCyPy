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
    const std::string& transverse_sampling_scheme,
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
      transverse_sampling_scheme(transverse_sampling_scheme),
      perfectly_aligned(perfectly_aligned)
{
    this->validate_physical_parameters();
    this->validate_event_scheme();
    this->validate_transverse_sampling_scheme();
    this->initialize();
}

std::tuple<std::vector<double>, std::vector<double>, std::vector<double>>
FlowCell::sample_transverse_profile(int n_samples) const {
    if (n_samples < 0) {
        throw std::runtime_error("n_samples must be non negative.");
    }

    std::vector<double> y_samples;
    std::vector<double> z_samples;
    std::vector<double> velocity_samples;

    y_samples.reserve(static_cast<std::size_t>(n_samples));
    z_samples.reserve(static_cast<std::size_t>(n_samples));
    velocity_samples.reserve(static_cast<std::size_t>(n_samples));

    std::random_device random_device;
    std::mt19937 generator(random_device());

    std::uniform_real_distribution<double> y_distribution(-sample.width / 2.0, sample.width / 2.0);
    std::uniform_real_distribution<double> z_distribution(-sample.height / 2.0, sample.height / 2.0);
    std::uniform_real_distribution<double> acceptance_distribution(0.0, 1.0);

    for (int sample_index = 0; sample_index < n_samples; ++sample_index) {
        double y = 0.0;
        double z = 0.0;
        double velocity = u_center;

        if (!perfectly_aligned) {
            bool accepted_sample = false;

            while (!accepted_sample) {
                y = y_distribution(generator);
                z = z_distribution(generator);
                velocity = this->get_velocity(y, z, dpdx);

                if (transverse_sampling_scheme == "uniform-random") {
                    accepted_sample = true;
                } else if (transverse_sampling_scheme == "velocity-weighted") {
                    const double acceptance_probability = velocity / u_center;

                    if (
                        acceptance_probability >= 1.0 ||
                        acceptance_distribution(generator) <= acceptance_probability
                    ) {
                        accepted_sample = true;
                    }
                } else {
                    throw std::runtime_error(
                        "Unsupported transverse_sampling_scheme '" + transverse_sampling_scheme +
                        "'. Expected one of: 'velocity-weighted', 'uniform-random'."
                    );
                }
            }
        }

        y_samples.push_back(y);
        z_samples.push_back(z);
        velocity_samples.push_back(velocity);
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

    const double sample_core_scale = this->compute_sample_core_scale();
    const double sample_width = sample_core_scale * width;
    const double sample_height = sample_core_scale * height;
    const double sample_area = sample_width * sample_height;
    const double sample_average_flow_speed = sample_volume_flow / sample_area;
    const double sample_max_flow_speed = this->get_velocity(0.0, 0.0, dpdx);

    this->sample = FluidRegion(
        sample_height,
        sample_width,
        sample_volume_flow,
        sample_max_flow_speed,
        sample_average_flow_speed
    );

    const double sheath_area = area - sample_area;
    const double sheath_average_flow_speed = sheath_area > 0.0
        ? sheath_volume_flow / sheath_area
        : 0.0;

    this->sheath = FluidRegion(
        height,
        width,
        sheath_volume_flow,
        u_center,
        sheath_average_flow_speed
    );
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

void FlowCell::validate_transverse_sampling_scheme() const {
    if (
        transverse_sampling_scheme != "velocity-weighted" &&
        transverse_sampling_scheme != "uniform-random"
    ) {
        throw std::runtime_error(
            "Unsupported transverse_sampling_scheme '" + transverse_sampling_scheme +
            "'. Expected one of: 'velocity-weighted', 'uniform-random'."
        );
    }
}

void FlowCell::validate_physical_parameters() const {
    if (width <= 0.0) {
        throw std::runtime_error("width must be strictly positive.");
    }

    if (height <= 0.0) {
        throw std::runtime_error("height must be strictly positive.");
    }

    if (sample_volume_flow < 0.0) {
        throw std::runtime_error("sample_volume_flow must be non negative.");
    }

    if (sheath_volume_flow < 0.0) {
        throw std::runtime_error("sheath_volume_flow must be non negative.");
    }

    if (sample_volume_flow + sheath_volume_flow <= 0.0) {
        throw std::runtime_error("The total volume flow must be strictly positive.");
    }

    if (viscosity <= 0.0) {
        throw std::runtime_error("viscosity must be strictly positive.");
    }

    if (N_terms <= 0) {
        throw std::runtime_error("N_terms must be strictly positive.");
    }

    if (n_int < 2) {
        throw std::runtime_error("n_int must be greater than or equal to 2.");
    }
}

double FlowCell::compute_sample_core_scale() const {
    if (sample_volume_flow == 0.0) {
        return 0.0;
    }

    if (sheath_volume_flow == 0.0) {
        return 1.0;
    }

    const double full_channel_flow = this->compute_region_flow(width, height, dpdx);

    if (full_channel_flow <= 0.0) {
        throw std::runtime_error("Computed full channel flow is non positive.");
    }

    if (sample_volume_flow > full_channel_flow) {
        throw std::runtime_error("sample_volume_flow exceeds the computed full channel flow.");
    }

    double lower_scale = 0.0;
    double upper_scale = 1.0;

    constexpr int maximum_iterations = 80;
    constexpr double relative_tolerance = 1e-10;

    for (int iteration = 0; iteration < maximum_iterations; ++iteration) {
        const double middle_scale = 0.5 * (lower_scale + upper_scale);
        const double region_width = middle_scale * width;
        const double region_height = middle_scale * height;
        const double region_flow = this->compute_region_flow(region_width, region_height, dpdx);

        const double relative_error = std::abs(region_flow - sample_volume_flow) / sample_volume_flow;

        if (relative_error < relative_tolerance) {
            return middle_scale;
        }

        if (region_flow < sample_volume_flow) {
            lower_scale = middle_scale;
        } else {
            upper_scale = middle_scale;
        }
    }

    return 0.5 * (lower_scale + upper_scale);
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

double FlowCell::compute_region_flow(
    const double region_width,
    const double region_height,
    const double dpdx_input
) const
{
    if (region_width < 0.0) {
        throw std::runtime_error("region_width must be non negative.");
    }

    if (region_height < 0.0) {
        throw std::runtime_error("region_height must be non negative.");
    }

    if (region_width > width) {
        throw std::runtime_error("region_width cannot exceed the channel width.");
    }

    if (region_height > height) {
        throw std::runtime_error("region_height cannot exceed the channel height.");
    }

    if (region_width == 0.0 || region_height == 0.0) {
        return 0.0;
    }

    const double y_min = -region_width / 2.0;
    const double y_max = region_width / 2.0;
    const double z_min = -region_height / 2.0;
    const double z_max = region_height / 2.0;

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

double FlowCell::compute_channel_flow(double dpdx_input) const {
    return this->compute_region_flow(width, height, dpdx_input);
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