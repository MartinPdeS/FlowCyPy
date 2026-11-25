#pragma once

#include <cstdint>
#include <optional>
#include <random>

namespace noise {
using Seed = std::optional<std::uint64_t>;

inline std::uint64_t resolve_seed(Seed seed) {
    return seed ? *seed : std::random_device{}();
}

inline std::mt19937 make_generator(std::uint64_t seed, unsigned int worker) {
    std::seed_seq sequence{
        static_cast<unsigned int>(seed), static_cast<unsigned int>(seed >> 32), worker
    };
    return std::mt19937(sequence);
}
}
