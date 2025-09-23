#include <LBFGS.h>

int main() {
    LBFGSpp::LBFGSParam<double> param;
    LBFGSpp::LBFGSSolver<double> solver(param);
}
