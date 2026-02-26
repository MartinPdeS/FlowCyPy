#pragma once

#include <vector>
#include <complex>
#include <string>
#include <unordered_map>

#include <distributions/distributions.h>
#include "sampling_methods.h"

typedef std::complex<double> complex128;

class BasePopulation {
public:
    std::string name;
    double concentration;
    std::shared_ptr<BaseSamplingMethod> sampling_method;

    BasePopulation() = default;
    virtual ~BasePopulation() = default;

    BasePopulation(
        const std::string &name,
        const double concentration,
        std::shared_ptr<BaseSamplingMethod> sampling_method
    )
    :   name(name),
        concentration(concentration),
        sampling_method(std::move(sampling_method)){}

    void dilute(const double dilution_factor) {
        concentration /= dilution_factor;
    }

    virtual double get_effective_concentration() const {
        return concentration;
    }

    virtual std::unordered_map<std::string, std::vector<double>> sample() const = 0;

};

class SpherePopulation: public BasePopulation {
public:
    std::shared_ptr<BaseDistribution> medium_refractive_index;
    std::shared_ptr<BaseDistribution> refractive_index;
    std::shared_ptr<BaseDistribution> diameter;

    SpherePopulation() = default;

    SpherePopulation(
        const std::string &name,
        const double concentration,
        std::shared_ptr<BaseDistribution> medium_refractive_index,
        std::shared_ptr<BaseDistribution> refractive_index,
        std::shared_ptr<BaseDistribution> diameter,
        std::shared_ptr<BaseSamplingMethod> sampling_method
    ) : BasePopulation(name, concentration, std::move(sampling_method)),
        medium_refractive_index(std::move(medium_refractive_index)),
        refractive_index(std::move(refractive_index)),
        diameter(std::move(diameter)) {}


    double get_effective_concentration() const override;

    std::unordered_map<std::string, std::vector<double>> sample() const override {
        std::unordered_map<std::string, std::vector<double>> samples;
        samples["Medium"] = medium_refractive_index->sample(1000);
        samples["RefractiveIndex"] = refractive_index->sample(1000);
        samples["Diameter"] = diameter->sample(1000);
        return samples;
    }

};


class CoreShellPopulation: public BasePopulation {
public:
    std::shared_ptr<BaseDistribution> medium_refractive_index;
    std::shared_ptr<BaseDistribution> core_refractive_index;
    std::shared_ptr<BaseDistribution> shell_refractive_index;
    std::shared_ptr<BaseDistribution> core_diameter;
    std::shared_ptr<BaseDistribution> shell_thickness;

    CoreShellPopulation() = default;

    CoreShellPopulation(
        const std::string &name,
        const double concentration,
        std::shared_ptr<BaseDistribution> medium_refractive_index,
        std::shared_ptr<BaseDistribution> core_refractive_index,
        std::shared_ptr<BaseDistribution> shell_refractive_index,
        std::shared_ptr<BaseDistribution> core_diameter,
        std::shared_ptr<BaseDistribution> shell_thickness,
        std::shared_ptr<BaseSamplingMethod> sampling_method
    ) : BasePopulation(name, concentration, std::move(sampling_method)),
        medium_refractive_index(std::move(medium_refractive_index)),
        core_refractive_index(std::move(core_refractive_index)),
        shell_refractive_index(std::move(shell_refractive_index)),
        core_diameter(std::move(core_diameter)),
        shell_thickness(std::move(shell_thickness)) {}


    double get_effective_concentration() const override;

    std::unordered_map<std::string, std::vector<double>> sample() const override {
        std::unordered_map<std::string, std::vector<double>> samples;
        samples["Medium"] = medium_refractive_index->sample(1000);
        samples["CoreRefractiveIndex"] = core_refractive_index->sample(1000);
        samples["ShellRefractiveIndex"] = shell_refractive_index->sample(1000);
        samples["CoreDiameter"] = core_diameter->sample(1000);
        samples["ShellThickness"] = shell_thickness->sample(1000);
        return samples;
    }

};
