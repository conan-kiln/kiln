#include <xpress.hpp>
#include <iostream>

void dummy_main() {
    xpress::XPRSProblem prob;
}

int main() {
    char version[1000];
    XPRSgetversion(version);
    std::cout << "Xpress Optimizer version: " << version << std::endl;
}
