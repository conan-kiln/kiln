#include <proxsuite/proxqp/dense/dense.hpp>

using namespace proxsuite::proxqp;

int main() {
    dense::isize dim = 3, n_eq = 0, n_in = 3;
    dense::QP<double> qp(dim, n_eq, n_in);
}
