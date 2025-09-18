#include <kdalgorithms/kdalgorithms.h>
#include <iostream>

int main() {
    auto vec = kdalgorithms::iota(1, 10);
    std::cout << "kdalgorithms::iota: " << vec[0] << "\n";
}
