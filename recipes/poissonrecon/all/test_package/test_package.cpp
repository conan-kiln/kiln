#include <PoissonRecon/PreProcessor.h>
#include <PoissonRecon/MyMiscellany.h>
#include <PoissonRecon/CmdLineParser.h>
#include <PoissonRecon/FEMTree.h>
#include <PoissonRecon/PPolynomial.h>

#ifdef ADAPTIVE_SOLVERS_VERSION
using namespace PoissonRecon;
#endif

int main() {
    FEMTree<3, double> tree(32);
}
