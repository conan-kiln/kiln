#include <nanoeigenpy/nanoeigenpy.hpp>

namespace nb = nanobind;

void f(const Eigen::Quaterniond &quat) {
}

NB_MODULE(test_package, m) {
    nanoeigenpy::exposeQuaternion<double>(m, "Quaternion");
    m.def("f", f, nb::arg("quat"));
}
