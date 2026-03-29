#include <pybind11/numpy.h>

/*
    @brief Converts a std::vector to a NumPy array by moving the data.
    @tparam T The data type of the elements in the vector and NumPy array.
    @param data The std::vector whose data will be moved to the NumPy array.
    @param shape The desired shape of the resulting NumPy array.
    @return A NumPy array containing the data from the input vector.
    @note This function moves the data from the vector to the NumPy array, leaving the original vector in a valid but unspecified state.
*/
template <class T>
inline pybind11::array_t<T> vector_move_from_numpy(
    const std::vector<T>& data,
    const std::vector<size_t>& shape
)
{
    // product(shape) in size_t with a simple overflow check
    size_t expect = 1;
    for (size_t d : shape) {
        if (d != 0 && expect > std::numeric_limits<size_t>::max() / d) {
            std::ostringstream os;
            os << "Shape product overflows size_t. shape=[";
            for (size_t i = 0; i < shape.size(); ++i) {
                os << shape[i] << (i + 1 < shape.size() ? ", " : "");
            }
            os << "]";
            throw pybind11::value_error(os.str());
        }
        expect *= d;
    }

    const size_t got = data.size();

    if (expect != got) {
        std::ostringstream os;
        os << "Shape does not match vector size. "
           << "shape=[";
        for (size_t i = 0; i < shape.size(); ++i) {
            os << shape[i] << (i + 1 < shape.size() ? ", " : "");
        }
        os << "] product=" << expect
           << " but vector size=" << got
           << " (dtype=" << typeid(T).name() << ")";
        throw pybind11::value_error(os.str());
    }

    // pybind11 wants int64_t for the constructor, cast once here
    std::vector<pybind11::ssize_t> shape_ss;
    shape_ss.reserve(shape.size());
    for (size_t d : shape) shape_ss.push_back(static_cast<pybind11::ssize_t>(d));

    pybind11::array_t<T> out(shape_ss);
    if (got > 0) {
        std::memcpy(out.mutable_data(),
                    data.data(),
                    got * sizeof(T));
    }
    return out;
}



template <class T>
inline pybind11::array_t<T> vector_move_from_numpy(
    const std::vector<T>& data,
    const size_t& size
)
{
    std::vector<size_t> shape = {size,};
    return vector_move_from_numpy(std::move(data), shape);
}
