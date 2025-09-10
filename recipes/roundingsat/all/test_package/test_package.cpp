#ifndef RS_OLD_API
#include <roundingsat/Env.hpp>
#else
#include <roundingsat/Solver.hpp>
#endif

int main() {
#ifndef RS_OLD_API
    rs::Env env;
#else
    rs::Solver solver;
#endif
}
