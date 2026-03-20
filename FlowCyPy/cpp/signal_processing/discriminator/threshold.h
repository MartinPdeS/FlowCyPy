#pragma once

#include <cmath>
#include <optional>
#include <string>
#include <utility>
#include <vector>
#include <algorithm> // std::minmax_element
#include <stdexcept> // std::runtime_error

/**
 * @brief Threshold representation used by trigger detectors.
 *
 * A threshold can be stored either as:
 *
 * - a numeric value
 * - a symbolic string such as "3sigma"
 *
 * The class provides explicit setters and accessors so the rest of the code
 * does not need to manipulate raw variants or duplicate validation logic.
 */
class Threshold {
public:
    enum class Mode {
        Undefined,
        Numeric,
        Symbolic
    };

private:
    Mode mode_ = Mode::Undefined;
    double numeric_value_ = 0.0;
    std::string symbolic_value_;

public:
    Threshold() = default;

    Threshold(const double value) {
        this->set_numeric(value);
    }

    Threshold(const std::string &value) {
        this->set_symbolic(value);
    }

    /**
     * @brief Set the threshold as a numeric value.
     */
    void set_numeric(const double value) {
        this->mode_ = Mode::Numeric;
        this->numeric_value_ = value;
        this->symbolic_value_.clear();
    }

    /**
     * @brief Set the threshold as a symbolic string.
     */
    void set_symbolic(const std::string &value) {
        this->mode_ = Mode::Symbolic;
        this->symbolic_value_ = value;
        this->numeric_value_ = 0.0;
    }

    /**
     * @brief Reset the threshold to an undefined state.
     */
    void clear() {
        this->mode_ = Mode::Undefined;
        this->numeric_value_ = 0.0;
        this->symbolic_value_.clear();
    }

    /**
     * @brief Return true if the threshold has been configured.
     */
    bool is_defined() const {
        return this->mode_ != Mode::Undefined;
    }

    /**
     * @brief Return true if the threshold stores a numeric value.
     */
    bool is_numeric() const {
        return this->mode_ == Mode::Numeric;
    }

    /**
     * @brief Return true if the threshold stores a symbolic value.
     */
    bool is_symbolic() const {
        return this->mode_ == Mode::Symbolic;
    }

    /**
     * @brief Get the current storage mode.
     */
    Mode get_mode() const {
        return this->mode_;
    }

    /**
     * @brief Get the numeric value.
     *
     * Throws if the threshold is not numeric.
     */
    double get_numeric() const {
        if (!this->is_numeric()) {
            throw std::runtime_error("Threshold does not contain a numeric value.");
        }

        return this->numeric_value_;
    }

    /**
     * @brief Get the symbolic value.
     *
     * Throws if the threshold is not symbolic.
     */
    const std::string &get_symbolic() const {
        if (!this->is_symbolic()) {
            throw std::runtime_error("Threshold does not contain a symbolic value.");
        }

        return this->symbolic_value_;
    }
};
