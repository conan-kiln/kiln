#include <hyhound/householder-updowndate.hpp>
#include <vector>

int main() {
    using namespace hyhound;
    index_t n = 3, m = 2;
    std::vector<real_t> L_sto(n * n), A_sto(n * m);
    MatrixView<real_t> L{{.data = L_sto.data(), .rows = n, .cols = n}};
    MatrixView<real_t> A{{.data = A_sto.data(), .rows = n, .cols = m}};
    L.set_constant(4, guanaqo::Triangular::Lower);
    A.set_constant(1);
    A(1, 1) = -1;
    std::vector<real_t> S{2, -1};
    update_cholesky(L, A, DiagonalUpDowndate{S});
}
