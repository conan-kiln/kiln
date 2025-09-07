#include <ortools/linear_solver/linear_solver.h>

int main() {
    operations_research::MPSolver::CreateSolver("GLOP");
}
