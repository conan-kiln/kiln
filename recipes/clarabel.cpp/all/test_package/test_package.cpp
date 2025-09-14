#include <clarabel.hpp>
#include <Eigen/Eigen>
#include <vector>

using namespace clarabel;
using namespace std;
using namespace Eigen;

int main() {
    MatrixXd P_dense = MatrixXd::Zero(2, 2);
    SparseMatrix<double> P = P_dense.sparseView();
    P.makeCompressed();

    Vector<double, 2> q = {1.0, -1.0};

    MatrixXd A_dense(4, 2);
    A_dense <<
         1.,  0.,
         0.,  1.,
        -1.,  0.,
         0., -1.;

    SparseMatrix<double> A = A_dense.sparseView();
    A.makeCompressed();

    Vector<double, 4> b = { 1.0, 1.0, 1.0, 1.0 };

    vector<SupportedConeT<double>> cones
    {
        NonnegativeConeT<double>(4),
    };

    DefaultSettings<double> settings = DefaultSettingsBuilder<double>::default_settings()
                                           .equilibrate_enable(true)
                                           .equilibrate_max_iter(50)
                                           .build();
    DefaultSolver<double> solver(P, q, A, b, cones, settings);
    solver.solve();
    DefaultSolution<double> solution = solver.solution();
}
