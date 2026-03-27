#pragma once

#include <cmath>
#include <optional>
#include <string>
#include <stdexcept>


/**
 * @brief Threshold container used by trigger detectors.
 *
 * A threshold may carry:
 *
 * - a numeric value
 * - a symbolic expression
 * - both at the same time
 * - neither, if undefined
 *
 * This is useful for trigger systems where a threshold may be specified
 * symbolically, such as "3sigma", and later resolved to a numeric value
 * during computation while still preserving the original expression.
 */
class Threshold {
private:
    std::optional<double> numeric_value_;
    std::optional<std::string> symbolic_value_;

public:
    Threshold() = default;

    explicit Threshold(const double value) {
        this->set_numeric(value);
    }

    explicit Threshold(const std::string &value) {
        this->set_symbolic(value);
    }

    Threshold(const double numeric_value, const std::string &symbolic_value) {
        this->set_numeric(numeric_value);
        this->set_symbolic(symbolic_value);
    }

    /**
     * @brief Set or replace the numeric value.
     */
    void set_numeric(const double value) {
        this->numeric_value_ = value;
    }

    /**
     * @brief Set or replace the symbolic value.
     */
    void set_symbolic(const std::string &value) {
        if (value.empty()) {
            throw std::runtime_error("Threshold symbolic value must not be empty.");
        }

        this->symbolic_value_ = value;
    }

    /**
     * @brief Remove the numeric value while preserving the symbolic value.
     */
    void clear_numeric() {
        this->numeric_value_.reset();
    }

    /**
     * @brief Remove the symbolic value while preserving the numeric value.
     */
    void clear_symbolic() {
        this->symbolic_value_.reset();
    }

    /**
     * @brief Reset the threshold to an undefined state.
     */
    void clear() {
        this->numeric_value_.reset();
        this->symbolic_value_.reset();
    }

    /**
     * @brief Return true if either a numeric or symbolic value is present.
     */
    bool is_defined() const {
        return this->numeric_value_.has_value() || this->symbolic_value_.has_value();
    }

    /**
     * @brief Return true if a numeric value is present.
     */
    bool has_numeric() const {
        return this->numeric_value_.has_value();
    }

    /**
     * @brief Return true if a symbolic value is present.
     */
    bool has_symbolic() const {
        return this->symbolic_value_.has_value();
    }

    /**
     * @brief Get the numeric value.
     *
     * Throws if no numeric value is available.
     */
    double get_numeric() const {
        if (!this->numeric_value_.has_value()) {
            throw std::runtime_error("Threshold does not contain a numeric value.");
        }

        return *this->numeric_value_;
    }

    /**
     * @brief Get the symbolic value.
     *
     * Throws if no symbolic value is available.
     */
    const std::string &get_symbolic() const {
        if (!this->symbolic_value_.has_value()) {
            throw std::runtime_error("Threshold does not contain a symbolic value.");
        }

        return *this->symbolic_value_;
    }

    /**
     * @brief Return the numeric value if present.
     */
    const std::optional<double> &get_optional_numeric() const {
        return this->numeric_value_;
    }

    /**
     * @brief Return the symbolic value if present.
     */
    const std::optional<std::string> &get_optional_symbolic() const {
        return this->symbolic_value_;
    }
};
