#pragma once

class BaseSamplingMethod {
public:
    virtual ~BaseSamplingMethod() = default;
};

class ExplicitModel : public BaseSamplingMethod {
};

class GammaModel : public BaseSamplingMethod {
public:
    size_t number_of_samples;
    GammaModel(size_t number_of_samples) : number_of_samples(number_of_samples) {}
};
